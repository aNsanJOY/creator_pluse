"""
Centralized LLM Wrapper Service
Manages all LLM API calls with proper logging and usage tracking
"""

import logging
import time
from typing import List, Dict, Any, Optional
from groq import Groq

from app.core.config import settings
from app.services.llm_usage_tracker import llm_usage_tracker

logger = logging.getLogger(__name__)


class LLMWrapper:
    """Centralized wrapper for all LLM API calls with logging and tracking"""
    
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.default_model = "meta-llama/llama-4-scout-17b-16e-instruct"
        #"openai/gpt-oss-20b"
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        user_id: str,
        service_name: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a chat completion call with automatic logging
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            user_id: User ID for tracking
            service_name: Name of the calling service (e.g., 'draft_generator')
            model: Model to use (defaults to default_model)
            temperature: Temperature parameter (0-1)
            max_tokens: Maximum tokens to generate
            metadata: Additional metadata to log
        
        Returns:
            Dictionary with 'response' (API response) and 'usage' (usage stats)
        """
        model = model or self.default_model
        
        logger.info(f"[LLM_WRAPPER] {service_name} - Making LLM call with model={model}, temp={temperature}, max_tokens={max_tokens}")
        
        try:
            # Track start time
            start_time = time.time()
            
            # Make API call
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                #max_tokens=max_tokens
            )
            
            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Extract usage information
            tokens_used = response.usage.total_tokens if response.usage else 0
            prompt_tokens = response.usage.prompt_tokens if response.usage else 0
            completion_tokens = response.usage.completion_tokens if response.usage else 0
            
            logger.info(
                f"[LLM_WRAPPER] {service_name} - Call successful: "
                f"tokens={tokens_used} (prompt={prompt_tokens}, completion={completion_tokens}), "
                f"duration={duration_ms}ms"
            )
            
            # Log usage to database
            if user_id:
                try:
                    log_metadata = {
                        "service": service_name,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        **(metadata or {})
                    }
                    
                    await llm_usage_tracker.log_llm_call(
                        user_id=user_id,
                        model=model,
                        endpoint="/v1/chat/completions",
                        status_code=200,
                        tokens_used=tokens_used,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        duration_ms=duration_ms,
                        metadata=log_metadata
                    )
                    
                    logger.info(f"[LLM_WRAPPER] {service_name} - Usage logged successfully")
                    
                except Exception as log_error:
                    logger.error(
                        f"[LLM_WRAPPER] {service_name} - Failed to log usage: {log_error}",
                        exc_info=True
                    )
            
            return {
                "response": response,
                "usage": {
                    "total_tokens": tokens_used,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "duration_ms": duration_ms
                }
            }
            
        except Exception as e:
            logger.error(
                f"[LLM_WRAPPER] {service_name} - API call failed: {str(e)}",
                exc_info=True
            )
            
            # Log error to database
            if user_id:
                try:
                    log_metadata = {
                        "service": service_name,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        "error": str(e),
                        **(metadata or {})
                    }
                    
                    await llm_usage_tracker.log_llm_call(
                        user_id=user_id,
                        model=model,
                        endpoint="/v1/chat/completions",
                        status_code=500,
                        tokens_used=0,
                        prompt_tokens=0,
                        completion_tokens=0,
                        duration_ms=0,
                        error_message=str(e),
                        metadata=log_metadata
                    )
                except Exception as log_error:
                    logger.error(
                        f"[LLM_WRAPPER] {service_name} - Failed to log error: {log_error}"
                    )
            
            raise


# Global instance
llm_wrapper = LLMWrapper()
