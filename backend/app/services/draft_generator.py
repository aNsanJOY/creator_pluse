"""
Draft Generation Service using Groq LLM
Generates newsletter drafts from trending topics and content summaries
"""

import logging
import uuid
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from groq import Groq
from supabase import Client

from app.core.config import settings
from app.core.database import get_supabase
from app.services.trend_detector import trend_detector
from app.services.content_summarizer import content_summarizer
from app.services.feedback_analyzer import feedback_analyzer
from app.services.llm_usage_tracker import llm_usage_tracker

logger = logging.getLogger(__name__)


class DraftGenerator:
    """Generates newsletter drafts using Groq LLM"""
    
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = "openai/gpt-oss-20b"
        self.supabase: Optional[Client] = None
    
    def initialize(self):
        """Initialize database connection"""
        if not self.supabase:
            self.supabase = get_supabase()
    
    async def generate_draft(
        self,
        user_id: str,
        topic_count: int = 5,
        days_back: int = 7,
        use_voice_profile: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a newsletter draft for a user
        
        Args:
            user_id: User ID
            topic_count: Number of topics to include (3-10)
            days_back: Days to look back for content
            use_voice_profile: Whether to use user's voice profile
        
        Returns:
            Draft dictionary with sections and metadata
        """
        self.initialize()
        
        logger.info(f"Generating draft for user {user_id} with {topic_count} topics")
        
        try:
            # Get trending topics with lower threshold for better results
            trends = await trend_detector.detect_trends(
                user_id=user_id,
                days_back=days_back,
                min_score=0.2,  # Lowered from 0.3 to find more trends
                max_trends=topic_count
            )
            
            if not trends:
                logger.warning(f"No trends found for user {user_id} with min_score=0.2")
                # Try again with even lower threshold
                trends = await trend_detector.detect_trends(
                    user_id=user_id,
                    days_back=days_back,
                    min_score=0.1,
                    max_trends=topic_count
                )
                
            if not trends:
                logger.warning(f"Still no trends found for user {user_id}, creating fallback draft")
                return await self._create_fallback_draft(user_id, days_back)
            
            logger.info(f"Found {len(trends)} trends for draft")
            
            # Get summaries for trend content
            trend_summaries = await self._get_trend_summaries(trends, user_id)
            
            # Get user's voice profile if requested
            voice_profile = None
            if use_voice_profile:
                voice_profile = await self._get_voice_profile(user_id)
            
            # Get feedback insights to adjust generation
            feedback_insights = await feedback_analyzer.get_feedback_insights(
                user_id=user_id,
                days_back=30
            )
            
            # Generate draft using Groq
            draft_content = await self._generate_draft_content(
                trends=trends,
                summaries=trend_summaries,
                voice_profile=voice_profile,
                feedback_insights=feedback_insights,
                user_id=user_id
            )
            
            # Store draft in database
            stored_draft = await self._store_draft(
                user_id=user_id,
                draft_data=draft_content,
                trends=trends
            )
            
            logger.info(f"Draft generated successfully: {stored_draft['id']}")
            
            return stored_draft
            
        except Exception as e:
            logger.error(f"Error generating draft: {str(e)}")
            raise
    
    async def regenerate_draft(
        self,
        draft_id: str,
        user_id: str,
        topic_count: Optional[int] = None,
        use_voice_profile: bool = True
    ) -> Dict[str, Any]:
        """
        Regenerate an existing draft
        
        Args:
            draft_id: Draft ID to regenerate
            user_id: User ID
            topic_count: Optional new topic count
            use_voice_profile: Whether to use voice profile
        
        Returns:
            Updated draft dictionary
        """
        self.initialize()
        
        logger.info(f"Regenerating draft {draft_id}")
        
        # Get existing draft
        result = self.supabase.table("newsletter_drafts").select("*").eq(
            "id", draft_id
        ).eq("user_id", user_id).execute()
        
        if not result.data:
            raise ValueError(f"Draft {draft_id} not found")
        
        old_draft = result.data[0]
        
        # Use existing topic count if not specified
        if topic_count is None:
            topic_count = len(old_draft.get("sections", [])) - 2  # Exclude intro/conclusion
            topic_count = max(3, min(10, topic_count))
        
        # Check if old draft was a fallback (no content found)
        # If so, try with a longer lookback period
        old_metadata = old_draft.get("metadata", {})
        was_fallback = old_metadata.get("fallback", False)
        
        # Use longer lookback for regeneration to find more content
        # If previous draft was fallback, try even longer period
        days_back = 14 if was_fallback else 10
        
        logger.info(f"Regenerating with days_back={days_back}, topic_count={topic_count}")
        
        # Generate new draft
        new_draft = await self.generate_draft(
            user_id=user_id,
            topic_count=topic_count,
            days_back=days_back,
            use_voice_profile=use_voice_profile
        )
        
        # Delete old draft
        self.supabase.table("newsletter_drafts").delete().eq("id", draft_id).execute()
        
        return new_draft
    
    async def _get_trend_summaries(
        self,
        trends: List[Dict[str, Any]],
        user_id: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get summaries for content related to trends
        
        Args:
            trends: List of trend dictionaries
            user_id: User ID
        
        Returns:
            Dictionary mapping trend topic to list of summaries
        """
        trend_summaries = {}
        
        for trend in trends:
            topic = trend["topic"]
            content_ids = trend.get("metadata", {}).get("content_ids", [])
            
            if not content_ids:
                trend_summaries[topic] = []
                continue
            
            # Get summaries for these content items
            summaries_dict = await content_summarizer.get_summaries_for_content(
                content_ids=content_ids[:5],  # Limit to top 5 per trend
                user_id=user_id
            )
            
            # If summaries don't exist, generate them
            missing_ids = [cid for cid in content_ids[:5] if cid not in summaries_dict]
            if missing_ids:
                new_summaries = await content_summarizer.summarize_batch(
                    content_ids=missing_ids,
                    user_id=user_id,
                    summary_type="brief"
                )
                for summary in new_summaries:
                    if "error" not in summary:
                        summaries_dict[summary["content_id"]] = summary
            
            trend_summaries[topic] = list(summaries_dict.values())
        
        return trend_summaries
    
    async def _get_voice_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's voice profile from database"""
        try:
            result = self.supabase.table("voice_profiles").select("*").eq(
                "user_id", user_id
            ).order("created_at", desc=True).limit(1).execute()
            
            if result.data:
                return result.data[0].get("profile_data", {})
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching voice profile: {str(e)}")
            return None
    
    async def _generate_draft_content(
        self,
        trends: List[Dict[str, Any]],
        summaries: Dict[str, List[Dict[str, Any]]],
        voice_profile: Optional[Dict[str, Any]],
        feedback_insights: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """
        Generate draft content using Groq LLM
        
        Args:
            trends: List of trending topics
            summaries: Summaries for each trend
            voice_profile: User's voice profile
            feedback_insights: Insights from user feedback
            user_id: User ID
        
        Returns:
            Draft content dictionary
        """
        try:
            # Create base prompt
            base_prompt = self._create_draft_prompt(trends, summaries, voice_profile)
            
            # Adjust prompt based on feedback
            prompt = feedback_analyzer.generate_adjusted_prompt(
                base_prompt=base_prompt,
                feedback_insights=feedback_insights,
                voice_profile=voice_profile
            )
            
            # Track API call timing
            start_time = time.time()
            
            # Call Groq API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert newsletter writer. Create engaging, well-structured newsletters in valid JSON format."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,  # Higher temperature for creative writing
                max_tokens=3000
            )
            
            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Log usage
            if user_id:
                try:
                    await llm_usage_tracker.log_llm_call(
                        user_id=user_id,
                        model=self.model,
                        endpoint="/v1/chat/completions",
                        status_code=200,
                        tokens_used=response.usage.total_tokens if response.usage else 0,
                        prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
                        completion_tokens=response.usage.completion_tokens if response.usage else 0,
                        duration_ms=duration_ms,
                        metadata={"service": "draft_generator", "trends_count": len(trends)}
                    )
                except Exception as log_error:
                    import traceback
                    logger.error(f"Failed to log LLM usage: {log_error}")
                    logger.error(traceback.format_exc())
            
            # Parse response
            import json
            import re
            
            draft_text = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', draft_text, re.DOTALL)
            if json_match:
                draft_data = json.loads(json_match.group())
            else:
                # Fallback: create basic structure
                draft_data = self._create_fallback_structure(trends, summaries)
            
            # Add metadata
            draft_data["generated_at"] = datetime.now().isoformat()
            draft_data["model_used"] = self.model
            draft_data["voice_profile_used"] = voice_profile is not None
            
            return draft_data
            
        except Exception as e:
            logger.error(f"Error generating draft content: {str(e)}")
            # Return fallback structure
            return self._create_fallback_structure(trends, summaries)
    
    def _create_draft_prompt(
        self,
        trends: List[Dict[str, Any]],
        summaries: Dict[str, List[Dict[str, Any]]],
        voice_profile: Optional[Dict[str, Any]]
    ) -> str:
        """Create prompt for draft generation"""
        
        # Format trends and summaries
        trends_text = ""
        for i, trend in enumerate(trends, 1):
            topic = trend["topic"]
            description = trend.get("description", "")
            score = trend.get("score", 0)
            
            trends_text += f"\n{i}. {topic} (Score: {score:.2f})\n"
            trends_text += f"   Description: {description}\n"
            
            # Add summaries for this trend
            trend_summaries = summaries.get(topic, [])
            if trend_summaries:
                trends_text += "   Key Content:\n"
                for summary in trend_summaries[:3]:  # Top 3 summaries
                    trends_text += f"   - {summary.get('title', 'Untitled')}\n"
                    trends_text += f"     {summary.get('summary', '')[:200]}...\n"
        
        # Format voice profile
        voice_instructions = ""
        if voice_profile:
            tone = voice_profile.get("tone", "professional")
            style = voice_profile.get("style", "informative")
            voice_instructions = f"""
WRITING STYLE REQUIREMENTS:
- Tone: {tone}
- Style: {style}
- Personality traits: {', '.join(voice_profile.get('personality_traits', []))}
- Intro style: {voice_profile.get('content_preferences', {}).get('intro_style', 'engaging')}
- Conclusion style: {voice_profile.get('content_preferences', {}).get('conclusion_style', 'call to action')}

Match this writing voice throughout the newsletter.
"""
        else:
            voice_instructions = """
WRITING STYLE REQUIREMENTS:
- Tone: Professional yet approachable
- Style: Informative and engaging
- Keep it friendly and conversational
"""
        
        prompt = f"""Create a newsletter draft based on the following trending topics and content.

TRENDING TOPICS:
{trends_text}

{voice_instructions}

Create a complete newsletter with the following structure:

1. **Introduction**: Warm, engaging opening that sets context for the newsletter
2. **Topic Sections**: One section for each trending topic with:
   - Catchy section title
   - Summary of the trend and why it matters
   - Key insights from the content
   - Links to original sources
3. **Conclusion**: Wrap up with key takeaways or a thought-provoking question

Provide your newsletter in the following JSON format:

{{
  "title": "Engaging newsletter title",
  "sections": [
    {{
      "id": "intro",
      "type": "intro",
      "title": null,
      "content": "Introduction paragraph...",
      "source_ids": [],
      "metadata": {{}}
    }},
    {{
      "id": "topic-1",
      "type": "topic",
      "title": "Topic Title",
      "content": "Topic content with insights and commentary...",
      "source_ids": ["content_id_1", "content_id_2"],
      "metadata": {{
        "trend_topic": "Topic Name",
        "trend_score": 0.85
      }}
    }},
    {{
      "id": "conclusion",
      "type": "conclusion",
      "title": null,
      "content": "Conclusion paragraph...",
      "source_ids": [],
      "metadata": {{}}
    }}
  ],
  "metadata": {{
    "topic_count": {len(trends)},
    "estimated_read_time": "5 min"
  }}
}}

Guidelines:
- Make it engaging and newsletter-friendly
- Include specific insights, not just summaries
- Add your own commentary and perspective
- Keep sections concise but informative
- Use markdown formatting for emphasis
- Include source references in content

Provide ONLY the JSON object, no additional text."""

        return prompt
    
    def _create_fallback_structure(
        self,
        trends: List[Dict[str, Any]],
        summaries: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Create fallback draft structure when LLM fails"""
        
        sections = []
        
        # Intro section
        sections.append({
            "id": "intro",
            "type": "intro",
            "title": None,
            "content": "Here are the top trending topics from your sources this week:",
            "source_ids": [],
            "metadata": {}
        })
        
        # Topic sections
        for i, trend in enumerate(trends, 1):
            topic = trend["topic"]
            description = trend.get("description", "")
            content_ids = trend.get("metadata", {}).get("content_ids", [])[:3]
            
            # Build content from summaries
            content = f"{description}\n\n"
            trend_summaries = summaries.get(topic, [])
            
            if trend_summaries:
                content += "Key highlights:\n\n"
                for summary in trend_summaries[:3]:
                    content += f"- **{summary.get('title', 'Untitled')}**\n"
                    content += f"  {summary.get('summary', '')}\n\n"
            
            sections.append({
                "id": f"topic-{i}",
                "type": "topic",
                "title": topic,
                "content": content,
                "source_ids": content_ids,
                "metadata": {
                    "trend_topic": topic,
                    "trend_score": trend.get("score", 0)
                }
            })
        
        # Conclusion section
        sections.append({
            "id": "conclusion",
            "type": "conclusion",
            "title": None,
            "content": "That's all for this week. Stay informed and keep creating!",
            "source_ids": [],
            "metadata": {}
        })
        
        return {
            "title": f"Weekly Digest - {datetime.now().strftime('%B %d, %Y')}",
            "sections": sections,
            "metadata": {
                "topic_count": len(trends),
                "estimated_read_time": f"{len(trends) * 2} min",
                "fallback": True
            }
        }
    
    async def _create_fallback_draft(
        self,
        user_id: str,
        days_back: int,
        store: bool = True
    ) -> Dict[str, Any]:
        """Create a fallback draft when no trends are found"""
        
        logger.info(f"Creating fallback draft for user {user_id}")
        
        # Get recent summaries instead
        summaries = await content_summarizer.summarize_recent_content(
            user_id=user_id,
            days_back=days_back,
            limit=5,
            summary_type="brief"
        )
        
        sections = []
        has_content = len(summaries) > 0
        
        if has_content:
            # Intro when we have some content
            sections.append({
                "id": "intro",
                "type": "intro",
                "title": None,
                "content": "Here's a summary of recent content from your sources:",
                "source_ids": [],
                "metadata": {}
            })
            
            # Add summaries as sections
            for i, summary in enumerate(summaries[:5], 1):
                if "error" not in summary:
                    sections.append({
                        "id": f"item-{i}",
                        "type": "topic",
                        "title": summary.get("title", "Untitled"),
                        "content": summary.get("summary", ""),
                        "source_ids": [summary.get("content_id", "")],
                        "metadata": {}
                    })
            
            # Conclusion
            sections.append({
                "id": "conclusion",
                "type": "conclusion",
                "title": None,
                "content": "That's all for now. Check back soon for more updates!",
                "source_ids": [],
                "metadata": {}
            })
        else:
            # No content available - provide helpful guidance
            sections.append({
                "id": "intro",
                "type": "intro",
                "title": "No Content Available",
                "content": "We couldn't find any content to create a newsletter from. This usually happens when:\n\n• No content sources are connected\n• Sources haven't been crawled yet\n• No new content has been published in the last " + str(days_back) + " days",
                "source_ids": [],
                "metadata": {}
            })
            
            sections.append({
                "id": "action",
                "type": "topic",
                "title": "What to do next",
                "content": "1. **Connect Content Sources**: Go to the Sources page and add Twitter accounts, YouTube channels, RSS feeds, or other sources.\n\n2. **Crawl Your Sources**: After adding sources, trigger a manual crawl to fetch recent content.\n\n3. **Wait for Content**: If sources are already connected, wait for new content to be published and crawled.\n\n4. **Try Again**: Once you have content, regenerate this draft to get a proper newsletter.",
                "source_ids": [],
                "metadata": {}
            })
            
            sections.append({
                "id": "conclusion",
                "type": "conclusion",
                "title": None,
                "content": "Need help? Check the documentation or contact support.",
                "source_ids": [],
                "metadata": {}
            })
        
        draft_data = {
            "title": f"Content Digest - {datetime.now(timezone.utc).strftime('%B %d, %Y')}" if has_content else "No Content Available",
            "sections": sections,
            "metadata": {
                "topic_count": len(summaries),
                "estimated_read_time": f"{len(summaries) * 2} min" if has_content else "0 min",
                "fallback": True,
                "no_trends": True,
                "no_content": not has_content
            },
            "generated_at": datetime.now().isoformat()
        }
        
        if store:
            return await self._store_draft(user_id, draft_data, [])
        else:
            return draft_data
    
    async def _store_draft(
        self,
        user_id: str,
        draft_data: Dict[str, Any],
        trends: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Store draft in database"""
        try:
            insert_data = {
                "user_id": user_id,
                "title": draft_data.get("title", ""),
                "sections": draft_data.get("sections", []),
                "status": "ready",
                "metadata": {
                    **draft_data.get("metadata", {}),
                    "trends_used": [t["topic"] for t in trends],
                    "model_used": draft_data.get("model_used", self.model),
                    "voice_profile_used": draft_data.get("voice_profile_used", False)
                },
                "generated_at": datetime.now().isoformat(),
                "email_sent": False
            }
            
            result = self.supabase.table("newsletter_drafts").insert(insert_data).execute()
            
            if result.data:
                stored = result.data[0]
                logger.info(f"Stored draft {stored['id']}")
                
                return {
                    "id": stored["id"],
                    "user_id": stored["user_id"],
                    "title": stored["title"],
                    "sections": stored["sections"],
                    "status": stored["status"],
                    "metadata": stored.get("metadata", {}),
                    "generated_at": stored["generated_at"],
                    "email_sent": stored.get("email_sent", False)
                }
            
            return draft_data
            
        except Exception as e:
            logger.error(f"Error storing draft: {str(e)}")
            raise


# Singleton instance
draft_generator = DraftGenerator()
