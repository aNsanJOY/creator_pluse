"""
Background crawler service for fetching content from sources.
Handles scheduled crawling, rate limiting, and content storage.
"""

import asyncio
from datetime import datetime
from typing import Optional
import logging
from supabase import Client

from app.core.database import get_supabase_client
from app.services.sources.base import SourceRegistry
from app.models.source import SourceStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CrawlerService:
    """
    Service for crawling content from sources.
    Supports both scheduled and on-demand crawling.
    """

    def __init__(self, supabase: Client):
        self.supabase = supabase

    async def crawl_source(self, source_id: str) -> dict:
        """
        Crawl a single source and store content.

        Args:
            source_id: ID of the source to crawl

        Returns:
            Dict with crawl results (success, items_fetched, error)
        """
        try:
            # Fetch source from database
            result = (
                self.supabase.table("sources").select("*").eq("id", source_id).execute()
            )

            if not result.data:
                return {
                    "success": False,
                    "error": "Source not found",
                    "items_fetched": 0,
                }

            source = result.data[0]
            source_type = source["source_type"]

            # Check if connector is available
            if not SourceRegistry.is_supported(source_type):
                logger.error(f"Unsupported source type: {source_type}")
                return {
                    "success": False,
                    "error": f"Unsupported source type: {source_type}",
                    "items_fetched": 0,
                }

            # Get connector class and create instance
            ConnectorClass = SourceRegistry.get_connector(source_type)
            connector = ConnectorClass(
                source_id=source_id,
                config=source.get("config", {}),
                credentials=source.get("credentials", {}),
            )

            # Validate connection
            is_valid = await connector.validate_connection()
            if not is_valid:
                logger.error(f"Source {source_id} connection validation failed")
                self._update_source_status(
                    source_id, SourceStatus.ERROR.value, "Connection validation failed"
                )
                return {
                    "success": False,
                    "error": "Connection validation failed",
                    "items_fetched": 0,
                }

            # Update config if it was modified during validation (e.g., handle to channel ID conversion)
            if connector.config != source.get("config", {}):
                logger.info(f"Updating source {source_id} config after validation")
                self.supabase.table("sources").update({"config": connector.config}).eq(
                    "id", source_id
                ).execute()

            # Determine since timestamp for delta crawl
            last_crawled_at = source.get("last_crawled_at")
            since = None
            if last_crawled_at:
                # Parse timestamp
                if isinstance(last_crawled_at, str):
                    since = datetime.fromisoformat(
                        last_crawled_at.replace("Z", "+00:00")
                    )
                else:
                    since = last_crawled_at

            # Fetch content
            logger.info(
                f"Fetching content from source {source_id} (type: {source_type})"
            )
            contents = await connector.fetch_content(since=since)

            # Store content in cache
            items_stored = 0
            for content in contents:
                try:
                    await self._store_content(source_id, source_type, content)
                    items_stored += 1
                except Exception as e:
                    logger.error(f"Error storing content: {e}")

            # Update source status
            self._update_source_status(
                source_id, SourceStatus.ACTIVE.value, None, datetime.utcnow()
            )

            logger.info(
                f"Crawl completed for source {source_id}: {items_stored} items fetched"
            )

            return {"success": True, "items_fetched": items_stored, "error": None}

        except Exception as e:
            logger.error(f"Error crawling source {source_id}: {e}")
            self._update_source_status(source_id, SourceStatus.ERROR.value, str(e))
            return {"success": False, "error": str(e), "items_fetched": 0}

    async def crawl_all_sources(self, user_id: Optional[str] = None) -> dict:
        """
        Crawl all active sources (optionally filtered by user).

        Args:
            user_id: Optional user ID to filter sources

        Returns:
            Dict with overall crawl results
        """
        try:
            # Fetch all active sources
            query = (
                self.supabase.table("sources")
                .select("id")
                .eq("status", SourceStatus.ACTIVE.value)
            )

            if user_id:
                query = query.eq("user_id", user_id)

            result = query.execute()

            if not result.data:
                logger.info("No active sources to crawl")
                return {
                    "success": True,
                    "sources_crawled": 0,
                    "total_items": 0,
                    "errors": [],
                }

            sources = result.data
            logger.info(f"Starting crawl for {len(sources)} sources")

            # Crawl each source
            total_items = 0
            errors = []

            for source in sources:
                source_id = source["id"]
                crawl_result = await self.crawl_source(source_id)

                if crawl_result["success"]:
                    total_items += crawl_result["items_fetched"]
                else:
                    errors.append(
                        {"source_id": source_id, "error": crawl_result["error"]}
                    )

                # Add delay between sources to avoid rate limiting
                await asyncio.sleep(2)

            logger.info(
                f"Crawl completed: {len(sources)} sources, {total_items} items, {len(errors)} errors"
            )

            return {
                "success": True,
                "sources_crawled": len(sources),
                "total_items": total_items,
                "errors": errors,
            }

        except Exception as e:
            logger.error(f"Error in crawl_all_sources: {e}")
            return {
                "success": False,
                "error": str(e),
                "sources_crawled": 0,
                "total_items": 0,
                "errors": [],
            }

    async def _store_content(self, source_id: str, source_type: str, content):
        """Store content in the source_content_cache table"""
        try:
            # Check if content already exists (by URL or unique identifier)
            if content.url:
                existing = (
                    self.supabase.table("source_content_cache")
                    .select("id")
                    .eq("source_id", source_id)
                    .eq("url", content.url)
                    .execute()
                )

                if existing.data:
                    logger.debug(f"Content already exists: {content.url}")
                    return

            # Determine content type based on source type
            content_type_map = {
                "youtube": "video",
                "twitter": "tweet",
                "rss": "article",
                "substack": "article",
                "medium": "article",
                "linkedin": "post",
                "podcast": "episode",
                "github": "code",
                "reddit": "post",
            }
            content_type = content_type_map.get(source_type, "article")

            # Insert new content
            content_data = {
                "source_id": source_id,
                "content_type": content_type,
                "title": content.title,
                "content": content.content,
                "url": content.url,
                "published_at": content.published_at.isoformat()
                if content.published_at
                else None,
                "metadata": content.metadata,
            }

            self.supabase.table("source_content_cache").insert(content_data).execute()
            logger.debug(f"Stored content: {content.title}")

        except Exception as e:
            logger.error(f"Error storing content: {e}")
            raise

    def _update_source_status(
        self,
        source_id: str,
        status: str,
        error_message: Optional[str] = None,
        last_crawled_at: Optional[datetime] = None,
    ):
        """Update source status in database"""
        try:
            update_data = {"status": status, "error_message": error_message}

            if last_crawled_at:
                update_data["last_crawled_at"] = last_crawled_at.isoformat()

            self.supabase.table("sources").update(update_data).eq(
                "id", source_id
            ).execute()

        except Exception as e:
            logger.error(f"Error updating source status: {e}")


async def crawl_source_task(source_id: str):
    """
    Background task to crawl a single source.
    Can be called from API endpoints or scheduled tasks.
    """
    supabase = get_supabase_client()
    crawler = CrawlerService(supabase)
    return await crawler.crawl_source(source_id)


async def crawl_all_sources_task(user_id: Optional[str] = None):
    """
    Background task to crawl all sources.
    Can be called from scheduled tasks.
    """
    supabase = get_supabase_client()
    crawler = CrawlerService(supabase)
    return await crawler.crawl_all_sources(user_id)
