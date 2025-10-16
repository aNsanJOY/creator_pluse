"""
Trend Detection Service using Groq LLM
Analyzes content from sources to detect trending topics and patterns
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import Counter
from groq import Groq
from supabase import Client

from app.core.config import settings
from app.core.database import get_supabase

logger = logging.getLogger(__name__)


class TrendDetector:
    """Detects trending topics from aggregated content using Groq LLM"""
    
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = "openai/gpt-oss-20b"
        self.supabase: Optional[Client] = None
    
    def initialize(self):
        """Initialize database connection"""
        if not self.supabase:
            self.supabase = get_supabase()
    
    async def detect_trends(
        self,
        user_id: str,
        days_back: int = 7,
        min_score: float = 0.5,
        max_trends: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Detect trending topics from user's content sources
        
        Args:
            user_id: User ID to detect trends for
            days_back: Number of days to look back for content
            min_score: Minimum trend score threshold (0-1)
            max_trends: Maximum number of trends to return
        
        Returns:
            List of detected trends with scores and metadata
        """
        self.initialize()
        
        logger.info(f"Detecting trends for user {user_id} (last {days_back} days)")
        
        # Get recent content from user's sources
        content_items = await self._get_recent_content(user_id, days_back)
        
        if not content_items:
            logger.warning(f"No content found for user {user_id}")
            return []
        
        logger.info(f"Analyzing {len(content_items)} content items")
        
        # Extract topics using Groq
        topics = await self._extract_topics(content_items)
        
        if not topics:
            logger.warning("No topics extracted from content")
            return []
        
        # Score trends using ensemble method
        scored_trends = await self._score_trends(topics, content_items)
        
        # Filter by minimum score and limit results
        filtered_trends = [
            trend for trend in scored_trends 
            if trend["score"] >= min_score
        ]
        
        # Sort by score descending
        filtered_trends.sort(key=lambda x: x["score"], reverse=True)
        
        # Limit to max_trends
        final_trends = filtered_trends[:max_trends]
        
        # Store trends in database
        await self._store_trends(user_id, final_trends)
        
        logger.info(f"Detected {len(final_trends)} trends for user {user_id}")
        
        return final_trends
    
    async def _get_recent_content(
        self,
        user_id: str,
        days_back: int
    ) -> List[Dict[str, Any]]:
        """
        Fetch recent content from user's sources
        
        Args:
            user_id: User ID
            days_back: Number of days to look back
        
        Returns:
            List of content items
        """
        try:
            # Calculate cutoff date
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            # Get user's sources
            sources_result = self.supabase.table("sources").select("id").eq(
                "user_id", user_id
            ).eq("status", "active").execute()
            
            if not sources_result.data:
                return []
            
            source_ids = [source["id"] for source in sources_result.data]
            
            # Get content from these sources
            content_result = self.supabase.table("source_content_cache").select(
                "id, source_id, content_type, title, content, url, metadata, published_at, created_at"
            ).in_("source_id", source_ids).gte(
                "created_at", cutoff_date.isoformat()
            ).order("created_at", desc=True).limit(100).execute()
            
            return content_result.data if content_result.data else []
            
        except Exception as e:
            logger.error(f"Error fetching recent content: {str(e)}")
            return []
    
    async def _extract_topics(
        self,
        content_items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract topics from content using Groq LLM
        
        Args:
            content_items: List of content items
        
        Returns:
            List of extracted topics with metadata
        """
        try:
            # Prepare content for analysis
            content_summaries = []
            for item in content_items[:50]:  # Limit to avoid token limits
                title = item.get("title", "")
                content = item.get("content", "")[:500]  # Truncate long content
                content_summaries.append({
                    "id": item["id"],
                    "title": title,
                    "snippet": content,
                    "source_id": item["source_id"],
                    "published_at": item.get("published_at")
                })
            
            # Create prompt for topic extraction
            prompt = self._create_topic_extraction_prompt(content_summaries)
            
            # Call Groq API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert content analyst specializing in identifying trending topics and themes. Provide analysis in valid JSON format only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.4,
                max_tokens=2000
            )
            
            # Parse response
            import json
            import re
            
            analysis_text = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                topics = result.get("topics", [])
                
                # Enrich topics with content references
                for topic in topics:
                    topic["content_ids"] = topic.get("content_ids", [])
                    topic["extracted_at"] = datetime.now().isoformat()
                
                return topics
            else:
                logger.warning("Failed to parse topic extraction response")
                return []
            
        except Exception as e:
            logger.error(f"Error extracting topics: {str(e)}")
            return []
    
    def _create_topic_extraction_prompt(
        self,
        content_summaries: List[Dict[str, Any]]
    ) -> str:
        """Create prompt for topic extraction"""
        
        content_text = "\n\n".join([
            f"[ID: {item['id']}]\nTitle: {item['title']}\nSnippet: {item['snippet']}"
            for item in content_summaries
        ])
        
        prompt = f"""Analyze the following content items and identify the main trending topics and themes.

CONTENT ITEMS:
{content_text}

Identify the top 10-15 trending topics/themes across this content. For each topic:
1. Provide a clear, concise topic name
2. Give a brief description
3. List the content IDs that discuss this topic
4. Estimate the topic's relevance (how important/interesting it is)

Provide your analysis in the following JSON format:

{{
  "topics": [
    {{
      "name": "Topic Name",
      "description": "Brief description of the topic",
      "content_ids": ["id1", "id2", "id3"],
      "keywords": ["keyword1", "keyword2"],
      "category": "technology/business/science/culture/etc",
      "relevance": 0.0-1.0
    }}
  ]
}}

Focus on topics that:
- Appear across multiple content items
- Are timely and newsworthy
- Would be interesting to newsletter readers
- Represent emerging trends or important developments

Provide ONLY the JSON object, no additional text."""

        return prompt
    
    async def _score_trends(
        self,
        topics: List[Dict[str, Any]],
        content_items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Score trends using ensemble detection method
        
        Combines multiple signals:
        - Frequency: How many content items mention this topic
        - Recency: How recent the content is
        - Engagement: Metadata signals (if available)
        - Relevance: LLM-assigned relevance score
        
        Args:
            topics: Extracted topics
            content_items: Original content items
        
        Returns:
            List of scored trends
        """
        scored_trends = []
        
        # Create content lookup
        content_by_id = {item["id"]: item for item in content_items}
        
        for topic in topics:
            # Frequency score (normalized by total content)
            frequency = len(topic.get("content_ids", []))
            frequency_score = min(frequency / 10.0, 1.0)  # Cap at 10 mentions
            
            # Recency score (based on content timestamps)
            recency_score = self._calculate_recency_score(
                topic.get("content_ids", []),
                content_by_id
            )
            
            # Engagement score (placeholder - can be enhanced with actual metrics)
            engagement_score = self._calculate_engagement_score(
                topic.get("content_ids", []),
                content_by_id
            )
            
            # Relevance score from LLM
            relevance_score = topic.get("relevance", 0.5)
            
            # Ensemble score (weighted average)
            ensemble_score = (
                0.3 * frequency_score +
                0.3 * recency_score +
                0.2 * engagement_score +
                0.2 * relevance_score
            )
            
            scored_trends.append({
                "topic": topic["name"],
                "description": topic.get("description", ""),
                "score": round(ensemble_score, 3),
                "signals": {
                    "frequency": round(frequency_score, 3),
                    "recency": round(recency_score, 3),
                    "engagement": round(engagement_score, 3),
                    "relevance": round(relevance_score, 3)
                },
                "metadata": {
                    "keywords": topic.get("keywords", []),
                    "category": topic.get("category", "general"),
                    "content_count": frequency,
                    "content_ids": topic.get("content_ids", [])
                },
                "manual_override": False  # Can be set by user later
            })
        
        return scored_trends
    
    def _calculate_recency_score(
        self,
        content_ids: List[str],
        content_by_id: Dict[str, Any]
    ) -> float:
        """Calculate recency score based on content timestamps"""
        if not content_ids:
            return 0.0
        
        now = datetime.now()
        scores = []
        
        for content_id in content_ids:
            content = content_by_id.get(content_id)
            if not content:
                continue
            
            # Get timestamp
            timestamp_str = content.get("published_at") or content.get("created_at")
            if not timestamp_str:
                continue
            
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                age_hours = (now - timestamp.replace(tzinfo=None)).total_seconds() / 3600
                
                # Exponential decay: newer content scores higher
                # Score 1.0 for content < 24h old, decays to ~0.1 after 7 days
                recency = max(0.0, 1.0 - (age_hours / 168))  # 168 hours = 7 days
                scores.append(recency)
            except Exception:
                continue
        
        return sum(scores) / len(scores) if scores else 0.5
    
    def _calculate_engagement_score(
        self,
        content_ids: List[str],
        content_by_id: Dict[str, Any]
    ) -> float:
        """
        Calculate engagement score based on metadata
        
        This is a placeholder that can be enhanced with actual engagement metrics
        like likes, shares, comments, etc. from the source platforms
        """
        if not content_ids:
            return 0.5
        
        # For now, return a baseline score
        # In the future, extract engagement metrics from metadata
        engagement_scores = []
        
        for content_id in content_ids:
            content = content_by_id.get(content_id)
            if not content:
                continue
            
            metadata = content.get("metadata", {})
            
            # Example: extract engagement signals if available
            # likes = metadata.get("likes", 0)
            # shares = metadata.get("shares", 0)
            # comments = metadata.get("comments", 0)
            
            # For now, use a baseline
            engagement_scores.append(0.5)
        
        return sum(engagement_scores) / len(engagement_scores) if engagement_scores else 0.5
    
    async def _store_trends(
        self,
        user_id: str,
        trends: List[Dict[str, Any]]
    ):
        """Store detected trends in database"""
        try:
            for trend in trends:
                self.supabase.table("trends").insert({
                    "user_id": user_id,
                    "topic": trend["topic"],
                    "score": trend["score"],
                    "sources": {
                        "description": trend.get("description", ""),
                        "signals": trend.get("signals", {}),
                        "metadata": trend.get("metadata", {}),
                        "manual_override": trend.get("manual_override", False)
                    }
                }).execute()
            
            logger.info(f"Stored {len(trends)} trends for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error storing trends: {str(e)}")
    
    async def get_user_trends(
        self,
        user_id: str,
        days_back: int = 7,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get previously detected trends for a user
        
        Args:
            user_id: User ID
            days_back: Number of days to look back
            limit: Maximum number of trends to return
        
        Returns:
            List of trends
        """
        self.initialize()
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            result = self.supabase.table("trends").select("*").eq(
                "user_id", user_id
            ).gte(
                "detected_at", cutoff_date.isoformat()
            ).order("score", desc=True).limit(limit).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error fetching user trends: {str(e)}")
            return []
    
    async def update_trend_override(
        self,
        trend_id: str,
        manual_override: bool,
        override_score: Optional[float] = None
    ) -> bool:
        """
        Update manual override flag for a trend
        
        Args:
            trend_id: Trend ID
            manual_override: Whether to manually override the trend
            override_score: Optional manual score override
        
        Returns:
            Success status
        """
        self.initialize()
        
        try:
            update_data = {
                "sources": {
                    "manual_override": manual_override
                }
            }
            
            if override_score is not None:
                update_data["score"] = override_score
            
            self.supabase.table("trends").update(update_data).eq("id", trend_id).execute()
            
            logger.info(f"Updated trend {trend_id} override: {manual_override}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating trend override: {str(e)}")
            return False


# Singleton instance
trend_detector = TrendDetector()
