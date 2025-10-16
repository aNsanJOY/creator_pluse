"""
Crawl Orchestration Service
Manages scheduled crawling of all user sources (Twitter, YouTube, RSS, etc.)
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import UUID

from supabase import Client
from app.core.database import get_supabase

logger = logging.getLogger(__name__)


class CrawlOrchestrator:
    """Orchestrates crawling across all sources for all users"""
    
    def __init__(self):
        self.supabase: Optional[Client] = None
    
    async def initialize(self):
        """Initialize database connection"""
        self.supabase = get_supabase()
    
    async def crawl_all_sources(self) -> Dict[str, Any]:
        """
        Crawl all active sources for all users
        This is the main entry point for scheduled crawls
        
        Returns:
            Summary of crawl results
        """
        logger.info("Starting scheduled crawl for all sources")
        start_time = datetime.utcnow()
        
        if not self.supabase:
            await self.initialize()
        
        summary = {
            "started_at": start_time.isoformat(),
            "total_sources": 0,
            "successful": 0,
            "failed": 0,
            "partial": 0,
            "total_items_fetched": 0,
            "total_items_new": 0,
            "errors": []
        }
        
        try:
            # Get all active sources
            sources = await self._get_active_sources()
            summary["total_sources"] = len(sources)
            
            logger.info(f"Found {len(sources)} active sources to crawl")
            
            # Group sources by user for better organization
            sources_by_user = {}
            for source in sources:
                user_id = source["user_id"]
                if user_id not in sources_by_user:
                    sources_by_user[user_id] = []
                sources_by_user[user_id].append(source)
            
            # Crawl sources for each user
            for user_id, user_sources in sources_by_user.items():
                logger.info(f"Crawling {len(user_sources)} sources for user {user_id}")
                
                # Mark batch crawl as started for this user
                await self._start_batch_crawl(user_id)
                
                user_successful = 0
                user_failed = 0
                user_start_time = datetime.utcnow()
                
                for source in user_sources:
                    try:
                        result = await self._crawl_source(source)
                        
                        if result["status"] == "success":
                            summary["successful"] += 1
                            user_successful += 1
                        elif result["status"] == "partial":
                            summary["partial"] += 1
                            user_successful += 1
                        else:
                            summary["failed"] += 1
                            user_failed += 1
                        
                        summary["total_items_fetched"] += result.get("items_fetched", 0)
                        summary["total_items_new"] += result.get("items_new", 0)
                        
                    except Exception as e:
                        logger.error(f"Error crawling source {source['id']}: {str(e)}")
                        summary["failed"] += 1
                        user_failed += 1
                        summary["errors"].append({
                            "source_id": source["id"],
                            "source_type": source["source_type"],
                            "error": str(e)
                        })
                
                # Mark batch crawl as completed for this user
                user_duration = (datetime.utcnow() - user_start_time).total_seconds()
                await self._complete_batch_crawl(user_id, user_successful, user_failed, int(user_duration))
            
            # Calculate duration
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            summary["completed_at"] = end_time.isoformat()
            summary["duration_seconds"] = duration
            
            logger.info(f"Crawl completed: {summary['successful']} successful, "
                       f"{summary['failed']} failed, {summary['partial']} partial")
            
            return summary
            
        except Exception as e:
            logger.error(f"Fatal error in crawl orchestration: {str(e)}")
            summary["errors"].append({"fatal_error": str(e)})
            return summary
    
    async def _get_active_sources(self) -> List[Dict[str, Any]]:
        """Get all active sources from database"""
        try:
            result = self.supabase.table("sources").select("*").eq("status", "active").execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error fetching active sources: {str(e)}")
            return []
    
    async def _crawl_source(self, source: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crawl a single source
        
        Args:
            source: Source record from database
        
        Returns:
            Crawl result summary
        """
        source_id = source["id"]
        source_type = source["source_type"]
        user_id = source["user_id"]
        
        logger.info(f"Crawling {source_type} source: {source['name']} (ID: {source_id})")
        
        # Create crawl log entry
        log_id = await self._create_crawl_log(user_id, source_id, "scheduled", "started")
        
        start_time = datetime.utcnow()
        result = {
            "source_id": source_id,
            "source_type": source_type,
            "status": "failed",
            "items_fetched": 0,
            "items_new": 0,
            "error": None
        }
        
        try:
            # Route to appropriate crawler based on source type
            if source_type == "rss":
                crawl_result = await self._crawl_rss_source(source)
            elif source_type == "twitter":
                crawl_result = await self._crawl_twitter_source(source)
            elif source_type == "youtube":
                crawl_result = await self._crawl_youtube_source(source)
            elif source_type == "github":
                crawl_result = await self._crawl_github_source(source)
            elif source_type == "reddit":
                crawl_result = await self._crawl_reddit_source(source)
            else:
                raise ValueError(f"Unsupported source type: {source_type}")
            
            result.update(crawl_result)
            
            # Update source last_crawled_at
            await self._update_source_crawl_time(source_id, success=True)
            
        except Exception as e:
            logger.error(f"Error crawling source {source_id}: {str(e)}")
            result["status"] = "failed"
            result["error"] = str(e)
            
            # Update source with error
            await self._update_source_crawl_time(source_id, success=False, error=str(e))
        
        finally:
            # Update crawl log
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            await self._update_crawl_log(
                log_id,
                status=result["status"],
                items_fetched=result["items_fetched"],
                items_new=result["items_new"],
                error_message=result.get("error"),
                duration_ms=duration_ms
            )
        
        return result
    
    async def _crawl_rss_source(self, source: Dict[str, Any]) -> Dict[str, Any]:
        """Crawl RSS feed source"""
        import feedparser
        
        url = source["url"]
        source_id = source["id"]
        
        try:
            # Parse RSS feed
            feed = feedparser.parse(url)
            
            # Check for critical errors (but be lenient with minor warnings)
            if feed.bozo and not feed.entries:
                # Only fail if there are no entries at all
                raise Exception(f"RSS feed error: {feed.bozo_exception}")
            
            items_fetched = len(feed.entries)
            items_new = 0
            
            # Process each entry
            for entry in feed.entries[:20]:  # Limit to 20 most recent
                try:
                    # Check if content already exists
                    existing = self.supabase.table("source_content_cache").select("id").eq(
                        "source_id", source_id
                    ).eq("url", entry.link).execute()
                    
                    if existing.data:
                        continue  # Skip existing content
                    
                    # Extract content
                    content = entry.get("summary", "") or entry.get("description", "")
                    title = entry.get("title", "")
                    published = entry.get("published_parsed")
                    
                    # Store in cache
                    self.supabase.table("source_content_cache").insert({
                        "source_id": source_id,
                        "content_type": "rss_article",
                        "title": title,
                        "content": content,
                        "url": entry.link,
                        "metadata": {
                            "author": entry.get("author"),
                            "tags": [tag.term for tag in entry.get("tags", [])]
                        },
                        "published_at": datetime(*published[:6]).isoformat() if published else None
                    }).execute()
                    
                    items_new += 1
                    
                except Exception as e:
                    logger.warning(f"Error processing RSS entry: {str(e)}")
                    continue
            
            return {
                "status": "success" if items_new > 0 else "partial",
                "items_fetched": items_fetched,
                "items_new": items_new
            }
            
        except Exception as e:
            raise Exception(f"RSS crawl failed: {str(e)}")
    
    async def _crawl_twitter_source(self, source: Dict[str, Any]) -> Dict[str, Any]:
        """Crawl Twitter source (placeholder for now)"""
        # TODO: Implement Twitter crawling
        logger.info(f"Twitter crawling not yet implemented for source {source['id']}")
        return {
            "status": "partial",
            "items_fetched": 0,
            "items_new": 0
        }
    
    async def _crawl_youtube_source(self, source: Dict[str, Any]) -> Dict[str, Any]:
        """Crawl YouTube source (placeholder for now)"""
        # TODO: Implement YouTube crawling
        logger.info(f"YouTube crawling not yet implemented for source {source['id']}")
        return {
            "status": "partial",
            "items_fetched": 0,
            "items_new": 0
        }
    
    async def _crawl_github_source(self, source: Dict[str, Any]) -> Dict[str, Any]:
        """Crawl GitHub source (placeholder for now)"""
        # TODO: Implement GitHub crawling
        logger.info(f"GitHub crawling not yet implemented for source {source['id']}")
        return {
            "status": "partial",
            "items_fetched": 0,
            "items_new": 0
        }
    
    async def _crawl_reddit_source(self, source: Dict[str, Any]) -> Dict[str, Any]:
        """Crawl Reddit source (placeholder for now)"""
        # TODO: Implement Reddit crawling
        logger.info(f"Reddit crawling not yet implemented for source {source['id']}")
        return {
            "status": "partial",
            "items_fetched": 0,
            "items_new": 0
        }
    
    async def _create_crawl_log(
        self,
        user_id: str,
        source_id: str,
        crawl_type: str,
        status: str
    ) -> str:
        """Create a new crawl log entry"""
        try:
            result = self.supabase.table("crawl_logs").insert({
                "user_id": user_id,
                "source_id": source_id,
                "crawl_type": crawl_type,
                "status": status
            }).execute()
            
            return result.data[0]["id"] if result.data else None
        except Exception as e:
            logger.error(f"Error creating crawl log: {str(e)}")
            return None
    
    async def _update_crawl_log(
        self,
        log_id: str,
        status: str,
        items_fetched: int = 0,
        items_new: int = 0,
        error_message: Optional[str] = None,
        duration_ms: Optional[int] = None
    ):
        """Update crawl log with results"""
        if not log_id:
            return
        
        try:
            update_data = {
                "status": status,
                "items_fetched": items_fetched,
                "items_new": items_new,
                "completed_at": datetime.utcnow().isoformat(),
                "duration_ms": duration_ms
            }
            
            if error_message:
                update_data["error_message"] = error_message
            
            self.supabase.table("crawl_logs").update(update_data).eq("id", log_id).execute()
        except Exception as e:
            logger.error(f"Error updating crawl log: {str(e)}")
    
    async def _update_source_crawl_time(
        self,
        source_id: str,
        success: bool = True,
        error: Optional[str] = None
    ):
        """Update source last_crawled_at and status"""
        try:
            update_data = {
                "last_crawled_at": datetime.utcnow().isoformat()
            }
            
            if success:
                update_data["status"] = "active"
                update_data["error_message"] = None
            else:
                update_data["status"] = "error"
                update_data["error_message"] = error
            
            self.supabase.table("sources").update(update_data).eq("id", source_id).execute()
        except Exception as e:
            logger.error(f"Error updating source crawl time: {str(e)}")
    
    async def _start_batch_crawl(self, user_id: str):
        """Mark batch crawl as started for a user"""
        try:
            # Ensure user has a crawl schedule record
            existing = self.supabase.table("user_crawl_schedule").select("*").eq(
                "user_id", user_id
            ).execute()
            
            if not existing.data:
                # Create new record
                self.supabase.table("user_crawl_schedule").insert({
                    "user_id": user_id,
                    "is_crawling": True,
                    "crawl_frequency_hours": 24
                }).execute()
            else:
                # Update existing record
                self.supabase.table("user_crawl_schedule").update({
                    "is_crawling": True
                }).eq("user_id", user_id).execute()
            
            logger.info(f"Marked batch crawl as started for user {user_id}")
        except Exception as e:
            logger.error(f"Error starting batch crawl for user {user_id}: {str(e)}")
    
    async def _complete_batch_crawl(
        self,
        user_id: str,
        sources_crawled: int,
        sources_failed: int,
        duration_seconds: int
    ):
        """Mark batch crawl as completed and schedule next crawl"""
        try:
            now = datetime.utcnow()
            
            # Get crawl frequency
            schedule = self.supabase.table("user_crawl_schedule").select("crawl_frequency_hours").eq(
                "user_id", user_id
            ).execute()
            
            frequency_hours = 24  # default
            if schedule.data:
                frequency_hours = schedule.data[0].get("crawl_frequency_hours", 24)
            
            # Calculate next scheduled crawl
            next_crawl = now + timedelta(hours=frequency_hours)
            
            # Update schedule
            self.supabase.table("user_crawl_schedule").update({
                "last_batch_crawl_at": now.isoformat(),
                "next_scheduled_crawl_at": next_crawl.isoformat(),
                "is_crawling": False,
                "last_crawl_duration_seconds": duration_seconds,
                "sources_crawled_count": sources_crawled,
                "sources_failed_count": sources_failed
            }).eq("user_id", user_id).execute()
            
            logger.info(f"Completed batch crawl for user {user_id}. "
                       f"Crawled: {sources_crawled}, Failed: {sources_failed}, "
                       f"Duration: {duration_seconds}s, Next: {next_crawl.isoformat()}")
        except Exception as e:
            logger.error(f"Error completing batch crawl for user {user_id}: {str(e)}")


# Singleton instance
crawl_orchestrator = CrawlOrchestrator()
