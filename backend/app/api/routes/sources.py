from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from supabase import Client
from typing import List, Dict, Any
from datetime import datetime

from app.core.database import get_supabase
from app.api.dependencies import get_current_active_user
from app.models.source import (
    SourceCreate,
    SourceUpdate,
    SourceResponse,
    SourceStatusResponse,
    SourceStatus
)
from app.utils.validators import SourceValidator
from app.services.crawler import crawl_source_task
from app.schemas.credentials import get_credential_schema, get_all_credential_schemas
from app.services.sources.base import SourceRegistry

router = APIRouter()


@router.get("", response_model=List[SourceResponse])
async def get_sources(
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Get all sources for the current user.
    """
    try:
        user_id = current_user["id"]
        
        # Fetch all sources for the user
        result = supabase.table("sources").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        
        if not result.data:
            return []
        
        return [SourceResponse(**source) for source in result.data]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch sources: {str(e)}"
        )


@router.post("", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
async def create_source(
    source_data: SourceCreate,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Add a new source for the current user.
    Validates the source configuration before creating.
    """
    try:
        user_id = current_user["id"]
        
        # Validate source
        is_valid, error_message = SourceValidator.validate_source(
            source_type=source_data.source_type,
            url=source_data.url,
            credentials=source_data.credentials
        )
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message
            )
        
        # Check if source with same URL already exists for this user
        if source_data.url:
            existing = supabase.table("sources").select("*").eq("user_id", user_id).eq("url", source_data.url).execute()
            if existing.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A source with this URL already exists"
                )
        
        # Prepare source data
        config = source_data.config or {}
        
        # Special handling for RSS feeds - ensure feed_url is in config
        if source_data.source_type.value == "rss":
            if source_data.url and "feed_url" not in config:
                config["feed_url"] = str(source_data.url)
            elif "feed_url" in config and not source_data.url:
                # If feed_url is in config but not in url, copy it
                source_data.url = config["feed_url"]
        
        new_source = {
            "user_id": user_id,
            "source_type": source_data.source_type.value,
            "name": source_data.name,
            "url": source_data.url,
            "credentials": source_data.credentials,
            "config": config,
            "status": SourceStatus.PENDING.value
        }
        
        # Insert source into database
        result = supabase.table("sources").insert(new_source).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create source"
            )
        
        created_source = result.data[0]
        
        # TODO: Trigger initial crawl in background task
        # For now, we'll just mark it as active
        supabase.table("sources").update({"status": SourceStatus.ACTIVE.value}).eq("id", created_source["id"]).execute()
        created_source["status"] = SourceStatus.ACTIVE.value
        
        return SourceResponse(**created_source)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create source: {str(e)}"
        )


@router.get("/{source_id}", response_model=SourceResponse)
async def get_source(
    source_id: str,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Get a specific source by ID.
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
        
        return SourceResponse(**result.data[0])
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch source: {str(e)}"
        )


@router.put("/{source_id}", response_model=SourceResponse)
async def update_source(
    source_id: str,
    source_data: SourceUpdate,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Update a source.
    """
    try:
        user_id = current_user["id"]
        
        # Check if source exists and belongs to user
        existing = supabase.table("sources").select("*").eq("id", source_id).eq("user_id", user_id).execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Source not found"
            )
        
        # Prepare update data (only include fields that are set)
        update_data = {}
        if source_data.name is not None:
            update_data["name"] = source_data.name
        if source_data.url is not None:
            update_data["url"] = source_data.url
        if source_data.config is not None:
            update_data["config"] = source_data.config
        if source_data.credentials is not None:
            update_data["credentials"] = source_data.credentials
        if source_data.status is not None:
            update_data["status"] = source_data.status.value
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        # Update source
        result = supabase.table("sources").update(update_data).eq("id", source_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update source"
            )
        
        return SourceResponse(**result.data[0])
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update source: {str(e)}"
        )


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(
    source_id: str,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Remove a source.
    This will also delete all associated content due to CASCADE constraint.
    """
    try:
        user_id = current_user["id"]
        
        # Check if source exists and belongs to user
        existing = supabase.table("sources").select("*").eq("id", source_id).eq("user_id", user_id).execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Source not found"
            )
        
        # Delete source
        supabase.table("sources").delete().eq("id", source_id).execute()
        
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete source: {str(e)}"
        )


@router.get("/{source_id}/status", response_model=SourceStatusResponse)
async def get_source_status(
    source_id: str,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Check the status of a source.
    Returns health status and last crawl information.
    """
    try:
        user_id = current_user["id"]
        
        # Fetch source
        result = supabase.table("sources").select("id, status, last_crawled_at, error_message").eq("id", source_id).eq("user_id", user_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Source not found"
            )
        
        source = result.data[0]
        
        # Determine if source is healthy
        is_healthy = source["status"] == SourceStatus.ACTIVE.value and source.get("error_message") is None
        
        return SourceStatusResponse(
            id=source["id"],
            status=SourceStatus(source["status"]),
            last_crawled_at=source.get("last_crawled_at"),
            error_message=source.get("error_message"),
            is_healthy=is_healthy
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch source status: {str(e)}"
        )


@router.post("/{source_id}/crawl")
async def trigger_source_crawl(
    source_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Manually trigger a crawl for a specific source.
    The crawl runs in the background.
    """
    try:
        user_id = current_user["id"]
        
        # Verify source exists and belongs to user
        result = supabase.table("sources").select("*").eq("id", source_id).eq("user_id", user_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Source not found"
            )
        
        source = result.data[0]
        
        # Check if source is active
        if source["status"] != SourceStatus.ACTIVE.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot crawl source with status: {source['status']}"
            )
        
        # Trigger background crawl
        background_tasks.add_task(crawl_source_task, source_id)
        
        return {
            "message": "Crawl started",
            "source_id": source_id,
            "source_name": source["name"]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger crawl: {str(e)}"
        )


@router.get("/types")
async def get_source_types():
    """
    Get all available source types with their credential requirements.
    This helps the frontend build dynamic forms.
    """
    try:
        # Get all registered source types
        source_types = SourceRegistry.get_all_source_types()
        
        # Get credential schemas
        all_schemas = get_all_credential_schemas()
        
        result = []
        for source_type in source_types:
            schema = all_schemas.get(source_type, {})
            result.append({
                "type": source_type,
                "name": source_type.capitalize(),
                "credential_schema": schema.dict() if schema else None
            })
        
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch source types: {str(e)}"
        )


@router.get("/types/{source_type}/credentials")
async def get_source_credential_schema(source_type: str):
    """
    Get credential schema for a specific source type.
    Returns field definitions for building credential input forms.
    """
    try:
        schema = get_credential_schema(source_type)
        
        if not schema:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Source type '{source_type}' not found"
            )
        
        return schema.dict()
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch credential schema: {str(e)}"
        )
