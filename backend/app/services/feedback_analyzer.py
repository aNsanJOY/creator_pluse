"""
Feedback Analyzer Service
Analyzes user feedback to improve draft generation and adjust writing style
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from supabase import Client
from groq import Groq

from app.core.config import settings
from app.core.database import get_supabase

logger = logging.getLogger(__name__)


class FeedbackAnalyzer:
    """Analyzes feedback and adjusts prompts for better draft generation"""
    
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = "openai/gpt-oss-20b"
        self.supabase: Optional[Client] = None
    
    def initialize(self):
        """Initialize database connection"""
        if not self.supabase:
            self.supabase = get_supabase()
    
    async def get_feedback_insights(self, user_id: str, days_back: int = 30) -> Dict[str, Any]:
        """
        Analyze user feedback to extract insights about preferences
        
        Args:
            user_id: User ID
            days_back: Number of days to look back for feedback
        
        Returns:
            Dictionary with feedback insights
        """
        self.initialize()
        
        try:
            # Get recent feedback
            cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()
            
            feedback_result = self.supabase.table("feedback").select(
                "*, newsletters(title, content, metadata)"
            ).eq("user_id", user_id).gte("created_at", cutoff_date).execute()
            
            if not feedback_result.data:
                logger.info(f"No feedback found for user {user_id}")
                return self._default_insights()
            
            feedback_data = feedback_result.data
            
            # Calculate statistics
            total_feedback = len(feedback_data)
            thumbs_up = sum(1 for f in feedback_data if f["feedback_type"] == "thumbs_up")
            thumbs_down = sum(1 for f in feedback_data if f["feedback_type"] == "thumbs_down")
            
            # Extract comments
            comments_positive = [f["comment"] for f in feedback_data 
                               if f["feedback_type"] == "thumbs_up" and f.get("comment")]
            comments_negative = [f["comment"] for f in feedback_data 
                                if f["feedback_type"] == "thumbs_down" and f.get("comment")]
            
            # Analyze patterns using Groq
            insights = await self._analyze_feedback_patterns(
                positive_comments=comments_positive,
                negative_comments=comments_negative,
                thumbs_up_count=thumbs_up,
                thumbs_down_count=thumbs_down
            )
            
            return {
                "total_feedback": total_feedback,
                "thumbs_up": thumbs_up,
                "thumbs_down": thumbs_down,
                "positive_rate": (thumbs_up / total_feedback * 100) if total_feedback > 0 else 0,
                "insights": insights,
                "has_sufficient_data": total_feedback >= 5
            }
            
        except Exception as e:
            logger.error(f"Error analyzing feedback: {str(e)}")
            return self._default_insights()
    
    async def _analyze_feedback_patterns(
        self,
        positive_comments: List[str],
        negative_comments: List[str],
        thumbs_up_count: int,
        thumbs_down_count: int
    ) -> Dict[str, Any]:
        """Use Groq to analyze feedback patterns"""
        
        try:
            prompt = f"""Analyze the following user feedback on newsletter drafts and provide insights:

Positive Feedback ({thumbs_up_count} thumbs up):
{chr(10).join(f"- {c}" for c in positive_comments[:10]) if positive_comments else "No comments"}

Negative Feedback ({thumbs_down_count} thumbs down):
{chr(10).join(f"- {c}" for c in negative_comments[:10]) if negative_comments else "No comments"}

Provide a JSON response with:
1. "liked_aspects": List of 3-5 things the user likes
2. "disliked_aspects": List of 3-5 things the user dislikes
3. "style_preferences": Writing style preferences (tone, length, structure)
4. "content_preferences": Content preferences (topics, depth, sources)
5. "recommendations": 3-5 specific recommendations for improvement

Keep the response concise and actionable."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a feedback analysis expert. Provide insights in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            # Parse response
            import json
            insights_text = response.choices[0].message.content.strip()
            
            # Try to extract JSON from response
            if "```json" in insights_text:
                insights_text = insights_text.split("```json")[1].split("```")[0].strip()
            elif "```" in insights_text:
                insights_text = insights_text.split("```")[1].split("```")[0].strip()
            
            insights = json.loads(insights_text)
            return insights
            
        except Exception as e:
            logger.error(f"Error analyzing patterns with Groq: {str(e)}")
            return {
                "liked_aspects": [],
                "disliked_aspects": [],
                "style_preferences": {},
                "content_preferences": {},
                "recommendations": []
            }
    
    def generate_adjusted_prompt(
        self,
        base_prompt: str,
        feedback_insights: Dict[str, Any],
        voice_profile: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Adjust the draft generation prompt based on feedback insights
        
        Args:
            base_prompt: Original prompt
            feedback_insights: Insights from feedback analysis
            voice_profile: User's voice profile
        
        Returns:
            Adjusted prompt string
        """
        if not feedback_insights.get("has_sufficient_data"):
            return base_prompt
        
        insights = feedback_insights.get("insights", {})
        
        # Build adjustment instructions
        adjustments = []
        
        # Add liked aspects to maintain
        liked = insights.get("liked_aspects", [])
        if liked:
            adjustments.append(f"MAINTAIN these aspects the user likes: {', '.join(liked)}")
        
        # Add disliked aspects to avoid
        disliked = insights.get("disliked_aspects", [])
        if disliked:
            adjustments.append(f"AVOID these aspects the user dislikes: {', '.join(disliked)}")
        
        # Add style preferences
        style_prefs = insights.get("style_preferences", {})
        if style_prefs:
            style_text = ", ".join(f"{k}: {v}" for k, v in style_prefs.items())
            adjustments.append(f"STYLE PREFERENCES: {style_text}")
        
        # Add content preferences
        content_prefs = insights.get("content_preferences", {})
        if content_prefs:
            content_text = ", ".join(f"{k}: {v}" for k, v in content_prefs.items())
            adjustments.append(f"CONTENT PREFERENCES: {content_text}")
        
        # Add recommendations
        recommendations = insights.get("recommendations", [])
        if recommendations:
            adjustments.append(f"IMPROVEMENTS: {', '.join(recommendations[:3])}")
        
        if not adjustments:
            return base_prompt
        
        # Combine base prompt with adjustments
        adjustment_text = "\n\n".join(adjustments)
        adjusted_prompt = f"""{base_prompt}

--- USER FEEDBACK ADJUSTMENTS ---
Based on previous feedback, please incorporate these preferences:

{adjustment_text}

---"""
        
        return adjusted_prompt
    
    def _default_insights(self) -> Dict[str, Any]:
        """Return default insights when no feedback is available"""
        return {
            "total_feedback": 0,
            "thumbs_up": 0,
            "thumbs_down": 0,
            "positive_rate": 0,
            "insights": {
                "liked_aspects": [],
                "disliked_aspects": [],
                "style_preferences": {},
                "content_preferences": {},
                "recommendations": []
            },
            "has_sufficient_data": False
        }
    
    async def get_section_feedback_summary(
        self,
        newsletter_id: str,
        section_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get feedback summary for a specific newsletter or section
        
        Args:
            newsletter_id: Newsletter ID
            section_id: Optional section ID
        
        Returns:
            Feedback summary
        """
        self.initialize()
        
        try:
            query = self.supabase.table("feedback").select("*").eq(
                "newsletter_id", newsletter_id
            )
            
            if section_id:
                query = query.eq("section_id", section_id)
            
            result = query.execute()
            
            if not result.data:
                return {
                    "total": 0,
                    "thumbs_up": 0,
                    "thumbs_down": 0,
                    "comments": []
                }
            
            feedback_data = result.data
            thumbs_up = sum(1 for f in feedback_data if f["feedback_type"] == "thumbs_up")
            thumbs_down = sum(1 for f in feedback_data if f["feedback_type"] == "thumbs_down")
            comments = [f["comment"] for f in feedback_data if f.get("comment")]
            
            return {
                "total": len(feedback_data),
                "thumbs_up": thumbs_up,
                "thumbs_down": thumbs_down,
                "positive_rate": (thumbs_up / len(feedback_data) * 100) if feedback_data else 0,
                "comments": comments
            }
            
        except Exception as e:
            logger.error(f"Error getting section feedback: {str(e)}")
            return {
                "total": 0,
                "thumbs_up": 0,
                "thumbs_down": 0,
                "comments": []
            }


# Global instance
feedback_analyzer = FeedbackAnalyzer()
