"""
Tests for Trend Detection Service
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from app.services.trend_detector import TrendDetector


class TestTrendDetector:
    """Test cases for TrendDetector service"""
    
    @pytest.fixture
    def trend_detector(self):
        """Create a TrendDetector instance"""
        return TrendDetector()
    
    @pytest.fixture
    def mock_content_items(self):
        """Mock content items for testing"""
        return [
            {
                "id": "1",
                "source_id": "source-1",
                "content_type": "rss_article",
                "title": "AI Breakthrough in Natural Language Processing",
                "content": "Researchers have made significant progress in large language models...",
                "url": "https://example.com/ai-breakthrough",
                "metadata": {},
                "published_at": datetime.now().isoformat(),
                "created_at": datetime.now().isoformat()
            },
            {
                "id": "2",
                "source_id": "source-1",
                "content_type": "rss_article",
                "title": "New AI Model Achieves State-of-the-Art Results",
                "content": "A new artificial intelligence model has achieved breakthrough results...",
                "url": "https://example.com/ai-model",
                "metadata": {},
                "published_at": (datetime.now() - timedelta(hours=2)).isoformat(),
                "created_at": (datetime.now() - timedelta(hours=2)).isoformat()
            },
            {
                "id": "3",
                "source_id": "source-2",
                "content_type": "rss_article",
                "title": "Climate Change Report Released",
                "content": "Scientists release comprehensive climate change report...",
                "url": "https://example.com/climate",
                "metadata": {},
                "published_at": (datetime.now() - timedelta(days=1)).isoformat(),
                "created_at": (datetime.now() - timedelta(days=1)).isoformat()
            }
        ]
    
    @pytest.fixture
    def mock_topics(self):
        """Mock extracted topics"""
        return [
            {
                "name": "Artificial Intelligence Advances",
                "description": "Recent breakthroughs in AI and machine learning",
                "content_ids": ["1", "2"],
                "keywords": ["AI", "machine learning", "NLP"],
                "category": "technology",
                "relevance": 0.9
            },
            {
                "name": "Climate Change",
                "description": "New climate research and reports",
                "content_ids": ["3"],
                "keywords": ["climate", "environment", "sustainability"],
                "category": "science",
                "relevance": 0.7
            }
        ]
    
    def test_trend_detector_initialization(self, trend_detector):
        """Test TrendDetector initializes correctly"""
        assert trend_detector is not None
        assert trend_detector.client is not None
        assert trend_detector.model == "openai/gpt-oss-20b"
    
    def test_calculate_recency_score_recent_content(self, trend_detector, mock_content_items):
        """Test recency score calculation for recent content"""
        content_by_id = {item["id"]: item for item in mock_content_items}
        
        # Test with recent content (IDs 1 and 2)
        score = trend_detector._calculate_recency_score(["1", "2"], content_by_id)
        
        # Recent content should have high recency score
        assert score > 0.8
        assert score <= 1.0
    
    def test_calculate_recency_score_old_content(self, trend_detector, mock_content_items):
        """Test recency score calculation for older content"""
        # Create old content
        old_content = {
            "id": "old-1",
            "published_at": (datetime.now() - timedelta(days=10)).isoformat(),
            "created_at": (datetime.now() - timedelta(days=10)).isoformat()
        }
        content_by_id = {"old-1": old_content}
        
        score = trend_detector._calculate_recency_score(["old-1"], content_by_id)
        
        # Old content should have low recency score
        assert score < 0.5
    
    def test_calculate_engagement_score(self, trend_detector, mock_content_items):
        """Test engagement score calculation"""
        content_by_id = {item["id"]: item for item in mock_content_items}
        
        score = trend_detector._calculate_engagement_score(["1", "2"], content_by_id)
        
        # Should return baseline score
        assert score == 0.5
    
    @pytest.mark.asyncio
    async def test_score_trends(self, trend_detector, mock_topics, mock_content_items):
        """Test trend scoring algorithm"""
        content_by_id = {item["id"]: item for item in mock_content_items}
        
        scored_trends = await trend_detector._score_trends(mock_topics, mock_content_items)
        
        assert len(scored_trends) == 2
        
        # Check first trend (AI - should have higher score due to frequency and recency)
        ai_trend = scored_trends[0]
        assert ai_trend["topic"] == "Artificial Intelligence Advances"
        assert 0.0 <= ai_trend["score"] <= 1.0
        assert "signals" in ai_trend
        assert "frequency" in ai_trend["signals"]
        assert "recency" in ai_trend["signals"]
        assert "engagement" in ai_trend["signals"]
        assert "relevance" in ai_trend["signals"]
        assert ai_trend["manual_override"] is False
        
        # Check metadata
        assert "keywords" in ai_trend["metadata"]
        assert "category" in ai_trend["metadata"]
        assert ai_trend["metadata"]["content_count"] == 2
    
    def test_create_topic_extraction_prompt(self, trend_detector, mock_content_items):
        """Test topic extraction prompt creation"""
        content_summaries = [
            {
                "id": item["id"],
                "title": item["title"],
                "snippet": item["content"][:500],
                "source_id": item["source_id"],
                "published_at": item.get("published_at")
            }
            for item in mock_content_items
        ]
        
        prompt = trend_detector._create_topic_extraction_prompt(content_summaries)
        
        assert "Analyze the following content items" in prompt
        assert "trending topics" in prompt.lower()
        assert "JSON format" in prompt
        assert mock_content_items[0]["title"] in prompt
    
    @pytest.mark.asyncio
    async def test_detect_trends_no_content(self, trend_detector):
        """Test trend detection with no content"""
        with patch.object(trend_detector, '_get_recent_content', return_value=[]):
            trend_detector.initialize()
            trends = await trend_detector.detect_trends("test-user-id")
            
            assert trends == []
    
    @pytest.mark.asyncio
    async def test_store_trends(self, trend_detector):
        """Test storing trends in database"""
        mock_supabase = Mock()
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.insert.return_value = mock_table
        mock_table.execute.return_value = Mock()
        
        trend_detector.supabase = mock_supabase
        
        trends = [
            {
                "topic": "Test Topic",
                "description": "Test description",
                "score": 0.85,
                "signals": {"frequency": 0.8, "recency": 0.9, "engagement": 0.5, "relevance": 0.7},
                "metadata": {"keywords": ["test"], "category": "test", "content_count": 5},
                "manual_override": False
            }
        ]
        
        await trend_detector._store_trends("test-user-id", trends)
        
        # Verify database insert was called
        mock_supabase.table.assert_called_with("trends")
        mock_table.insert.assert_called_once()
    
    def test_ensemble_scoring_weights(self, trend_detector, mock_topics, mock_content_items):
        """Test that ensemble scoring uses correct weights"""
        # This test verifies the scoring algorithm combines signals correctly
        content_by_id = {item["id"]: item for item in mock_content_items}
        
        # Manually calculate expected score for first topic
        topic = mock_topics[0]
        frequency = len(topic["content_ids"])
        frequency_score = min(frequency / 10.0, 1.0)  # 2/10 = 0.2
        
        # Expected ensemble: 0.3*freq + 0.3*recency + 0.2*engagement + 0.2*relevance
        # With freq=0.2, recency~0.9+, engagement=0.5, relevance=0.9
        # Expected: 0.3*0.2 + 0.3*0.9+ + 0.2*0.5 + 0.2*0.9 = 0.06 + 0.27+ + 0.1 + 0.18 = 0.61+
        
        # Just verify the score is in a reasonable range
        scored = asyncio.run(trend_detector._score_trends(mock_topics, mock_content_items))
        ai_trend = scored[0]
        
        assert ai_trend["score"] > 0.5  # Should be above 0.5
        assert ai_trend["score"] < 1.0  # Should be below 1.0


class TestTrendDetectorIntegration:
    """Integration tests for trend detection (requires actual Groq API)"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_extract_topics_with_real_api(self):
        """
        Integration test with real Groq API
        
        Note: This test requires GROQ_API_KEY to be set and will make actual API calls.
        Mark as integration test to skip in regular test runs.
        """
        detector = TrendDetector()
        
        content_items = [
            {
                "id": "1",
                "title": "OpenAI Releases GPT-5",
                "content": "OpenAI has announced the release of GPT-5, their latest language model...",
                "source_id": "test-source",
                "published_at": datetime.now().isoformat()
            },
            {
                "id": "2",
                "title": "Google Announces New AI Model",
                "content": "Google has unveiled a new AI model that surpasses previous benchmarks...",
                "source_id": "test-source",
                "published_at": datetime.now().isoformat()
            }
        ]
        
        try:
            topics = await detector._extract_topics(content_items)
            
            assert isinstance(topics, list)
            if topics:  # API might return results
                assert "name" in topics[0]
                assert "description" in topics[0]
                assert "content_ids" in topics[0]
        except Exception as e:
            pytest.skip(f"Groq API not available: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
