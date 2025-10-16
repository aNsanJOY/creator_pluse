from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class NewsletterSampleBase(BaseModel):
    """Base newsletter sample model"""
    title: Optional[str] = Field(None, max_length=500)
    content: str = Field(..., min_length=1)


class NewsletterSampleCreate(NewsletterSampleBase):
    """Model for creating a new newsletter sample"""
    pass


class NewsletterSampleResponse(NewsletterSampleBase):
    """Model for newsletter sample response"""
    id: str
    user_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class NewsletterSampleUpload(BaseModel):
    """Model for uploading newsletter sample via text or file"""
    title: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = None  # For direct text input
    file_content: Optional[str] = None  # For file upload content
    file_format: Optional[str] = Field(None, pattern="^(txt|md|html)$")  # File format

    def get_content(self) -> str:
        """Get the actual content from either content or file_content"""
        if self.file_content:
            return self.file_content
        if self.content:
            return self.content
        raise ValueError("Either content or file_content must be provided")
