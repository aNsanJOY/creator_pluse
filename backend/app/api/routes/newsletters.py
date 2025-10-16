from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from supabase import Client
from typing import List, Optional
from datetime import datetime
import html2text
import markdown

from app.core.database import get_supabase
from app.api.dependencies import get_current_active_user
from app.models.newsletter_sample import (
    NewsletterSampleCreate,
    NewsletterSampleResponse,
    NewsletterSampleUpload
)

router = APIRouter()


def process_file_content(content: str, file_format: str) -> str:
    """
    Process file content based on format and convert to plain text.
    
    Args:
        content: Raw file content
        file_format: File format (txt, md, html)
    
    Returns:
        Processed plain text content
    """
    if file_format == "txt":
        return content
    elif file_format == "md":
        # Convert markdown to HTML first, then to plain text
        html_content = markdown.markdown(content)
        h = html2text.HTML2Text()
        h.ignore_links = False
        return h.handle(html_content)
    elif file_format == "html":
        # Convert HTML to plain text
        h = html2text.HTML2Text()
        h.ignore_links = False
        return h.handle(content)
    else:
        return content


@router.post("/upload", response_model=NewsletterSampleResponse, status_code=status.HTTP_201_CREATED)
async def upload_newsletter_sample(
    sample_data: NewsletterSampleUpload,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Upload a newsletter sample for voice training.
    Supports direct text input or file content in txt, md, or html format.
    """
    try:
        user_id = current_user["id"]
        
        # Get content from either direct input or file upload
        try:
            raw_content = sample_data.get_content()
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        
        # Process content based on file format
        if sample_data.file_format:
            processed_content = process_file_content(raw_content, sample_data.file_format)
        else:
            processed_content = raw_content
        
        # Validate content length
        if len(processed_content.strip()) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Content is too short. Please provide at least 10 characters."
            )
        
        # Create newsletter sample
        new_sample = {
            "user_id": user_id,
            "title": sample_data.title,
            "content": processed_content,
        }
        
        result = supabase.table("newsletter_samples").insert(new_sample).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create newsletter sample"
            )
        
        return NewsletterSampleResponse(**result.data[0])
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload newsletter sample: {str(e)}"
        )


@router.post("/upload-file", response_model=NewsletterSampleResponse, status_code=status.HTTP_201_CREATED)
async def upload_newsletter_file(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Upload a newsletter sample file for voice training.
    Supports .txt, .md, and .html file formats.
    """
    try:
        user_id = current_user["id"]
        
        # Validate file extension
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File name is required"
            )
        
        file_ext = file.filename.split(".")[-1].lower()
        if file_ext not in ["txt", "md", "html"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only .txt, .md, and .html files are supported"
            )
        
        # Read file content
        content = await file.read()
        try:
            content_str = content.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be UTF-8 encoded"
            )
        
        # Process content based on file format
        processed_content = process_file_content(content_str, file_ext)
        
        # Validate content length
        if len(processed_content.strip()) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Content is too short. Please provide at least 10 characters."
            )
        
        # Use filename as title if not provided
        sample_title = title or file.filename
        
        # Create newsletter sample
        new_sample = {
            "user_id": user_id,
            "title": sample_title,
            "content": processed_content,
        }
        
        result = supabase.table("newsletter_samples").insert(new_sample).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create newsletter sample"
            )
        
        return NewsletterSampleResponse(**result.data[0])
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload newsletter file: {str(e)}"
        )


@router.get("/samples", response_model=List[NewsletterSampleResponse])
async def get_newsletter_samples(
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Get all newsletter samples for the current user.
    """
    try:
        user_id = current_user["id"]
        
        # Fetch all newsletter samples for the user
        result = supabase.table("newsletter_samples").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        
        if not result.data:
            return []
        
        return [NewsletterSampleResponse(**sample) for sample in result.data]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch newsletter samples: {str(e)}"
        )


@router.delete("/samples/{sample_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_newsletter_sample(
    sample_id: str,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Delete a newsletter sample by ID.
    """
    try:
        user_id = current_user["id"]
        
        # Check if sample exists and belongs to the user
        existing = supabase.table("newsletter_samples").select("*").eq("id", sample_id).eq("user_id", user_id).execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Newsletter sample not found"
            )
        
        # Delete the sample
        result = supabase.table("newsletter_samples").delete().eq("id", sample_id).eq("user_id", user_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete newsletter sample"
            )
        
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete newsletter sample: {str(e)}"
        )
