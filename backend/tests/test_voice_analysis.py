import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from app.services.voice_analyzer import VoiceAnalyzer, DEFAULT_VOICE_PROFILE


class TestVoiceAnalyzer:
    """Test voice analysis service"""
    
    @pytest.fixture
    def analyzer(self):
        """Create voice analyzer instance"""
        with patch('app.services.voice_analyzer.Groq'):
            return VoiceAnalyzer()
    
    @pytest.fixture
    def sample_newsletters(self):
        """Sample newsletter data"""
        return [
            {
                "title": "Weekly Tech Update #1",
                "content": """
                Hey everyone! 👋
                
                This week has been absolutely incredible in the tech world. Let me share some exciting updates with you.
                
                First off, AI continues to blow my mind. The latest models are getting smarter every day, and I can't wait to see where this goes.
                
                Here's what caught my attention:
                - New AI models released
                - Framework updates
                - Cool new tools
                
                What do you think about these developments? Hit reply and let me know!
                
                Until next time,
                Your friendly tech enthusiast
                """
            },
            {
                "title": "Weekly Tech Update #2",
                "content": """
                Hello friends!
                
                Another week, another set of amazing tech news. I'm pumped to share this with you!
                
                The developer community has been on fire lately. So many cool projects launching, so many innovations happening.
                
                My top picks this week:
                1. Open source project X launched
                2. Company Y announced new features
                3. Tool Z got a major update
                
                I'd love to hear your thoughts on these. What's exciting you in tech right now?
                
                Cheers,
                Your tech buddy
                """
            }
        ]
    
    def test_default_profile_no_samples(self, analyzer):
        """Test that default profile is returned when no samples provided"""
        result = analyzer.analyze_voice([])
        
        assert result["source"] == "default"
        assert "message" in result
        assert result["tone"] == DEFAULT_VOICE_PROFILE["tone"]
        assert result["style"] == DEFAULT_VOICE_PROFILE["style"]
    
    def test_create_analysis_prompt(self, analyzer, sample_newsletters):
        """Test prompt creation for voice analysis"""
        prompt = analyzer.create_analysis_prompt(sample_newsletters)
        
        assert "Weekly Tech Update #1" in prompt
        assert "Weekly Tech Update #2" in prompt
        assert "NEWSLETTER SAMPLES:" in prompt
        assert "JSON format" in prompt
        assert "tone" in prompt
        assert "style" in prompt
    
    def test_analyze_voice_with_samples(self, analyzer, sample_newsletters):
        """Test voice analysis with sample newsletters"""
        # Mock Groq API response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '''
        {
            "tone": "friendly and enthusiastic",
            "style": "conversational and engaging",
            "vocabulary_level": "intermediate",
            "sentence_structure": "mix of short and medium sentences",
            "personality_traits": ["enthusiastic", "friendly", "knowledgeable"],
            "writing_patterns": {
                "uses_questions": true,
                "uses_examples": true,
                "uses_lists": true,
                "uses_humor": false,
                "uses_personal_anecdotes": false,
                "uses_data_statistics": false
            },
            "content_preferences": {
                "intro_style": "warm greeting with excitement",
                "conclusion_style": "call to action with friendly sign-off",
                "section_transitions": "natural and conversational"
            },
            "formatting_preferences": {
                "paragraph_length": "short",
                "uses_headings": false,
                "uses_bullet_points": true,
                "uses_emphasis": true,
                "uses_emojis": true
            },
            "unique_characteristics": ["uses emojis", "asks reader questions", "enthusiastic tone"],
            "sample_phrases": ["Hey everyone", "I can't wait", "What do you think"]
        }
        '''
        
        analyzer.client.chat.completions.create = Mock(return_value=mock_response)
        
        result = analyzer.analyze_voice(sample_newsletters)
        
        assert result["source"] == "analyzed"
        assert result["samples_count"] == 2
        assert result["tone"] == "friendly and enthusiastic"
        assert result["style"] == "conversational and engaging"
        assert "personality_traits" in result
        assert "writing_patterns" in result
    
    def test_analyze_voice_few_samples_warning(self, analyzer):
        """Test that warning is included when fewer than 3 samples"""
        single_sample = [{
            "title": "Test",
            "content": "This is a test newsletter with some content to analyze."
        }]
        
        # Mock Groq API response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"tone": "test", "style": "test"}'
        
        analyzer.client.chat.completions.create = Mock(return_value=mock_response)
        
        result = analyzer.analyze_voice(single_sample)
        
        assert "warning" in result
        assert "1 sample(s) provided" in result["warning"]
    
    def test_analyze_voice_api_error(self, analyzer, sample_newsletters):
        """Test fallback to default profile on API error"""
        # Mock API error
        analyzer.client.chat.completions.create = Mock(side_effect=Exception("API Error"))
        
        result = analyzer.analyze_voice(sample_newsletters)
        
        assert result["source"] == "default_error"
        assert "error" in result
        assert result["tone"] == DEFAULT_VOICE_PROFILE["tone"]
    
    def test_generate_style_summary_default(self, analyzer):
        """Test summary generation for default profile"""
        profile = {**DEFAULT_VOICE_PROFILE, "source": "default"}
        
        summary = analyzer.generate_style_summary(profile)
        
        assert "default" in summary.lower()
        assert "upload" in summary.lower()
    
    def test_generate_style_summary_analyzed(self, analyzer):
        """Test summary generation for analyzed profile"""
        profile = {
            "tone": "friendly and enthusiastic",
            "style": "conversational",
            "personality_traits": ["enthusiastic", "friendly", "knowledgeable"],
            "samples_count": 3,
            "source": "analyzed"
        }
        
        summary = analyzer.generate_style_summary(profile)
        
        assert "friendly and enthusiastic" in summary
        assert "conversational" in summary
        assert "3 sample(s)" in summary


class TestVoiceAnalysisAPI:
    """Test voice analysis API endpoints"""
    
    def test_analyze_voice_endpoint_no_samples(self):
        """Test voice analysis with no samples returns default profile"""
        # This would be an integration test with actual API
        # For now, we're testing the logic
        pass
    
    def test_analyze_voice_endpoint_with_samples(self):
        """Test voice analysis with samples"""
        # Integration test placeholder
        pass
    
    def test_get_voice_profile_endpoint(self):
        """Test getting voice profile"""
        # Integration test placeholder
        pass
    
    def test_delete_voice_profile_endpoint(self):
        """Test deleting voice profile"""
        # Integration test placeholder
        pass
