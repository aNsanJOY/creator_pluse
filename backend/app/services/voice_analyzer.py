"""
Voice Analysis Service using Groq LLM
Analyzes newsletter samples to extract writing style and create voice profiles
"""

from typing import List, Dict, Any, Optional
from groq import Groq
from app.core.config import settings
from app.services.llm_usage_tracker import llm_usage_tracker
import time

# Default voice profile when no samples are available
DEFAULT_VOICE_PROFILE = {
    "tone": "professional yet approachable",
    "style": "informative and engaging",
    "vocabulary_level": "intermediate",
    "sentence_structure": "mix of short and medium sentences",
    "personality_traits": ["friendly", "knowledgeable", "enthusiastic"],
    "writing_patterns": {
        "uses_questions": True,
        "uses_examples": True,
        "uses_lists": True,
        "uses_humor": False
    },
    "content_preferences": {
        "intro_style": "warm greeting with context",
        "conclusion_style": "call to action or thought-provoking question",
        "section_transitions": "smooth and natural"
    },
    "formatting_preferences": {
        "paragraph_length": "medium (3-5 sentences)",
        "uses_headings": True,
        "uses_bullet_points": True,
        "uses_emphasis": True
    }
}


class VoiceAnalyzer:
    """Analyzes writing samples to extract voice and style characteristics"""
    
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = "openai/gpt-oss-20b"  # Using Mixtral for better analysis
    
    def create_analysis_prompt(self, samples: List[Dict[str, str]]) -> str:
        """
        Create a prompt for analyzing writing style from newsletter samples
        
        Args:
            samples: List of newsletter samples with 'title' and 'content'
        
        Returns:
            Formatted prompt for Groq
        """
        samples_text = "\n\n---SAMPLE SEPARATOR---\n\n".join([
            f"Title: {sample.get('title', 'Untitled')}\n\nContent:\n{sample['content']}"
            for sample in samples
        ])
        
        prompt = f"""You are an expert writing style analyst. Analyze the following newsletter samples and extract the author's unique writing voice and style characteristics.

NEWSLETTER SAMPLES:
{samples_text}

Please analyze these samples and provide a detailed voice profile in JSON format with the following structure:

{{
  "tone": "describe the overall tone (e.g., professional, casual, friendly, authoritative)",
  "style": "describe the writing style (e.g., conversational, formal, storytelling)",
  "vocabulary_level": "beginner/intermediate/advanced",
  "sentence_structure": "describe typical sentence patterns",
  "personality_traits": ["list", "of", "personality", "traits"],
  "writing_patterns": {{
    "uses_questions": true/false,
    "uses_examples": true/false,
    "uses_lists": true/false,
    "uses_humor": true/false,
    "uses_personal_anecdotes": true/false,
    "uses_data_statistics": true/false
  }},
  "content_preferences": {{
    "intro_style": "how they typically start newsletters",
    "conclusion_style": "how they typically end newsletters",
    "section_transitions": "how they transition between topics"
  }},
  "formatting_preferences": {{
    "paragraph_length": "short/medium/long",
    "uses_headings": true/false,
    "uses_bullet_points": true/false,
    "uses_emphasis": true/false,
    "uses_emojis": true/false
  }},
  "unique_characteristics": ["list", "of", "unique", "writing", "traits"],
  "sample_phrases": ["example", "phrases", "they", "commonly", "use"]
}}

Provide ONLY the JSON object, no additional text or explanation."""

        return prompt
    
    async def analyze_voice(self, samples: List[Dict[str, str]], user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze writing samples to extract voice profile
        
        Args:
            samples: List of newsletter samples with 'title' and 'content'
            user_id: User ID for usage tracking (optional)
        
        Returns:
            Voice profile dictionary
        """
        # If no samples, return default profile
        if not samples:
            return {
                **DEFAULT_VOICE_PROFILE,
                "source": "default",
                "message": "Using default voice profile. Upload newsletter samples for personalized analysis."
            }
        
        # If very few samples, warn but still analyze
        if len(samples) < 3:
            warning = f"Only {len(samples)} sample(s) provided. For best results, upload 3-5 samples."
        else:
            warning = None
        
        try:
            # Create analysis prompt
            prompt = self.create_analysis_prompt(samples)
            
            # Track API call timing
            start_time = time.time()
            
            # Call Groq API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert writing style analyst. Provide detailed, accurate analysis in valid JSON format only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for more consistent analysis
                max_tokens=2000
            )
            
            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Log usage if user_id provided
            if user_id:
                try:
                    await llm_usage_tracker.log_llm_call(
                        user_id=user_id,
                        model=self.model,
                        endpoint="/v1/chat/completions",
                        status_code=200,
                        tokens_used=response.usage.total_tokens if response.usage else 0,
                        prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
                        completion_tokens=response.usage.completion_tokens if response.usage else 0,
                        duration_ms=duration_ms,
                        metadata={"service": "voice_analyzer", "samples_count": len(samples)}
                    )
                except Exception as log_error:
                    # Don't fail the request if logging fails
                    import logging
                    import traceback
                    logging.error(f"Failed to log LLM usage: {log_error}")
                    logging.error(traceback.format_exc())
            
            # Extract and parse response
            analysis_text = response.choices[0].message.content.strip()
            
            # Try to extract JSON from response
            import json
            import re
            
            # Find JSON object in response
            json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
            if json_match:
                voice_profile = json.loads(json_match.group())
            else:
                # Fallback to default if parsing fails
                voice_profile = DEFAULT_VOICE_PROFILE.copy()
                voice_profile["source"] = "default_fallback"
                voice_profile["message"] = "Analysis failed, using default profile"
                return voice_profile
            
            # Add metadata
            voice_profile["source"] = "analyzed"
            voice_profile["samples_count"] = len(samples)
            voice_profile["model_used"] = self.model
            
            if warning:
                voice_profile["warning"] = warning
            
            return voice_profile
            
        except Exception as e:
            # On error, return default profile with error message
            return {
                **DEFAULT_VOICE_PROFILE,
                "source": "default_error",
                "error": str(e),
                "message": "Analysis failed, using default voice profile"
            }
    
    def generate_style_summary(self, voice_profile: Dict[str, Any]) -> str:
        """
        Generate a human-readable summary of the voice profile
        
        Args:
            voice_profile: Voice profile dictionary
        
        Returns:
            Human-readable summary string
        """
        if voice_profile.get("source") == "default":
            return "Using default voice profile. Upload newsletter samples for personalized analysis."
        
        tone = voice_profile.get("tone", "professional")
        style = voice_profile.get("style", "informative")
        traits = ", ".join(voice_profile.get("personality_traits", [])[:3])
        
        summary = f"Your writing voice is {tone} with a {style} style. "
        summary += f"Key personality traits: {traits}. "
        
        if voice_profile.get("samples_count"):
            summary += f"Analyzed from {voice_profile['samples_count']} sample(s)."
        
        return summary


# Singleton instance
voice_analyzer = VoiceAnalyzer()
