"""
Email API Routes
Endpoints for email delivery, tracking, and unsubscribe management
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from fastapi.responses import HTMLResponse
from supabase import Client
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from pydantic import BaseModel, EmailStr

from app.core.database import get_supabase
from app.api.dependencies import get_current_active_user
from app.services.email_service import email_service

router = APIRouter()


class SendEmailRequest(BaseModel):
    """Request model for sending emails"""
    draft_id: str
    subject: str
    recipient_emails: List[EmailStr]


class AddRecipientRequest(BaseModel):
    """Request model for adding a recipient"""
    email: EmailStr
    name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class UnsubscribeRequest(BaseModel):
    """Request model for unsubscribe"""
    email: EmailStr
    reason: Optional[str] = None


@router.post("/send")
async def send_email(
    request: SendEmailRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Send newsletter email to recipients
    
    Validates rate limits, checks unsubscribe list, and sends emails.
    Email sending happens in the background.
    """
    try:
        user_id = current_user["id"]
        
        # Check rate limit before queuing
        rate_limit = await email_service.check_rate_limit(
            user_id, 
            len(request.recipient_emails)
        )
        
        if not rate_limit["can_send"]:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "message": "Daily email limit exceeded",
                    "rate_limit": rate_limit
                }
            )
        
        # Queue email sending in background
        background_tasks.add_task(
            email_service.send_newsletter,
            draft_id=request.draft_id,
            subject=request.subject,
            recipients=request.recipient_emails,
            user_id=user_id
        )
        
        return {
            "success": True,
            "message": f"Email queued for delivery to {len(request.recipient_emails)} recipient(s)",
            "rate_limit": rate_limit
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue email: {str(e)}"
        )


@router.get("/rate-limit")
async def get_rate_limit(
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get current rate limit status for the user
    
    Returns daily limit, current count, and remaining emails.
    """
    try:
        user_id = current_user["id"]
        
        rate_limit = await email_service.check_rate_limit(user_id)
        
        return {
            "success": True,
            "rate_limit": rate_limit
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get rate limit: {str(e)}"
        )


@router.get("/delivery-logs")
async def get_delivery_logs(
    limit: int = 50,
    status_filter: Optional[str] = None,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Get email delivery logs for the current user
    
    Returns logs with delivery status, timestamps, and error messages.
    """
    try:
        user_id = current_user["id"]
        
        query = supabase.table("email_delivery_log").select("*").eq(
            "user_id", user_id
        )
        
        if status_filter:
            query = query.eq("status", status_filter)
        
        result = query.order("created_at", desc=True).limit(limit).execute()
        
        return {
            "success": True,
            "logs": result.data or [],
            "total": len(result.data or [])
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch delivery logs: {str(e)}"
        )


@router.get("/stats")
async def get_email_stats(
    days: int = 30,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Get email delivery statistics
    
    Returns aggregated stats for the specified time period.
    """
    try:
        user_id = current_user["id"]
        
        from datetime import timedelta
        since_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        # Get all logs for the period
        result = supabase.table("email_delivery_log").select("*").eq(
            "user_id", user_id
        ).gte("created_at", since_date).execute()
        
        logs = result.data or []
        
        # Calculate stats
        total_sent = sum(1 for log in logs if log["status"] == "sent")
        total_failed = sum(1 for log in logs if log["status"] == "failed")
        total_queued = sum(1 for log in logs if log["status"] in ["queued", "sending"])
        
        # Get rate limit info
        rate_limit = await email_service.check_rate_limit(user_id)
        
        return {
            "success": True,
            "stats": {
                "period_days": days,
                "total_sent": total_sent,
                "total_failed": total_failed,
                "total_queued": total_queued,
                "total_attempts": len(logs),
                "success_rate": round(total_sent / len(logs) * 100, 2) if logs else 0
            },
            "rate_limit": rate_limit
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get email stats: {str(e)}"
        )


# Recipient Management Endpoints

@router.get("/recipients")
async def list_recipients(
    limit: int = 100,
    status_filter: Optional[str] = None,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    List all recipients for the current user
    
    Returns recipient list with subscription status.
    """
    try:
        user_id = current_user["id"]
        
        query = supabase.table("recipients").select("*").eq("user_id", user_id)
        
        if status_filter:
            query = query.eq("status", status_filter)
        
        result = query.order("created_at", desc=True).limit(limit).execute()
        
        return {
            "success": True,
            "recipients": result.data or [],
            "total": len(result.data or [])
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch recipients: {str(e)}"
        )


@router.post("/recipients")
async def add_recipient(
    request: AddRecipientRequest,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Add a new recipient to the user's list
    
    Creates a new recipient entry if it doesn't exist.
    """
    try:
        user_id = current_user["id"]
        
        # Check if recipient already exists
        existing = supabase.table("recipients").select("*").eq(
            "user_id", user_id
        ).eq("email", request.email.lower()).execute()
        
        if existing.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Recipient already exists"
            )
        
        # Add recipient
        recipient_data = {
            "user_id": user_id,
            "email": request.email.lower(),
            "name": request.name,
            "status": "active",
            "metadata": request.metadata or {}
        }
        
        result = supabase.table("recipients").insert(recipient_data).execute()
        
        return {
            "success": True,
            "message": "Recipient added successfully",
            "recipient": result.data[0] if result.data else None
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add recipient: {str(e)}"
        )


@router.delete("/recipients/{recipient_id}")
async def delete_recipient(
    recipient_id: str,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Delete a recipient from the user's list
    
    Permanently removes the recipient.
    """
    try:
        user_id = current_user["id"]
        
        # Verify recipient belongs to user
        result = supabase.table("recipients").select("id").eq(
            "id", recipient_id
        ).eq("user_id", user_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recipient not found"
            )
        
        # Delete recipient
        supabase.table("recipients").delete().eq("id", recipient_id).execute()
        
        return {
            "success": True,
            "message": "Recipient deleted successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete recipient: {str(e)}"
        )


# Unsubscribe Endpoints

@router.get("/unsubscribe", response_class=HTMLResponse)
async def unsubscribe_page(
    email: str,
    token: Optional[str] = None,
    supabase: Client = Depends(get_supabase)
):
    """
    Unsubscribe page (GET request from email link)
    
    Displays a confirmation page and processes the unsubscribe request.
    """
    try:
        # Check if already unsubscribed
        result = supabase.table("unsubscribes").select("*").eq(
            "email", email.lower()
        ).execute()
        
        if result.data:
            return """
            <html>
            <head>
                <title>Already Unsubscribed</title>
                <style>
                    body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center; }
                    .container { background-color: #F9FAFB; padding: 40px; border-radius: 8px; }
                    h1 { color: #1F2937; }
                    p { color: #6B7280; line-height: 1.6; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Already Unsubscribed</h1>
                    <p>This email address has already been unsubscribed from our mailing list.</p>
                    <p>You will not receive any further emails from us.</p>
                </div>
            </body>
            </html>
            """
        
        # Add to unsubscribe list
        supabase.table("unsubscribes").insert({
            "email": email.lower(),
            "reason": "Unsubscribed via email link"
        }).execute()
        
        # Update recipient status if exists
        supabase.table("recipients").update({
            "status": "unsubscribed"
        }).eq("email", email.lower()).execute()
        
        return """
        <html>
        <head>
            <title>Unsubscribed Successfully</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center; }
                .container { background-color: #F9FAFB; padding: 40px; border-radius: 8px; }
                h1 { color: #1F2937; }
                p { color: #6B7280; line-height: 1.6; }
                .success { color: #10B981; font-weight: bold; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>✓ Unsubscribed Successfully</h1>
                <p class="success">You have been unsubscribed from our mailing list.</p>
                <p>We're sorry to see you go. You will no longer receive emails from CreatorPulse.</p>
                <p>If this was a mistake, please contact support to resubscribe.</p>
            </div>
        </body>
        </html>
        """
    
    except Exception as e:
        return f"""
        <html>
        <head>
            <title>Error</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center; }}
                .container {{ background-color: #FEE2E2; padding: 40px; border-radius: 8px; }}
                h1 {{ color: #DC2626; }}
                p {{ color: #991B1B; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Error</h1>
                <p>An error occurred while processing your unsubscribe request.</p>
                <p>Error: {str(e)}</p>
            </div>
        </body>
        </html>
        """


@router.post("/unsubscribe")
async def unsubscribe_api(
    request: UnsubscribeRequest,
    supabase: Client = Depends(get_supabase)
):
    """
    Unsubscribe API endpoint (POST request)
    
    Adds email to unsubscribe list.
    """
    try:
        # Check if already unsubscribed
        result = supabase.table("unsubscribes").select("*").eq(
            "email", request.email.lower()
        ).execute()
        
        if result.data:
            return {
                "success": True,
                "message": "Email already unsubscribed"
            }
        
        # Add to unsubscribe list
        supabase.table("unsubscribes").insert({
            "email": request.email.lower(),
            "reason": request.reason or "Unsubscribed via API"
        }).execute()
        
        # Update recipient status if exists
        supabase.table("recipients").update({
            "status": "unsubscribed"
        }).eq("email", request.email.lower()).execute()
        
        return {
            "success": True,
            "message": "Successfully unsubscribed"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unsubscribe: {str(e)}"
        )


@router.get("/check-unsubscribed/{email}")
async def check_unsubscribed(
    email: str,
    supabase: Client = Depends(get_supabase)
):
    """
    Check if an email is unsubscribed
    
    Public endpoint for checking unsubscribe status.
    """
    try:
        is_unsubscribed = await email_service.check_unsubscribed(email)
        
        return {
            "success": True,
            "email": email,
            "is_unsubscribed": is_unsubscribed
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check unsubscribe status: {str(e)}"
        )


# Email Tracking Endpoints

@router.get("/track-open")
async def track_email_open(
    user_id: str,
    draft_id: str,
    recipient: str,
    supabase: Client = Depends(get_supabase)
):
    """
    Track email open event via 1x1 pixel
    
    This endpoint is called when the tracking pixel in an email is loaded.
    Returns a transparent 1x1 pixel image.
    """
    try:
        # Log the open event
        supabase.table("email_tracking_events").insert({
            "user_id": user_id,
            "draft_id": draft_id,
            "recipient_email": recipient.lower(),
            "event_type": "open",
            "event_data": {},
            "tracked_at": datetime.now().isoformat()
        }).execute()
        
        # Return 1x1 transparent pixel
        from fastapi.responses import Response
        pixel = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
        return Response(content=pixel, media_type="image/gif")
    
    except Exception as e:
        # Silently fail - don't break email rendering
        from fastapi.responses import Response
        pixel = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
        return Response(content=pixel, media_type="image/gif")


@router.get("/track-click")
async def track_email_click(
    url: str,
    user_id: str,
    draft_id: str,
    request: Request,
    supabase: Client = Depends(get_supabase)
):
    """
    Track email link click event and redirect to original URL
    
    This endpoint is called when a tracked link in an email is clicked.
    Logs the click event and redirects to the original URL.
    """
    try:
        # Get recipient email from referer or other headers if available
        recipient_email = request.headers.get("X-Recipient-Email", "unknown")
        
        # Log the click event
        supabase.table("email_tracking_events").insert({
            "user_id": user_id,
            "draft_id": draft_id,
            "recipient_email": recipient_email,
            "event_type": "click",
            "event_data": {"url": url},
            "tracked_at": datetime.now().isoformat()
        }).execute()
        
        # Redirect to original URL
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=url, status_code=302)
    
    except Exception as e:
        # On error, still redirect to the URL
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=url, status_code=302)


@router.get("/tracking-stats/{draft_id}")
async def get_tracking_stats(
    draft_id: str,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Get tracking statistics for a specific draft
    
    Returns open and click counts, unique recipients, and engagement metrics.
    """
    try:
        user_id = current_user["id"]
        
        # Verify draft belongs to user
        draft_result = supabase.table("newsletter_drafts").select("id").eq(
            "id", draft_id
        ).eq("user_id", user_id).execute()
        
        if not draft_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Draft not found"
            )
        
        # Get all tracking events for this draft
        events_result = supabase.table("email_tracking_events").select("*").eq(
            "draft_id", draft_id
        ).eq("user_id", user_id).execute()
        
        events = events_result.data or []
        
        # Calculate statistics
        opens = [e for e in events if e["event_type"] == "open"]
        clicks = [e for e in events if e["event_type"] == "click"]
        
        unique_opens = len(set(e["recipient_email"] for e in opens))
        unique_clicks = len(set(e["recipient_email"] for e in clicks))
        
        # Get total recipients from draft metadata
        draft_full = supabase.table("newsletter_drafts").select("metadata").eq(
            "id", draft_id
        ).execute()
        
        total_recipients = 0
        if draft_full.data:
            metadata = draft_full.data[0].get("metadata", {})
            email_stats = metadata.get("email_stats", {})
            total_recipients = email_stats.get("sent_count", 0)
        
        return {
            "success": True,
            "draft_id": draft_id,
            "stats": {
                "total_recipients": total_recipients,
                "total_opens": len(opens),
                "unique_opens": unique_opens,
                "total_clicks": len(clicks),
                "unique_clicks": unique_clicks,
                "open_rate": round(unique_opens / total_recipients * 100, 2) if total_recipients > 0 else 0,
                "click_rate": round(unique_clicks / total_recipients * 100, 2) if total_recipients > 0 else 0,
                "click_through_rate": round(unique_clicks / unique_opens * 100, 2) if unique_opens > 0 else 0
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tracking stats: {str(e)}"
        )
