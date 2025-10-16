"""
Draft Scheduler Service
Handles scheduled draft generation and delivery
"""

import logging
from datetime import datetime, time
from typing import List, Dict, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from supabase import Client

from app.core.database import get_supabase
from app.services.draft_generator import draft_generator
from app.services.email_service import email_service

logger = logging.getLogger(__name__)


class DraftScheduler:
    """Manages scheduled draft generation and delivery"""
    
    def __init__(self):
        self.scheduler: AsyncIOScheduler = None
        self.supabase: Client = None
    
    def initialize(self):
        """Initialize scheduler and database connection"""
        if not self.supabase:
            self.supabase = get_supabase()
    
    def start(self, scheduler: AsyncIOScheduler):
        """
        Start scheduled tasks
        
        Args:
            scheduler: APScheduler instance
        """
        self.scheduler = scheduler
        self.initialize()
        
        # Schedule daily draft generation at 8:00 AM
        # Note: This uses server time. For production, implement timezone handling per user
        self.scheduler.add_job(
            self.generate_daily_drafts,
            CronTrigger(hour=8, minute=0),
            id='daily_draft_generation',
            name='Generate daily newsletter drafts',
            replace_existing=True
        )
        
        logger.info("Draft scheduler started - daily drafts at 8:00 AM")
    
    async def generate_daily_drafts(self):
        """
        Generate drafts for all active users
        
        This runs daily at the scheduled time and generates drafts
        for users who have active sources and want daily newsletters.
        """
        logger.info("Starting daily draft generation")
        
        try:
            # Get all active users with sources
            users = await self._get_active_users()
            
            logger.info(f"Generating drafts for {len(users)} active user(s)")
            
            success_count = 0
            error_count = 0
            
            for user in users:
                try:
                    user_id = user["id"]
                    user_email = user.get("email")
                    
                    # Check user preferences for draft frequency
                    preferences = await self._get_user_preferences(user_id)
                    
                    # Skip if user has disabled daily drafts
                    if not preferences.get("daily_drafts_enabled", True):
                        logger.info(f"Skipping user {user_id} - daily drafts disabled")
                        continue
                    
                    # Generate draft
                    draft = await draft_generator.generate_draft(
                        user_id=user_id,
                        topic_count=preferences.get("topic_count", 5),
                        days_back=preferences.get("days_back", 7),
                        use_voice_profile=preferences.get("use_voice_profile", True)
                    )
                    
                    logger.info(f"Generated draft {draft['id']} for user {user_id}")
                    
                    # Send notification email if enabled
                    if preferences.get("send_draft_notification", True) and user_email:
                        await email_service.send_draft_notification(
                            draft_id=draft["id"],
                            user_email=user_email,
                            user_id=user_id
                        )
                    
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"Error generating draft for user {user.get('id')}: {str(e)}")
                    error_count += 1
            
            logger.info(f"Daily draft generation complete: {success_count} success, {error_count} errors")
            
            # Log summary to database
            await self._log_generation_summary(success_count, error_count)
            
        except Exception as e:
            logger.error(f"Error in daily draft generation: {str(e)}")
    
    async def _get_active_users(self) -> List[Dict[str, Any]]:
        """
        Get all active users who should receive daily drafts
        
        Returns:
            List of user dictionaries
        """
        try:
            # Get users who have active sources
            result = self.supabase.table("users").select(
                "id, email"
            ).execute()
            
            if not result.data:
                return []
            
            active_users = []
            
            for user in result.data:
                # Check if user has active sources
                sources_result = self.supabase.table("sources").select("id").eq(
                    "user_id", user["id"]
                ).eq("status", "active").execute()
                
                if sources_result.data:
                    active_users.append(user)
            
            return active_users
            
        except Exception as e:
            logger.error(f"Error fetching active users: {str(e)}")
            return []
    
    async def _get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        Get user's draft preferences
        
        Args:
            user_id: User ID
        
        Returns:
            Preferences dictionary with defaults
        """
        try:
            result = self.supabase.table("user_preferences").select("*").eq(
                "user_id", user_id
            ).execute()
            
            if result.data:
                return result.data[0].get("preferences", {})
            
            # Return defaults
            return {
                "daily_drafts_enabled": True,
                "topic_count": 5,
                "days_back": 7,
                "use_voice_profile": True,
                "send_draft_notification": True,
                "draft_time": "08:00"
            }
            
        except Exception as e:
            logger.error(f"Error fetching user preferences: {str(e)}")
            return {
                "daily_drafts_enabled": True,
                "topic_count": 5,
                "days_back": 7,
                "use_voice_profile": True,
                "send_draft_notification": True
            }
    
    async def _log_generation_summary(self, success_count: int, error_count: int):
        """
        Log draft generation summary to database
        
        Args:
            success_count: Number of successful generations
            error_count: Number of errors
        """
        try:
            self.supabase.table("draft_generation_logs").insert({
                "generated_at": datetime.now().isoformat(),
                "success_count": success_count,
                "error_count": error_count,
                "total_count": success_count + error_count
            }).execute()
            
        except Exception as e:
            logger.error(f"Error logging generation summary: {str(e)}")
    
    async def generate_draft_for_user(
        self,
        user_id: str,
        send_notification: bool = True
    ) -> Dict[str, Any]:
        """
        Manually trigger draft generation for a specific user
        
        Args:
            user_id: User ID
            send_notification: Whether to send email notification
        
        Returns:
            Draft dictionary
        """
        try:
            # Get user preferences
            preferences = await self._get_user_preferences(user_id)
            
            # Generate draft
            draft = await draft_generator.generate_draft(
                user_id=user_id,
                topic_count=preferences.get("topic_count", 5),
                days_back=preferences.get("days_back", 7),
                use_voice_profile=preferences.get("use_voice_profile", True)
            )
            
            # Send notification if requested
            if send_notification:
                user_result = self.supabase.table("users").select("email").eq(
                    "id", user_id
                ).execute()
                
                if user_result.data and user_result.data[0].get("email"):
                    await email_service.send_draft_notification(
                        draft_id=draft["id"],
                        user_email=user_result.data[0]["email"],
                        user_id=user_id
                    )
            
            return draft
            
        except Exception as e:
            logger.error(f"Error generating draft for user {user_id}: {str(e)}")
            raise


# Singleton instance
draft_scheduler = DraftScheduler()
