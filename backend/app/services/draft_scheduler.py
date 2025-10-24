"""
Draft Scheduler Service
Handles scheduled draft generation and delivery
"""

import logging
from datetime import datetime, timezone
from typing import List, Dict, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from supabase import Client

from app.core.database import get_supabase
from app.services.draft_generator import draft_generator
from app.services.email_service import email_service
from app.services.preferences_service import PreferencesService

logger = logging.getLogger(__name__)


class DraftScheduler:
    """Manages scheduled draft generation and delivery"""
    
    def __init__(self):
        self.scheduler: AsyncIOScheduler = None
        self.supabase: Client = None
        self.preferences_service: PreferencesService = None
        self.user_jobs: Dict[str, str] = {}  # Track per-user job IDs
    
    def initialize(self):
        """Initialize scheduler and database connection"""
        if not self.supabase:
            self.supabase = get_supabase()
        if not self.preferences_service:
            self.preferences_service = PreferencesService(self.supabase)
    
    def start(self, scheduler: AsyncIOScheduler):
        """
        Start scheduled tasks
        
        Args:
            scheduler: APScheduler instance
        """
        self.scheduler = scheduler
        self.initialize()
        
        # Schedule per-user draft generation based on their preferences
        # This will be called periodically to update user schedules
        self.scheduler.add_job(
            self.update_user_schedules,
            CronTrigger(minute='*/30'),  # Check every 30 minutes
            id='update_user_schedules',
            name='Update per-user draft schedules',
            replace_existing=True
        )
        
        # Initial schedule setup
        self.scheduler.add_job(
            self.update_user_schedules,
            'date',  # Run once immediately
            id='initial_schedule_setup'
        )
        
        logger.info("Draft scheduler started - per-user scheduling enabled")
    
    async def update_user_schedules(self):
        """
        Update scheduled jobs for all users based on their preferences.
        Creates/updates per-user draft generation jobs.
        """
        logger.info("Updating user draft schedules")
        
        try:
            # Get all active users
            users = await self._get_active_users()
            
            for user in users:
                user_id = user["id"]
                
                try:
                    # Get user preferences
                    preferences = await self.preferences_service.get_preferences(user_id)
                    
                    # Get schedule time and frequency
                    schedule_time = preferences.get("draft_schedule_time", "09:00")
                    frequency = preferences.get("newsletter_frequency", "weekly")
                    
                    # Parse time
                    hour, minute = map(int, schedule_time.split(":"))
                    
                    # Create job ID for this user
                    job_id = f"draft_gen_user_{user_id}"
                    
                    # Remove existing job if it exists
                    if job_id in self.user_jobs:
                        try:
                            self.scheduler.remove_job(job_id)
                        except:
                            pass
                    
                    # Schedule based on frequency
                    if frequency == "daily":
                        # Daily at user's preferred time
                        self.scheduler.add_job(
                            self.generate_user_draft,
                            CronTrigger(hour=hour, minute=minute),
                            args=[user_id],
                            id=job_id,
                            name=f"Daily draft for user {user_id}",
                            replace_existing=True
                        )
                        self.user_jobs[user_id] = job_id
                        logger.info(f"Scheduled daily draft for user {user_id} at {schedule_time}")
                        
                    elif frequency == "weekly":
                        # Weekly on Monday at user's preferred time
                        self.scheduler.add_job(
                            self.generate_user_draft,
                            CronTrigger(day_of_week='mon', hour=hour, minute=minute),
                            args=[user_id],
                            id=job_id,
                            name=f"Weekly draft for user {user_id}",
                            replace_existing=True
                        )
                        self.user_jobs[user_id] = job_id
                        logger.info(f"Scheduled weekly draft for user {user_id} on Mondays at {schedule_time}")
                    
                except Exception as e:
                    logger.error(f"Error scheduling for user {user_id}: {str(e)}")
            
            logger.info(f"Updated schedules for {len(self.user_jobs)} users")
            
        except Exception as e:
            logger.error(f"Error updating user schedules: {str(e)}")
    
    async def generate_user_draft(self, user_id: str):
        """
        Generate draft for a specific user.
        
        Args:
            user_id: User ID to generate draft for
        """
        logger.info(f"Generating scheduled draft for user {user_id}")
        
        try:
            # Get user info
            user_result = self.supabase.table("users").select("email").eq("id", user_id).execute()
            if not user_result.data:
                logger.error(f"User {user_id} not found")
                return
            
            user_email = user_result.data[0].get("email")
            
            # Get preferences
            preferences = await self.preferences_service.get_preferences(user_id)
            
            # Generate draft
            draft = await draft_generator.generate_draft(
                user_id=user_id,
                topic_count=5,
                days_back=7
            )
            
            logger.info(f"Generated draft {draft['id']} for user {user_id}")
            
            # Send notification if enabled
            notification_prefs = preferences.get("notification_preferences", {})
            if notification_prefs.get("email_on_draft_ready", True) and user_email:
                await email_service.send_draft_notification(
                    draft_id=draft["id"],
                    user_email=user_email,
                    user_id=user_id
                )
            
        except Exception as e:
            logger.error(f"Error generating draft for user {user_id}: {str(e)}")
            
            # Send error notification if enabled
            try:
                preferences = await self.preferences_service.get_preferences(user_id)
                notification_prefs = preferences.get("notification_preferences", {})
                if notification_prefs.get("email_on_errors", True):
                    user_result = self.supabase.table("users").select("email").eq("id", user_id).execute()
                    if user_result.data:
                        user_email = user_result.data[0].get("email")
                        if user_email:
                            await email_service.send_error_notification(
                                user_email=user_email,
                                error_message=str(e),
                                user_id=user_id
                            )
            except Exception as notify_error:
                logger.error(f"Error sending error notification: {str(notify_error)}")
    
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
                    
                    # Get user preferences using PreferencesService
                    preferences = await self.preferences_service.get_preferences(user_id)
                    
                    # Check newsletter frequency
                    frequency = preferences.get("newsletter_frequency", "weekly")
                    if frequency not in ["daily", "weekly"]:
                        logger.info(f"Skipping user {user_id} - custom frequency not yet supported")
                        continue
                    
                    # Generate draft (use_voice_profile will be read from preferences by draft_generator)
                    draft = await draft_generator.generate_draft(
                        user_id=user_id,
                        topic_count=5,
                        days_back=7
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
        Get user's draft preferences from users.preferences JSONB field
        
        Args:
            user_id: User ID
        
        Returns:
            Preferences dictionary with defaults
        """
        try:
            # Query preferences from users table
            result = self.supabase.table("users").select("preferences").eq(
                "id", user_id
            ).execute()
            
            if result.data and len(result.data) > 0:
                prefs = result.data[0].get("preferences", {})
                # Return preferences if they exist, otherwise return defaults
                return prefs if prefs else self._get_default_preferences()
            
            # Return defaults if user not found
            return self._get_default_preferences()
            
        except Exception as e:
            logger.error(f"Error fetching user preferences: {str(e)}")
            return self._get_default_preferences()
    
    def _get_default_preferences(self) -> Dict[str, Any]:
        """
        Get default preferences for draft generation
        
        Returns:
            Default preferences dictionary
        """
        return {
            "daily_drafts_enabled": True,
            "topic_count": 5,
            "days_back": 7,
            "use_voice_profile": True,
            "send_draft_notification": True,
            "draft_schedule_time": "08:00"
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
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "success_count": success_count,
                "error_count": error_count,
                "total_count": success_count + error_count
            }).execute()
            
        except Exception as e:
            logger.error(f"Error logging generation summary: {str(e)}")
    
  
# Singleton instance
draft_scheduler = DraftScheduler()
