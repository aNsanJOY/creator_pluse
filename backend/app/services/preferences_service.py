"""
User Preferences Service
Handles fetching and caching user preferences for use across the application.
"""

from typing import Optional, Dict, Any
from supabase import Client
import logging

logger = logging.getLogger(__name__)


class PreferencesService:
    """Service for managing user preferences"""
    
    def __init__(self, supabase: Client):
        self.supabase = supabase
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    async def get_preferences(self, user_id: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Get user preferences from database with optional caching.
        
        Args:
            user_id: User ID to fetch preferences for
            use_cache: Whether to use cached preferences (default: True)
        
        Returns:
            Dictionary containing user preferences with defaults for missing values
        """
        # Check cache first
        if use_cache and user_id in self._cache:
            return self._cache[user_id]
        
        try:
            # Fetch from users table preferences JSONB column
            result = self.supabase.table("users").select("preferences").eq("id", user_id).execute()
            
            if result.data and len(result.data) > 0:
                # Get preferences JSONB object
                preferences = result.data[0].get("preferences", {})
                
                # If preferences is None or empty, use defaults
                if not preferences:
                    logger.info(f"Empty preferences for user {user_id}, using defaults")
                    return self._get_default_preferences()
                
                # Merge with defaults to ensure all keys exist
                default_prefs = self._get_default_preferences()
                
                # Deep merge preferences with defaults
                formatted_prefs = {
                    "draft_schedule_time": preferences.get("draft_schedule_time", default_prefs["draft_schedule_time"]),
                    "newsletter_frequency": preferences.get("newsletter_frequency", default_prefs["newsletter_frequency"]),
                    "use_voice_profile": preferences.get("use_voice_profile", default_prefs["use_voice_profile"]),
                    "tone_preferences": {
                        **default_prefs["tone_preferences"],
                        **preferences.get("tone_preferences", {})
                    },
                    "notification_preferences": {
                        **default_prefs["notification_preferences"],
                        **preferences.get("notification_preferences", {})
                    },
                    "email_preferences": {
                        **default_prefs["email_preferences"],
                        **preferences.get("email_preferences", {})
                    }
                }
                
                # Cache the result
                if use_cache:
                    self._cache[user_id] = formatted_prefs
                
                return formatted_prefs
            else:
                # No user found, return defaults
                logger.warning(f"User {user_id} not found, using default preferences")
                return self._get_default_preferences()
        
        except Exception as e:
            logger.error(f"Error fetching preferences for user {user_id}: {e}")
            return self._get_default_preferences()
    
    def _get_default_preferences(self) -> Dict[str, Any]:
        """Return default preferences"""
        return {
            "draft_schedule_time": "09:00",
            "newsletter_frequency": "weekly",
            "use_voice_profile": False,
            "tone_preferences": {
                "formality": "balanced",
                "enthusiasm": "moderate",
                "length_preference": "medium",
                "use_emojis": True,
            },
            "notification_preferences": {
                "email_on_draft_ready": True,
                "email_on_publish_success": True,
                "email_on_errors": True,
                "weekly_summary": False,
            },
            "email_preferences": {
                "default_subject_template": "{title} - Weekly Newsletter",
                "include_preview_text": True,
                "track_opens": False,
                "track_clicks": False,
            }
        }
    
    def clear_cache(self, user_id: Optional[str] = None):
        """
        Clear preferences cache.
        
        Args:
            user_id: If provided, clear cache for specific user. Otherwise clear all.
        """
        if user_id:
            self._cache.pop(user_id, None)
        else:
            self._cache.clear()
    
    def should_send_notification(self, user_id: str, notification_type: str) -> bool:
        """
        Check if a notification should be sent based on user preferences.
        
        Args:
            user_id: User ID
            notification_type: Type of notification (email_on_draft_ready, email_on_publish_success, etc.)
        
        Returns:
            Boolean indicating whether to send the notification
        """
        try:
            preferences = self.get_preferences(user_id)
            notification_prefs = preferences.get("notification_preferences", {})
            return notification_prefs.get(notification_type, True)
        except Exception as e:
            logger.error(f"Error checking notification preference: {e}")
            return True  # Default to sending if error
    
    async def get_voice_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user's voice profile if available and enabled.
        
        Args:
            user_id: User ID
        
        Returns:
            Voice profile dictionary or None if not available/enabled
        """
        try:
            preferences = await self.get_preferences(user_id)
            
            # Check if voice profile is enabled
            if not preferences.get("use_voice_profile", False):
                return None
            
            # Fetch voice profile from database
            result = self.supabase.table("users").select("voice_profile").eq("id", user_id).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]
            else:
                logger.warning(f"Voice profile enabled but not found for user {user_id}")
                return None
        
        except Exception as e:
            logger.error(f"Error fetching voice profile for user {user_id}: {e}")
            return None
    
    def build_tone_prompt(self, preferences: Dict[str, Any]) -> str:
        """
        Build LLM prompt instructions based on tone preferences.
        
        Args:
            preferences: User preferences dictionary
        
        Returns:
            String with tone instructions for LLM
        """
        tone_prefs = preferences.get("tone_preferences", {})
        
        # Formality instructions
        formality_map = {
            "casual": "Write in a friendly, conversational tone as if talking to a friend. Use contractions and informal language.",
            "balanced": "Write in a professional yet approachable tone. Balance formality with friendliness.",
            "formal": "Write in a business-like, structured, and formal tone. Use complete sentences and professional language."
        }
        
        # Enthusiasm instructions
        enthusiasm_map = {
            "low": "Keep the tone matter-of-fact and straightforward. Be informative without excessive excitement.",
            "moderate": "Be enthusiastic but not overwhelming. Show genuine interest in the content.",
            "high": "Be very excited and energetic about the content. Use exclamation points and enthusiastic language."
        }
        
        # Length instructions
        length_map = {
            "short": "Keep it concise and to the point. Aim for 200-300 words. Focus on key takeaways only.",
            "medium": "Provide balanced detail with good explanations. Aim for 400-600 words.",
            "long": "Be comprehensive with full explanations and context. Aim for 800-1200 words. Include examples and details."
        }
        
        formality = tone_prefs.get("formality", "balanced")
        enthusiasm = tone_prefs.get("enthusiasm", "moderate")
        length = tone_prefs.get("length_preference", "medium")
        use_emojis = tone_prefs.get("use_emojis", True)
        
        prompt = f"""
TONE & STYLE INSTRUCTIONS:

Formality: {formality_map.get(formality, formality_map['balanced'])}

Enthusiasm: {enthusiasm_map.get(enthusiasm, enthusiasm_map['moderate'])}

Length: {length_map.get(length, length_map['medium'])}

Emojis: {'Include relevant emojis to make the content more engaging and visual.' if use_emojis else 'Do not use emojis in the content.'}
"""
        
        return prompt.strip()
