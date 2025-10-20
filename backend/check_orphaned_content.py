"""
Script to identify and optionally clean up orphaned content references in trends table.

This script checks for content_ids in the trends.sources JSONB field that no longer
exist in the source_content_cache table.

Usage:
    python check_orphaned_content.py [--fix]
    
    --fix: Actually remove orphaned content_ids from trends (default: dry-run only)
"""

import asyncio
import argparse
import logging
from typing import List, Dict, Any, Set
from app.core.database import get_supabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def get_all_trends() -> List[Dict[str, Any]]:
    """Fetch all trends from database"""
    supabase = get_supabase()
    result = supabase.table("trends").select("*").execute()
    return result.data or []


async def get_existing_content_ids() -> Set[str]:
    """Fetch all existing content IDs from source_content_cache"""
    supabase = get_supabase()
    result = supabase.table("source_content_cache").select("id").execute()
    return {item["id"] for item in (result.data or [])}


async def find_orphaned_references(trends: List[Dict[str, Any]], existing_ids: Set[str]) -> Dict[str, Any]:
    """
    Find trends with orphaned content references
    
    Returns:
        Dictionary with statistics and list of affected trends
    """
    orphaned_trends = []
    total_orphaned_refs = 0
    total_content_refs = 0
    
    for trend in trends:
        sources = trend.get("sources", {})
        metadata = sources.get("metadata", {}) if isinstance(sources, dict) else {}
        content_ids = metadata.get("content_ids", [])
        
        if not content_ids:
            continue
        
        total_content_refs += len(content_ids)
        orphaned_ids = [cid for cid in content_ids if cid not in existing_ids]
        
        if orphaned_ids:
            orphaned_trends.append({
                "trend_id": trend["id"],
                "topic": trend["topic"],
                "user_id": trend["user_id"],
                "total_content_ids": len(content_ids),
                "orphaned_content_ids": orphaned_ids,
                "orphaned_count": len(orphaned_ids),
                "detected_at": trend["detected_at"]
            })
            total_orphaned_refs += len(orphaned_ids)
    
    return {
        "total_trends": len(trends),
        "affected_trends": len(orphaned_trends),
        "total_content_refs": total_content_refs,
        "total_orphaned_refs": total_orphaned_refs,
        "orphaned_trends": orphaned_trends
    }


async def clean_orphaned_references(orphaned_data: Dict[str, Any], existing_ids: Set[str]) -> int:
    """
    Remove orphaned content_ids from trends
    
    Returns:
        Number of trends updated
    """
    supabase = get_supabase()
    updated_count = 0
    
    for trend_info in orphaned_data["orphaned_trends"]:
        trend_id = trend_info["trend_id"]
        
        # Fetch the current trend
        result = supabase.table("trends").select("*").eq("id", trend_id).execute()
        if not result.data:
            continue
        
        trend = result.data[0]
        sources = trend.get("sources", {})
        
        if not isinstance(sources, dict):
            continue
        
        metadata = sources.get("metadata", {})
        content_ids = metadata.get("content_ids", [])
        
        # Filter out orphaned IDs
        valid_content_ids = [cid for cid in content_ids if cid in existing_ids]
        
        # Update metadata
        metadata["content_ids"] = valid_content_ids
        sources["metadata"] = metadata
        
        # Update the trend
        update_result = supabase.table("trends").update({
            "sources": sources
        }).eq("id", trend_id).execute()
        
        if update_result.data:
            updated_count += 1
            logger.info(f"✓ Updated trend {trend_id} ({trend_info['topic']}): removed {trend_info['orphaned_count']} orphaned refs")
    
    return updated_count


async def main(fix: bool = False):
    """Main execution function"""
    logger.info("=" * 80)
    logger.info("ORPHANED CONTENT REFERENCE CHECK")
    logger.info("=" * 80)
    
    # Fetch data
    logger.info("Fetching trends...")
    trends = await get_all_trends()
    logger.info(f"Found {len(trends)} trends")
    
    logger.info("Fetching existing content IDs...")
    existing_ids = await get_existing_content_ids()
    logger.info(f"Found {len(existing_ids)} content items in source_content_cache")
    
    # Find orphaned references
    logger.info("\nAnalyzing trends for orphaned content references...")
    orphaned_data = await find_orphaned_references(trends, existing_ids)
    
    # Print results
    logger.info("\n" + "=" * 80)
    logger.info("RESULTS")
    logger.info("=" * 80)
    logger.info(f"Total trends: {orphaned_data['total_trends']}")
    logger.info(f"Total content references: {orphaned_data['total_content_refs']}")
    logger.info(f"Orphaned references: {orphaned_data['total_orphaned_refs']}")
    logger.info(f"Affected trends: {orphaned_data['affected_trends']}")
    
    if orphaned_data['affected_trends'] > 0:
        logger.info("\nAFFECTED TRENDS:")
        logger.info("-" * 80)
        for trend in orphaned_data['orphaned_trends']:
            logger.info(f"\nTrend ID: {trend['trend_id']}")
            logger.info(f"  Topic: {trend['topic']}")
            logger.info(f"  User ID: {trend['user_id']}")
            logger.info(f"  Detected: {trend['detected_at']}")
            logger.info(f"  Total content refs: {trend['total_content_ids']}")
            logger.info(f"  Orphaned refs: {trend['orphaned_count']}")
            logger.info(f"  Orphaned IDs: {', '.join(trend['orphaned_content_ids'][:3])}{'...' if len(trend['orphaned_content_ids']) > 3 else ''}")
    
    # Clean up if requested
    if fix and orphaned_data['affected_trends'] > 0:
        logger.info("\n" + "=" * 80)
        logger.info("CLEANING UP ORPHANED REFERENCES")
        logger.info("=" * 80)
        updated_count = await clean_orphaned_references(orphaned_data, existing_ids)
        logger.info(f"\n✓ Updated {updated_count} trends")
    elif orphaned_data['affected_trends'] > 0:
        logger.info("\n" + "=" * 80)
        logger.info("DRY RUN - No changes made")
        logger.info("Run with --fix flag to clean up orphaned references")
        logger.info("=" * 80)
    else:
        logger.info("\n✓ No orphaned references found!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check for orphaned content references in trends")
    parser.add_argument("--fix", action="store_true", help="Actually fix orphaned references (default: dry-run)")
    args = parser.parse_args()
    
    asyncio.run(main(fix=args.fix))
