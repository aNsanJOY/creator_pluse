"""
LLM API Usage Tracking Service
Tracks LLM API calls for usage monitoring and rate limiting
Supports multiple providers (Groq, OpenAI, Anthropic, etc.)
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from supabase import Client
from app.core.database import get_supabase

logger = logging.getLogger(__name__)


class LLMUsageTracker:
    """Tracks LLM API usage and enforces rate limits"""
    
    def __init__(self):
        self.supabase: Optional[Client] = None
    
    def initialize(self):
        """Initialize database connection"""
        if not self.supabase:
            self.supabase = get_supabase()
    
    async def log_llm_call(
        self,
        user_id: str,
        model: str,
        endpoint: str = "/v1/chat/completions",
        status_code: int = 200,
        tokens_used: int = 0,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        duration_ms: int = 0,
        error_message: str = None,
        metadata: Dict[str, Any] = None
    ):
        """
        Log an LLM API call to the database
        
        Args:
            user_id: User making the call
            model: LLM model used (e.g., llama-3.1-70b-versatile, gpt-4, claude-3, etc.)
            endpoint: API endpoint (default: /v1/chat/completions)
            status_code: Response status code
            tokens_used: Total tokens consumed
            prompt_tokens: Input/prompt tokens
            completion_tokens: Output/completion tokens
            duration_ms: Request duration in milliseconds
            error_message: Error message if failed
            metadata: Additional metadata (temperature, max_tokens, provider, etc.)
        """
        try:
            self.initialize()
            
            logger.info(f"[LLM_USAGE] Logging call for user {user_id}: model={model}, tokens={tokens_used}, prompt={prompt_tokens}, completion={completion_tokens}")
            
            # Insert log
            log_data = {
                "user_id": user_id,
                "model": model,
                "endpoint": endpoint,
                "status_code": status_code,
                "tokens_used": tokens_used,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "duration_ms": duration_ms,
                "error_message": error_message,
                "metadata": metadata or {}
            }
            
            logger.info(f"[LLM_USAGE] Inserting log data: {log_data}")
            result = self.supabase.table("llm_usage_logs").insert(log_data).execute()
            
            if result.data:
                logger.info(f"[LLM_USAGE] ✓ Log inserted successfully with ID: {result.data[0].get('id')}")
            else:
                logger.warning(f"[LLM_USAGE] ⚠ Log insert returned no data")
            
            # Update rate limit counter
            logger.info(f"[LLM_USAGE] Updating rate limits for user {user_id}")
            await self._update_rate_limit(user_id)
            logger.info(f"[LLM_USAGE] ✓ Rate limits updated successfully")
            
        except Exception as e:
            logger.error(f"[LLM_USAGE] ✗ ERROR logging LLM usage: {str(e)}", exc_info=True)
            # Don't re-raise - logging failures shouldn't break the main operation
    
    async def _update_rate_limit(self, user_id: str):
        """Update rate limit counters for all limit types"""
        try:
            self.initialize()
            
            # Ensure rate limits exist for all types
            limit_types = ["minute", "day"]
            
            for limit_type in limit_types:
                logger.info(f"[RATE_LIMIT] Updating {limit_type} limit for user {user_id}")
                
                # Get or create rate limit
                result = self.supabase.table("llm_rate_limits").select("*").eq(
                    "user_id", user_id
                ).eq("limit_type", limit_type).execute()
                
                now = datetime.now(timezone.utc)
                
                if not result.data:
                    logger.info(f"[RATE_LIMIT] No {limit_type} limit found, creating new one")
                    # Create new rate limit
                    await self._create_user_rate_limit(user_id, limit_type)
                    # Set count to 1 for this call
                    update_result = self.supabase.table("llm_rate_limits").update({
                        "current_count": 1
                    }).eq("user_id", user_id).eq("limit_type", limit_type).execute()
                    logger.info(f"[RATE_LIMIT] ✓ Created {limit_type} limit with count=1")
                else:
                    limit = result.data[0]
                    reset_at = datetime.fromisoformat(limit["reset_at"].replace("Z", "+00:00"))
                    current_count = limit["current_count"]
                    
                    logger.info(f"[RATE_LIMIT] Current {limit_type}: count={current_count}, reset_at={reset_at}")
                    
                    # Check if reset time has passed
                    if now >= reset_at:
                        # Reset counter and set new reset time
                        new_reset_at = self._calculate_next_reset(limit_type)
                        update_result = self.supabase.table("llm_rate_limits").update({
                            "current_count": 1,
                            "reset_at": new_reset_at.isoformat()
                        }).eq("id", limit["id"]).execute()
                        logger.info(f"[RATE_LIMIT] ✓ Reset {limit_type} limit: count=1, new_reset={new_reset_at}")
                    else:
                        # Increment counter
                        new_count = current_count + 1
                        update_result = self.supabase.table("llm_rate_limits").update({
                            "current_count": new_count
                        }).eq("id", limit["id"]).execute()
                        logger.info(f"[RATE_LIMIT] ✓ Incremented {limit_type} limit: {current_count} -> {new_count}")
        
        except Exception as e:
            logger.error(f"[RATE_LIMIT] ✗ ERROR updating rate limit: {str(e)}", exc_info=True)
    
    def _calculate_next_reset(self, limit_type: str) -> datetime:
        """Calculate next reset time based on limit type"""
        now = datetime.now(timezone.utc)
        
        if limit_type == "minute":
            # Reset at the start of the next minute
            next_minute = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
            return next_minute
        elif limit_type == "hour":
            # Reset at the start of the next hour
            next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
            return next_hour
        elif limit_type == "day":
            # Reset at midnight UTC of the next day
            next_day = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            return next_day
        elif limit_type == "month":
            # Reset at start of next month
            if now.month == 12:
                return datetime(now.year + 1, 1, 1, tzinfo=timezone.utc)
            else:
                return datetime(now.year, now.month + 1, 1, tzinfo=timezone.utc)
        
        # Default to next day at midnight
        return (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    async def check_rate_limit(
        self,
        user_id: str,
        limit_type: str = "minute"
    ) -> Dict[str, Any]:
        """
        Check if user has exceeded LLM rate limit
        
        Returns:
            Dict with can_call, current_count, limit_value, reset_at
        """
        try:
            self.initialize()
            
            result = self.supabase.table("llm_rate_limits").select("*").eq(
                "user_id", user_id
            ).eq("limit_type", limit_type).execute()
            
            if not result.data:
                # Create default rate limit from config
                await self._create_user_rate_limit(user_id, limit_type)
                # Fetch the newly created rate limit
                result = self.supabase.table("llm_rate_limits").select("*").eq(
                    "user_id", user_id
                ).eq("limit_type", limit_type).execute()
                
                if not result.data:
                    # If still no data, return safe defaults
                    return {
                        "can_call": True,
                        "current_count": 0,
                        "limit_value": 1000,  # Safe default instead of 0
                        "reset_at": self._calculate_next_reset(limit_type).isoformat(),
                        "remaining": 1000
                    }
            
            limit = result.data[0]
            now = datetime.now(timezone.utc)
            reset_at = datetime.fromisoformat(limit["reset_at"].replace("Z", "+00:00"))
            
            # Check if reset time has passed
            if now >= reset_at:
                # Reset the counter and update reset time
                new_reset_at = self._calculate_next_reset(limit_type)
                self.supabase.table("llm_rate_limits").update({
                    "current_count": 0,
                    "reset_at": new_reset_at.isoformat()
                }).eq("id", limit["id"]).execute()
                
                can_call = True
                current_count = 0
                reset_at_str = new_reset_at.isoformat()
            else:
                can_call = limit["current_count"] < limit["limit_value"]
                current_count = limit["current_count"]
                reset_at_str = limit["reset_at"]
            
            result_dict = {
                "can_call": can_call,
                "current_count": current_count,
                "limit_value": limit["limit_value"],
                "reset_at": reset_at_str,
                "remaining": max(0, limit["limit_value"] - current_count)
            }
            
            logger.info(f"Rate limit check for user {user_id}, type {limit_type}: {result_dict}")
            return result_dict
        
        except Exception as e:
            logger.error(f"Error checking rate limit: {str(e)}")
            # Return safe defaults instead of 0 to prevent NaN in frontend
            return {
                "can_call": True,
                "current_count": 0,
                "limit_value": 1000,
                "reset_at": self._calculate_next_reset(limit_type).isoformat(),
                "remaining": 1000
            }
    
    async def _create_user_rate_limit(self, user_id: str, limit_type: str):
        """Create user rate limit from default config"""
        try:
            # Get default config
            config = self.supabase.table("llm_rate_limit_configs").select("*").eq(
                "limit_type", limit_type
            ).execute()
            
            if not config.data:
                return
            
            limit_value = config.data[0]["limit_value"]
            reset_at = self._calculate_next_reset(limit_type)
            
            # Create user rate limit
            self.supabase.table("llm_rate_limits").insert({
                "user_id": user_id,
                "limit_type": limit_type,
                "limit_value": limit_value,
                "current_count": 0,
                "reset_at": reset_at.isoformat()
            }).execute()
            
        except Exception as e:
            logger.error(f"Error creating user rate limit: {str(e)}")
    
    async def get_usage_stats(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get LLM usage statistics for a user
        
        Args:
            user_id: User ID
            days: Number of days to look back
        
        Returns:
            Usage statistics
        """
        try:
            self.initialize()
            
            since_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            
            result = self.supabase.table("llm_usage_logs").select("*").eq(
                "user_id", user_id
            ).gte("created_at", since_date).execute()
            
            if not result.data:
                return {
                    "total_calls": 0,
                    "total_tokens": 0,
                    "total_prompt_tokens": 0,
                    "total_completion_tokens": 0,
                    "by_model": {},
                    "by_day": []
                }
            
            logs = result.data
            
            # Calculate totals
            total_calls = len(logs)
            total_tokens = sum(log.get("tokens_used", 0) for log in logs)
            total_prompt_tokens = sum(log.get("prompt_tokens", 0) for log in logs)
            total_completion_tokens = sum(log.get("completion_tokens", 0) for log in logs)
            
            # Group by model
            by_model = {}
            for log in logs:
                model = log.get("model", "unknown")
                if model not in by_model:
                    by_model[model] = {
                        "calls": 0,
                        "tokens": 0,
                        "prompt_tokens": 0,
                        "completion_tokens": 0
                    }
                by_model[model]["calls"] += 1
                by_model[model]["tokens"] += log.get("tokens_used", 0)
                by_model[model]["prompt_tokens"] += log.get("prompt_tokens", 0)
                by_model[model]["completion_tokens"] += log.get("completion_tokens", 0)
            
            # Group by day
            by_day = {}
            for log in logs:
                date = log["created_at"][:10]  # YYYY-MM-DD
                if date not in by_day:
                    by_day[date] = {
                        "calls": 0,
                        "tokens": 0,
                        "prompt_tokens": 0,
                        "completion_tokens": 0
                    }
                by_day[date]["calls"] += 1
                by_day[date]["tokens"] += log.get("tokens_used", 0)
                by_day[date]["prompt_tokens"] += log.get("prompt_tokens", 0)
                by_day[date]["completion_tokens"] += log.get("completion_tokens", 0)
            
            # Convert to list sorted by date
            by_day_list = [
                {"date": date, **stats}
                for date, stats in sorted(by_day.items())
            ]
            
            return {
                "total_calls": total_calls,
                "total_tokens": total_tokens,
                "total_prompt_tokens": total_prompt_tokens,
                "total_completion_tokens": total_completion_tokens,
                "by_model": by_model,
                "by_day": by_day_list
            }
        
        except Exception as e:
            logger.error(f"Error getting usage stats: {str(e)}")
            return {
                "total_calls": 0,
                "total_tokens": 0,
                "total_prompt_tokens": 0,
                "total_completion_tokens": 0,
                "by_model": {},
                "by_day": []
            }


# Global instance
llm_usage_tracker = LLMUsageTracker()
