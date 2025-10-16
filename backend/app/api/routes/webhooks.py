"""
Webhook endpoints for push-based source integrations.
Allows external services to push content updates instead of polling.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from supabase import Client
from typing import Optional
from datetime import datetime
import hmac
import hashlib
import logging

from app.core.database import get_supabase
from app.api.dependencies import get_current_active_user
from app.services.sources.base import SourceRegistry, SourceContent

router = APIRouter()
logger = logging.getLogger(__name__)


def verify_webhook_signature(
    payload: bytes,
    signature: str,
    secret: str,
    algorithm: str = "sha256"
) -> bool:
    """
    Verify webhook signature using HMAC.
    
    Args:
        payload: Raw request body
        signature: Signature from webhook header
        secret: Webhook secret for verification
        algorithm: Hash algorithm (default: sha256)
    
    Returns:
        True if signature is valid, False otherwise
    """
    try:
        expected_signature = hmac.new(
            secret.encode(),
            payload,
            getattr(hashlib, algorithm)
        ).hexdigest()
        return hmac.compare_digest(signature, expected_signature)
    except Exception as e:
        logger.error(f"Error verifying webhook signature: {e}")
        return False


@router.post("/generic/{source_id}")
async def receive_generic_webhook(
    source_id: str,
    request: Request,
    x_webhook_signature: Optional[str] = Header(None),
    supabase: Client = Depends(get_supabase)
):
    """
    Generic webhook endpoint for push-based sources.
    
    The source must be configured with:
    - webhook_secret: Secret for signature verification
    - webhook_parser: Name of the parser function to use
    
    Example webhook configuration in source.config:
    {
        "webhook_enabled": true,
        "webhook_secret": "your-secret-key",
        "webhook_parser": "substack",  // or "medium", "custom", etc.
        "signature_header": "X-Webhook-Signature",
        "signature_algorithm": "sha256"
    }
    """
    try:
        # Fetch source from database
        result = supabase.table("sources").select("*").eq("id", source_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Source not found"
            )
        
        source = result.data[0]
        config = source.get("config", {})
        
        # Check if webhook is enabled
        if not config.get("webhook_enabled", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Webhook not enabled for this source"
            )
        
        # Get raw body for signature verification
        body = await request.body()
        
        # Verify signature if secret is configured
        webhook_secret = config.get("webhook_secret")
        if webhook_secret and x_webhook_signature:
            signature_algorithm = config.get("signature_algorithm", "sha256")
            
            if not verify_webhook_signature(body, x_webhook_signature, webhook_secret, signature_algorithm):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid webhook signature"
                )
        
        # Parse JSON payload
        try:
            payload = await request.json()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid JSON payload: {str(e)}"
            )
        
        # Get parser type from config
        parser_type = config.get("webhook_parser", "generic")
        
        # Parse webhook payload based on parser type
        content = parse_webhook_payload(payload, parser_type)
        
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to parse webhook payload"
            )
        
        # Store content in cache
        content_data = {
            "source_id": source_id,
            "user_id": source["user_id"],
            "title": content.title,
            "content": content.content,
            "url": content.url,
            "published_at": content.published_at.isoformat() if content.published_at else None,
            "metadata": content.metadata,
            "fetched_at": datetime.utcnow().isoformat()
        }
        
        supabase.table("source_content_cache").insert(content_data).execute()
        
        logger.info(f"Webhook content stored for source {source_id}: {content.title}")
        
        return {
            "success": True,
            "message": "Webhook received and processed",
            "content_title": content.title
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process webhook: {str(e)}"
        )


def parse_webhook_payload(payload: dict, parser_type: str) -> Optional[SourceContent]:
    """
    Parse webhook payload based on parser type.
    
    Args:
        payload: Webhook JSON payload
        parser_type: Type of parser to use (substack, medium, generic, etc.)
    
    Returns:
        SourceContent object or None if parsing fails
    """
    try:
        if parser_type == "substack":
            return parse_substack_webhook(payload)
        elif parser_type == "medium":
            return parse_medium_webhook(payload)
        elif parser_type == "generic":
            return parse_generic_webhook(payload)
        else:
            # Try generic parser as fallback
            return parse_generic_webhook(payload)
    except Exception as e:
        logger.error(f"Error parsing webhook payload with {parser_type} parser: {e}")
        return None


def parse_generic_webhook(payload: dict) -> SourceContent:
    """
    Parse generic webhook payload.
    Expects standard fields: title, content, url, published_at, metadata
    """
    return SourceContent(
        title=payload.get("title", "Untitled"),
        content=payload.get("content", ""),
        url=payload.get("url"),
        published_at=datetime.fromisoformat(payload["published_at"]) if payload.get("published_at") else None,
        metadata=payload.get("metadata", {})
    )


def parse_substack_webhook(payload: dict) -> SourceContent:
    """
    Parse Substack webhook payload.
    
    Substack webhook format:
    {
        "type": "post.published",
        "post": {
            "id": 123,
            "title": "Post Title",
            "subtitle": "Post Subtitle",
            "body_html": "<p>Content...</p>",
            "canonical_url": "https://...",
            "post_date": "2024-01-01T00:00:00Z",
            "audience": "everyone",
            "type": "newsletter"
        }
    }
    """
    post = payload.get("post", {})
    
    return SourceContent(
        title=post.get("title", "Untitled"),
        content=post.get("body_html", ""),
        url=post.get("canonical_url"),
        published_at=datetime.fromisoformat(post["post_date"].replace("Z", "+00:00")) if post.get("post_date") else None,
        metadata={
            "subtitle": post.get("subtitle", ""),
            "audience": post.get("audience", ""),
            "type": post.get("type", ""),
            "post_id": post.get("id"),
            "source": "substack"
        }
    )


def parse_medium_webhook(payload: dict) -> SourceContent:
    """
    Parse Medium webhook payload.
    
    Note: Medium doesn't officially support webhooks, but this is for
    potential third-party integrations or RSS-to-webhook services.
    """
    return SourceContent(
        title=payload.get("title", "Untitled"),
        content=payload.get("content", ""),
        url=payload.get("url"),
        published_at=datetime.fromisoformat(payload["published_at"]) if payload.get("published_at") else None,
        metadata={
            "author": payload.get("author", ""),
            "tags": payload.get("tags", []),
            "claps": payload.get("claps", 0),
            "source": "medium"
        }
    )


@router.get("/{source_id}/info")
async def get_webhook_info(
    source_id: str,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Get webhook configuration information for a source.
    Returns the webhook URL and configuration details.
    """
    try:
        user_id = current_user["id"]
        
        # Fetch source
        result = supabase.table("sources").select("*").eq("id", source_id).eq("user_id", user_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Source not found"
            )
        
        source = result.data[0]
        config = source.get("config", {})
        
        # Build webhook URL (you'll need to replace with your actual domain)
        webhook_url = f"/api/webhooks/generic/{source_id}"
        
        return {
            "webhook_url": webhook_url,
            "webhook_enabled": config.get("webhook_enabled", False),
            "webhook_parser": config.get("webhook_parser", "generic"),
            "signature_header": config.get("signature_header", "X-Webhook-Signature"),
            "signature_algorithm": config.get("signature_algorithm", "sha256"),
            "has_secret": bool(config.get("webhook_secret"))
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch webhook info: {str(e)}"
        )
