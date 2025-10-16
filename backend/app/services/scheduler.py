"""
Scheduled task manager using APScheduler.
Handles periodic crawling and other background tasks.
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import logging
from datetime import datetime

from app.services.crawl_orchestrator import crawl_orchestrator
from app.services.draft_scheduler import draft_scheduler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SchedulerService:
    """
    Service for managing scheduled background tasks.
    """
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._is_running = False
    
    def start(self):
        """Start the scheduler"""
        if self._is_running:
            logger.warning("Scheduler is already running")
            return
        
        # Schedule daily crawl at 2:00 AM UTC
        self.scheduler.add_job(
            self._daily_crawl_job,
            trigger=CronTrigger(hour=2, minute=0),
            id="daily_crawl",
            name="Daily source crawl",
            replace_existing=True
        )
        
        # Schedule hourly crawl for high-frequency sources
        self.scheduler.add_job(
            self._hourly_crawl_job,
            trigger=IntervalTrigger(hours=1),
            id="hourly_crawl",
            name="Hourly source crawl",
            replace_existing=True
        )
        
        # Initialize draft scheduler
        draft_scheduler.start(self.scheduler)
        
        self.scheduler.start()
        self._is_running = True
        logger.info("Scheduler started successfully")
    
    def stop(self):
        """Stop the scheduler"""
        if not self._is_running:
            logger.warning("Scheduler is not running")
            return
        
        self.scheduler.shutdown()
        self._is_running = False
        logger.info("Scheduler stopped")
    
    async def _daily_crawl_job(self):
        """Daily crawl job - crawls all sources"""
        logger.info("Starting daily crawl job")
        try:
            await crawl_orchestrator.initialize()
            result = await crawl_orchestrator.crawl_all_sources()
            logger.info(f"Daily crawl completed: {result}")
            
            # Send alert if too many failures
            if result.get("failed", 0) > 5:
                await self._send_admin_alert("Daily Crawl Alert", 
                    f"Daily crawl had {result['failed']} failures")
        except Exception as e:
            logger.error(f"Error in daily crawl job: {e}")
            await self._send_admin_alert("Daily Crawl Error", str(e))
    
    async def _hourly_crawl_job(self):
        """Hourly crawl job - crawls high-priority sources"""
        logger.info("Starting hourly crawl job")
        try:
            await crawl_orchestrator.initialize()
            result = await crawl_orchestrator.crawl_all_sources()
            logger.info(f"Hourly crawl completed: {result}")
        except Exception as e:
            logger.error(f"Error in hourly crawl job: {e}")
    
    async def _send_admin_alert(self, subject: str, message: str):
        """Send alert to admin about critical failures"""
        try:
            from app.services.email_service import send_email
            from app.core.config import settings
            
            # Send email to admin (using GMAIL_EMAIL as admin email)
            await send_email(
                to_email=settings.GMAIL_EMAIL,
                subject=f"[CreatorPulse Alert] {subject}",
                body=f"""
                Alert from CreatorPulse Scheduled Crawl System
                
                Subject: {subject}
                Time: {datetime.now().isoformat()}
                
                Details:
                {message}
                
                Please check the crawl logs for more information.
                """
            )
            logger.info(f"Admin alert sent: {subject}")
        except Exception as e:
            logger.error(f"Failed to send admin alert: {e}")
    
    def add_custom_job(self, func, trigger, job_id: str, name: str):
        """
        Add a custom scheduled job.
        
        Args:
            func: Function to execute
            trigger: APScheduler trigger (CronTrigger, IntervalTrigger, etc.)
            job_id: Unique job identifier
            name: Human-readable job name
        """
        self.scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            name=name,
            replace_existing=True
        )
        logger.info(f"Added custom job: {name} ({job_id})")
    
    def remove_job(self, job_id: str):
        """Remove a scheduled job by ID"""
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed job: {job_id}")
        except Exception as e:
            logger.error(f"Error removing job {job_id}: {e}")
    
    def get_jobs(self):
        """Get all scheduled jobs"""
        return self.scheduler.get_jobs()


# Global scheduler instance
scheduler_service = SchedulerService()


def start_scheduler():
    """Start the global scheduler"""
    scheduler_service.start()


def stop_scheduler():
    """Stop the global scheduler"""
    scheduler_service.stop()


def get_scheduler() -> SchedulerService:
    """Get the global scheduler instance"""
    return scheduler_service
