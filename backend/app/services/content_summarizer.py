"""
Content Summarization Service using Groq LLM
Generates structured summaries of content from various sources
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from groq import Groq
from supabase import Client

from app.core.config import settings
from app.core.database import get_supabase

logger = logging.getLogger(__name__)


class ContentSummarizer:
    """Generates AI-powered summaries of content using Groq LLM"""
    
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = "openai/gpt-oss-20b"
        self.supabase: Optional[Client] = None
    
    def initialize(self):
        """Initialize database connection"""
        if not self.supabase:
            self.supabase = get_supabase()
    
    async def summarize_content(
        self,
        content_id: str,
        user_id: str,
        summary_type: str = "standard",
        force_regenerate: bool = False
    ) -> Dict[str, Any]:
        """
        Generate a summary for a specific content item
        
        Args:
            content_id: ID of content item to summarize
            user_id: User ID (for authorization)
            summary_type: Type of summary ('standard', 'brief', 'detailed')
            force_regenerate: Force regeneration even if summary exists
        
        Returns:
            Summary dictionary with title, key points, and summary text
        """
        self.initialize()
        
        logger.info(f"Summarizing content {content_id} for user {user_id}")
        
        # Check if summary already exists
        if not force_regenerate:
            existing = await self._get_existing_summary(content_id, summary_type)
            if existing:
                logger.info(f"Using existing summary for content {content_id}")
                return existing
        
        # Fetch content
        content = await self._get_content(content_id, user_id)
        if not content:
            raise ValueError(f"Content {content_id} not found or not accessible")
        
        # Generate summary using Groq
        summary = await self._generate_summary(content, summary_type)
        
        # Store summary in database
        stored_summary = await self._store_summary(
            content_id=content_id,
            user_id=user_id,
            summary_type=summary_type,
            summary_data=summary
        )
        
        return stored_summary
    
    async def summarize_batch(
        self,
        content_ids: List[str],
        user_id: str,
        summary_type: str = "standard"
    ) -> List[Dict[str, Any]]:
        """
        Generate summaries for multiple content items
        
        Args:
            content_ids: List of content IDs to summarize
            user_id: User ID
            summary_type: Type of summary
        
        Returns:
            List of summary dictionaries
        """
        summaries = []
        
        for content_id in content_ids:
            try:
                summary = await self.summarize_content(
                    content_id=content_id,
                    user_id=user_id,
                    summary_type=summary_type
                )
                summaries.append(summary)
            except Exception as e:
                logger.error(f"Error summarizing content {content_id}: {str(e)}")
                summaries.append({
                    "content_id": content_id,
                    "error": str(e),
                    "status": "failed"
                })
        
        return summaries
    
    async def summarize_recent_content(
        self,
        user_id: str,
        days_back: int = 7,
        limit: int = 20,
        summary_type: str = "standard"
    ) -> List[Dict[str, Any]]:
        """
        Summarize recent content for a user
        
        Args:
            user_id: User ID
            days_back: Number of days to look back
            limit: Maximum number of items to summarize
            summary_type: Type of summary
        
        Returns:
            List of summaries
        """
        self.initialize()
        
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        # Get user's sources
        sources_result = self.supabase.table("sources").select("id").eq(
            "user_id", user_id
        ).eq("status", "active").execute()
        
        if not sources_result.data:
            return []
        
        source_ids = [s["id"] for s in sources_result.data]
        
        # Get recent content without summaries
        content_result = self.supabase.table("source_content_cache").select(
            "id"
        ).in_("source_id", source_ids).gte(
            "created_at", cutoff_date.isoformat()
        ).order("created_at", desc=True).limit(limit).execute()
        
        if not content_result.data:
            return []
        
        content_ids = [c["id"] for c in content_result.data]
        
        # Filter out content that already has summaries
        unsummarized_ids = []
        for content_id in content_ids:
            existing = await self._get_existing_summary(content_id, summary_type)
            if not existing:
                unsummarized_ids.append(content_id)
        
        logger.info(f"Summarizing {len(unsummarized_ids)} unsummarized items")
        
        # Generate summaries
        return await self.summarize_batch(unsummarized_ids, user_id, summary_type)
    
    async def _get_content(
        self,
        content_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Fetch content item from database"""
        try:
            # Verify user has access to this content
            result = self.supabase.table("source_content_cache").select(
                "*, sources!inner(user_id)"
            ).eq("id", content_id).execute()
            
            if not result.data:
                return None
            
            content = result.data[0]
            
            # Check user authorization
            if content["sources"]["user_id"] != user_id:
                logger.warning(f"User {user_id} attempted to access content {content_id}")
                return None
            
            return content
            
        except Exception as e:
            logger.error(f"Error fetching content {content_id}: {str(e)}")
            return None
    
    async def _generate_summary(
        self,
        content: Dict[str, Any],
        summary_type: str
    ) -> Dict[str, Any]:
        """
        Generate summary using Groq LLM
        
        Args:
            content: Content item dictionary
            summary_type: Type of summary to generate
        
        Returns:
            Summary dictionary
        """
        try:
            # Create prompt based on summary type
            prompt = self._create_summary_prompt(content, summary_type)
            
            # Call Groq API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert content summarizer. Create clear, concise, and informative summaries in valid JSON format."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for consistent summaries
                max_tokens=1000 if summary_type == "detailed" else 500
            )
            
            # Parse response
            import json
            import re
            
            summary_text = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', summary_text, re.DOTALL)
            if json_match:
                summary_data = json.loads(json_match.group())
            else:
                # Fallback: create basic summary
                summary_data = {
                    "title": content.get("title", "Untitled"),
                    "key_points": [],
                    "summary": summary_text,
                    "topics": []
                }
            
            # Add metadata
            summary_data["word_count"] = len(summary_data.get("summary", "").split())
            summary_data["source_url"] = content.get("url")
            summary_data["source_title"] = content.get("title")
            
            return summary_data
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            # Return basic fallback summary
            return {
                "title": content.get("title", "Untitled"),
                "key_points": [],
                "summary": content.get("content", "")[:500] + "...",
                "topics": [],
                "error": str(e)
            }
    
    def _create_summary_prompt(
        self,
        content: Dict[str, Any],
        summary_type: str
    ) -> str:
        """Create prompt for summary generation"""
        
        title = content.get("title", "Untitled")
        text = content.get("content", "")
        url = content.get("url", "")
        
        # Truncate very long content
        max_length = 3000 if summary_type == "detailed" else 2000
        if len(text) > max_length:
            text = text[:max_length] + "..."
        
        length_instruction = {
            "brief": "Create a very brief summary (2-3 sentences, 3-5 key points max).",
            "standard": "Create a concise summary (3-5 sentences, 5-7 key points).",
            "detailed": "Create a comprehensive summary (5-8 sentences, 7-10 key points)."
        }.get(summary_type, "Create a concise summary.")
        
        prompt = f"""Summarize the following content for a newsletter reader.

TITLE: {title}
URL: {url}

CONTENT:
{text}

{length_instruction}

Provide your summary in the following JSON format:

{{
  "title": "Clear, engaging title for the summary",
  "key_points": [
    "First key point or highlight",
    "Second key point",
    "Third key point"
  ],
  "summary": "Concise summary paragraph that captures the main ideas and why it matters",
  "topics": ["topic1", "topic2", "topic3"],
  "sentiment": "positive/neutral/negative/mixed",
  "relevance_score": 0.0-1.0
}}

Focus on:
- What is the main idea or news?
- Why does it matter?
- What are the key takeaways?
- Keep it engaging and newsletter-friendly

Provide ONLY the JSON object, no additional text."""

        return prompt
    
    async def _get_existing_summary(
        self,
        content_id: str,
        summary_type: str
    ) -> Optional[Dict[str, Any]]:
        """Check if summary already exists"""
        try:
            result = self.supabase.table("content_summaries").select("*").eq(
                "content_id", content_id
            ).eq("summary_type", summary_type).execute()
            
            if result.data:
                summary = result.data[0]
                return {
                    "id": summary["id"],
                    "content_id": summary["content_id"],
                    "title": summary["title"],
                    "key_points": summary.get("key_points", []),
                    "summary": summary["summary_text"],
                    "metadata": summary.get("metadata", {}),
                    "created_at": summary["created_at"]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking existing summary: {str(e)}")
            return None
    
    async def _store_summary(
        self,
        content_id: str,
        user_id: str,
        summary_type: str,
        summary_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Store summary in database"""
        try:
            # Prepare data for insertion
            insert_data = {
                "content_id": content_id,
                "user_id": user_id,
                "summary_type": summary_type,
                "title": summary_data.get("title", ""),
                "key_points": summary_data.get("key_points", []),
                "summary_text": summary_data.get("summary", ""),
                "metadata": {
                    "topics": summary_data.get("topics", []),
                    "sentiment": summary_data.get("sentiment", "neutral"),
                    "relevance_score": summary_data.get("relevance_score", 0.5),
                    "word_count": summary_data.get("word_count", 0),
                    "source_url": summary_data.get("source_url"),
                    "source_title": summary_data.get("source_title")
                },
                "model_used": self.model
            }
            
            result = self.supabase.table("content_summaries").insert(insert_data).execute()
            
            if result.data:
                stored = result.data[0]
                logger.info(f"Stored summary {stored['id']} for content {content_id}")
                
                return {
                    "id": stored["id"],
                    "content_id": stored["content_id"],
                    "title": stored["title"],
                    "key_points": stored.get("key_points", []),
                    "summary": stored["summary_text"],
                    "metadata": stored.get("metadata", {}),
                    "created_at": stored["created_at"]
                }
            
            return summary_data
            
        except Exception as e:
            logger.error(f"Error storing summary: {str(e)}")
            # Return the generated summary even if storage fails
            return summary_data
    
    async def get_summaries_for_content(
        self,
        content_ids: List[str],
        user_id: str
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get summaries for multiple content items
        
        Args:
            content_ids: List of content IDs
            user_id: User ID
        
        Returns:
            Dictionary mapping content_id to summary
        """
        self.initialize()
        
        try:
            result = self.supabase.table("content_summaries").select("*").in_(
                "content_id", content_ids
            ).eq("user_id", user_id).execute()
            
            summaries = {}
            for summary in result.data or []:
                summaries[summary["content_id"]] = {
                    "id": summary["id"],
                    "title": summary["title"],
                    "key_points": summary.get("key_points", []),
                    "summary": summary["summary_text"],
                    "metadata": summary.get("metadata", {}),
                    "created_at": summary["created_at"]
                }
            
            return summaries
            
        except Exception as e:
            logger.error(f"Error fetching summaries: {str(e)}")
            return {}


# Singleton instance
content_summarizer = ContentSummarizer()
