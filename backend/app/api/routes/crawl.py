from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.core.database import get_supabase
from app.api.dependencies import get_current_active_user
from app.services.crawl_orchestrator import crawl_orchestrator

router = APIRouter()


@router.post("/trigger")
async def trigger_manual_crawl(
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Manually trigger a crawl for all user's sources.
    Useful for testing or immediate content refresh.
    """
    try:
        from datetime import datetime
        
        user_id = current_user["id"]
        
        # Initialize orchestrator
        await crawl_orchestrator.initialize()
        
        # Get user's sources
        sources_result = supabase.table("sources").select("*").eq(
            "user_id", user_id
        ).eq("status", "active").execute()
        
        if not sources_result.data:
            return {
                "message": "No active sources to crawl",
                "sources_crawled": 0
            }
        
        # Mark batch crawl as started
        start_time = datetime.now()
        await crawl_orchestrator._start_batch_crawl(user_id)
        
        # Crawl each source
        results = []
        for source in sources_result.data:
            try:
                result = await crawl_orchestrator._crawl_source(source)
                results.append(result)
            except Exception as e:
                results.append({
                    "source_id": source["id"],
                    "status": "failed",
                    "error": str(e)
                })
        
        # Summary
        successful = sum(1 for r in results if r["status"] in ["success", "partial"])
        failed = sum(1 for r in results if r["status"] == "failed")
        
        # Mark batch crawl as completed
        duration_seconds = int((datetime.now() - start_time).total_seconds())
        await crawl_orchestrator._complete_batch_crawl(user_id, successful, failed, duration_seconds)
        
        return {
            "message": "Manual crawl completed",
            "sources_crawled": len(results),
            "successful": successful,
            "failed": failed,
            "results": results
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger crawl: {str(e)}"
        )


@router.get("/logs")
async def get_crawl_logs(
    limit: int = 50,
    source_id: str = None,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Get crawl logs for the current user.
    Optionally filter by source_id.
    """
    try:
        user_id = current_user["id"]
        
        # Build query
        query = supabase.table("crawl_logs").select("*").eq("user_id", user_id)
        
        if source_id:
            query = query.eq("source_id", source_id)
        
        # Get logs ordered by most recent
        result = query.order("started_at", desc=True).limit(limit).execute()
        
        return {
            "logs": result.data if result.data else [],
            "count": len(result.data) if result.data else 0
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch crawl logs: {str(e)}"
        )


@router.get("/stats")
async def get_crawl_stats(
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Get crawl statistics for the current user.
    """
    try:
        user_id = current_user["id"]
        
        # Get all logs for user
        logs_result = supabase.table("crawl_logs").select("*").eq("user_id", user_id).execute()
        
        logs = logs_result.data if logs_result.data else []
        
        # Calculate stats
        total_crawls = len(logs)
        successful = sum(1 for log in logs if log["status"] == "success")
        failed = sum(1 for log in logs if log["status"] == "failed")
        partial = sum(1 for log in logs if log["status"] == "partial")
        
        total_items_fetched = sum(log.get("items_fetched", 0) for log in logs)
        total_items_new = sum(log.get("items_new", 0) for log in logs)
        
        # Get last crawl time
        last_crawl = None
        if logs:
            last_crawl = max(log["started_at"] for log in logs)
        
        # Average duration
        durations = [log.get("duration_ms", 0) for log in logs if log.get("duration_ms")]
        avg_duration_ms = sum(durations) / len(durations) if durations else 0
        
        return {
            "total_crawls": total_crawls,
            "successful": successful,
            "failed": failed,
            "partial": partial,
            "total_items_fetched": total_items_fetched,
            "total_items_new": total_items_new,
            "last_crawl_at": last_crawl,
            "avg_duration_ms": round(avg_duration_ms, 2),
            "success_rate": round((successful / total_crawls * 100) if total_crawls > 0 else 0, 2)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch crawl stats: {str(e)}"
        )


@router.get("/status")
async def get_crawl_status(
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Get current crawl status for all user's sources and batch crawl schedule.
    """
    try:
        user_id = current_user["id"]
        
        # Get batch crawl schedule
        schedule_result = supabase.table("user_crawl_schedule").select("*").eq(
            "user_id", user_id
        ).execute()
        
        batch_schedule = None
        if schedule_result.data:
            batch_schedule = schedule_result.data[0]
        else:
            # Create default schedule if doesn't exist
            new_schedule = supabase.table("user_crawl_schedule").insert({
                "user_id": user_id,
                "crawl_frequency_hours": 24
            }).execute()
            batch_schedule = new_schedule.data[0] if new_schedule.data else None
        
        # Get all sources
        sources_result = supabase.table("sources").select("*").eq("user_id", user_id).execute()
        
        if not sources_result.data:
            return {
                "sources": [],
                "total": 0,
                "active": 0,
                "error": 0,
                "last_batch_crawl_at": batch_schedule.get("last_batch_crawl_at") if batch_schedule else None,
                "next_scheduled_crawl_at": batch_schedule.get("next_scheduled_crawl_at") if batch_schedule else None,
                "is_crawling": batch_schedule.get("is_crawling", False) if batch_schedule else False,
                "last_crawl_duration_seconds": batch_schedule.get("last_crawl_duration_seconds") if batch_schedule else None,
                "sources_crawled_count": batch_schedule.get("sources_crawled_count", 0) if batch_schedule else 0,
                "sources_failed_count": batch_schedule.get("sources_failed_count", 0) if batch_schedule else 0
            }
        
        sources = []
        for source in sources_result.data:
            # Get latest crawl log for this source
            log_result = supabase.table("crawl_logs").select("*").eq(
                "source_id", source["id"]
            ).order("started_at", desc=True).limit(1).execute()
            
            latest_log = log_result.data[0] if log_result.data else None
            
            sources.append({
                "id": source["id"],
                "name": source["name"],
                "type": source["source_type"],
                "status": source["status"],
                "last_crawled_at": source.get("last_crawled_at"),
                "error_message": source.get("error_message"),
                "latest_crawl": latest_log
            })
        
        return {
            "sources": sources,
            "total": len(sources),
            "active": sum(1 for s in sources if s["status"] == "active"),
            "error": sum(1 for s in sources if s["status"] == "error"),
            "last_batch_crawl_at": batch_schedule.get("last_batch_crawl_at") if batch_schedule else None,
            "next_scheduled_crawl_at": batch_schedule.get("next_scheduled_crawl_at") if batch_schedule else None,
            "is_crawling": batch_schedule.get("is_crawling", False) if batch_schedule else False,
            "last_crawl_duration_seconds": batch_schedule.get("last_crawl_duration_seconds") if batch_schedule else None,
            "sources_crawled_count": batch_schedule.get("sources_crawled_count", 0) if batch_schedule else 0,
            "sources_failed_count": batch_schedule.get("sources_failed_count", 0) if batch_schedule else 0
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch crawl status: {str(e)}"
        )


@router.post("/reactivate/{source_id}")
async def reactivate_source(
    source_id: str,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Reactivate a failed or error source.
    Changes status from 'error' to 'active' and clears error message.
    """
    try:
        user_id = current_user["id"]
        
        # Verify the source exists and belongs to the user
        source_result = supabase.table("sources").select("*").eq(
            "id", source_id
        ).eq("user_id", user_id).execute()
        
        if not source_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Source not found"
            )
        
        source = source_result.data[0]
        
        # Update source status to active and clear error
        update_result = supabase.table("sources").update({
            "status": "active",
            "error_message": None
        }).eq("id", source_id).eq("user_id", user_id).execute()
        
        if not update_result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reactivate source"
            )
        
        return {
            "message": f"Source '{source['name']}' reactivated successfully",
            "source_id": source_id,
            "previous_status": source["status"],
            "new_status": "active"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reactivate source: {str(e)}"
        )


@router.post("/reactivate-all")
async def reactivate_all_failed_sources(
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Reactivate all failed/error sources for the current user.
    Useful for bulk recovery after fixing issues.
    """
    try:
        user_id = current_user["id"]
        
        # Get all error sources
        error_sources_result = supabase.table("sources").select("*").eq(
            "user_id", user_id
        ).eq("status", "error").execute()
        
        if not error_sources_result.data:
            return {
                "message": "No failed sources to reactivate",
                "reactivated_count": 0,
                "sources": []
            }
        
        # Reactivate all error sources
        reactivated = []
        for source in error_sources_result.data:
            try:
                supabase.table("sources").update({
                    "status": "active",
                    "error_message": None
                }).eq("id", source["id"]).eq("user_id", user_id).execute()
                
                reactivated.append({
                    "id": source["id"],
                    "name": source["name"],
                    "type": source["source_type"]
                })
            except Exception as e:
                # Log but continue with other sources
                print(f"Failed to reactivate source {source['id']}: {str(e)}")
        
        return {
            "message": f"Reactivated {len(reactivated)} source(s)",
            "reactivated_count": len(reactivated),
            "sources": reactivated
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reactivate sources: {str(e)}"
        )
