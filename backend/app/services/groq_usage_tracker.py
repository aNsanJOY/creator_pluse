"""
Groq API Usage Tracking Service
Tracks Groq API calls for LLM usage monitoring and rate limiting
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from supabase import Client
from app.core.database import get_supabase

logger = logging.getLogger(__name__)


class GroqUsageTracker:
    """Tracks Groq API usage and enforces rate limits"""
    
    def __init__(self):
        self.supabase: Optional[Client] = None
    
    def initialize(self):
        """Initialize database connection"""
        if not self.supabase:
            self.supabase = get_supabase()
    
    async def log_groq_call(
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
        Log a Groq API call to the database
        
        Args:
            user_id: User making the call
            model: Groq model used (e.g., llama-3.1-70b-versatile)
            endpoint: API endpoint (default: /v1/chat/completions)
            status_code: Response status code
            tokens_used: Total tokens consumed
            prompt_tokens: Input/prompt tokens
            completion_tokens: Output/completion tokens
            duration_ms: Request duration in milliseconds
            error_message: Error message if failed
            metadata: Additional metadata (temperature, max_tokens, etc.)
        """
        try:
            self.initialize()
            
            # Insert log
            self.supabase.table("groq_usage_logs").insert({
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
            }).execute()
            
            # Update rate limit counter
            await self._update_rate_limit(user_id)
            
        except Exception as e:
            logger.error(f"Error logging Groq usage: {str(e)}")
    
    async def _update_rate_limit(self, user_id: str):
        """Update rate limit counters"""
        try:
            self.initialize()
            
            # Get current rate limits
            result = self.supabase.table("groq_rate_limits").select("*").eq(
                "user_id", user_id
            ).execute()
            
            if not result.data:
                return
            
            now = datetime.now()
            
            for limit in result.data:
                reset_at = datetime.fromisoformat(limit["reset_at"].replace("Z", "+00:00"))
                
                # Check if reset time has passed
                if now >= reset_at:
                    # Reset counter
                    new_reset_at = self._calculate_next_reset(limit["limit_type"])
                    self.supabase.table("groq_rate_limits").update({
                        "current_count": 1,
                        "reset_at": new_reset_at.isoformat()
                    }).eq("id", limit["id"]).execute()
                else:
                    # Increment counter
                    self.supabase.table("groq_rate_limits").update({
                        "current_count": limit["current_count"] + 1
                    }).eq("id", limit["id"]).execute()
        
        except Exception as e:
            logger.error(f"Error updating rate limit: {str(e)}")
    
    def _calculate_next_reset(self, limit_type: str) -> datetime:
        """Calculate next reset time based on limit type"""
        now = datetime.now()
        
        if limit_type == "minute":
            return now + timedelta(minutes=1)
        elif limit_type == "hour":
            return now + timedelta(hours=1)
        elif limit_type == "day":
            return now + timedelta(days=1)
        elif limit_type == "month":
            # Reset at start of next month
            if now.month == 12:
                return datetime(now.year + 1, 1, 1)
            else:
                return datetime(now.year, now.month + 1, 1)
        
        return now + timedelta(days=1)  # Default to daily
    
    async def check_rate_limit(
        self,
        user_id: str,
        limit_type: str = "minute"
    ) -> Dict[str, Any]:
        """
        Check if user has exceeded Groq rate limit
        
        Returns:
            Dict with can_call, current_count, limit_value, reset_at
        """
        try:
            self.initialize()
            
            result = self.supabase.table("groq_rate_limits").select("*").eq(
                "user_id", user_id
            ).eq("limit_type", limit_type).execute()
            
            if not result.data:
                # Create default rate limit from config
                await self._create_user_rate_limit(user_id, limit_type)
                return {
                    "can_call": True,
                    "current_count": 0,
                    "limit_value": 0,
                    "reset_at": None,
                    "remaining": 0
                }
            
            limit = result.data[0]
            now = datetime.now()
            reset_at = datetime.fromisoformat(limit["reset_at"].replace("Z", "+00:00"))
            
            # Check if reset time has passed
            if now >= reset_at:
                can_call = True
                current_count = 0
            else:
                can_call = limit["current_count"] < limit["limit_value"]
                current_count = limit["current_count"]
            
            return {
                "can_call": can_call,
                "current_count": current_count,
                "limit_value": limit["limit_value"],
                "reset_at": limit["reset_at"],
                "remaining": max(0, limit["limit_value"] - current_count)
            }
        
        except Exception as e:
            logger.error(f"Error checking rate limit: {str(e)}")
            return {
                "can_call": True,
                "current_count": 0,
                "limit_value": 0,
                "reset_at": None,
                "remaining": 0
            }
    
    async def _create_user_rate_limit(self, user_id: str, limit_type: str):
        """Create user rate limit from default config"""
        try:
            # Get default config
            config = self.supabase.table("groq_rate_limit_configs").select("*").eq(
                "limit_type", limit_type
            ).execute()
            
            if not config.data:
                return
            
            limit_value = config.data[0]["limit_value"]
            reset_at = self._calculate_next_reset(limit_type)
            
            # Create user rate limit
            self.supabase.table("groq_rate_limits").insert({
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
        Get Groq usage statistics for a user
        
        Args:
            user_id: User ID
            days: Number of days to look back
        
        Returns:
            Usage statistics
        """
        try:
            self.initialize()
            
            since_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            result = self.supabase.table("groq_usage_logs").select("*").eq(
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
groq_usage_tracker = GroqUsageTracker()
