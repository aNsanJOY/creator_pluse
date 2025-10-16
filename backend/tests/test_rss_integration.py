"""
Test RSS integration functionality.
This test verifies RSS feed parsing, validation, and content extraction.
"""

import pytest
from app.services.sources.rss_connector import RSSConnector
from app.utils.validators import SourceValidator
from app.models.source import SourceType


# Test RSS feeds (public feeds for testing)
TEST_FEEDS = {
    "rss2": "https://feeds.feedburner.com/TechCrunch/",
    "atom": "https://github.blog/feed/",
    "simple_rss": "http://rss.cnn.com/rss/cnn_topstories.rss"
}


class TestRSSValidation:
    """Test RSS feed validation"""
    
    def test_valid_rss_feed(self):
        """Test validation of a valid RSS feed"""
        is_valid, error = SourceValidator.validate_rss_feed(TEST_FEEDS["rss2"])
        assert is_valid, f"Valid RSS feed should pass validation: {error}"
    
    def test_invalid_url_format(self):
        """Test validation with invalid URL format"""
        is_valid, error = SourceValidator.validate_rss_feed("not-a-url")
        assert not is_valid
        assert "Invalid URL format" in error
    
    def test_non_rss_url(self):
        """Test validation with non-RSS URL"""
        is_valid, error = SourceValidator.validate_rss_feed("https://www.google.com")
        assert not is_valid
    
    def test_source_validator_rss(self):
        """Test source validator for RSS type"""
        is_valid, error = SourceValidator.validate_source(
            SourceType.RSS,
            url=TEST_FEEDS["rss2"]
        )
        assert is_valid, f"RSS source validation failed: {error}"


class TestRSSConnector:
    """Test RSS connector functionality"""
    
    @pytest.mark.asyncio
    async def test_rss_connector_initialization(self):
        """Test RSS connector can be initialized"""
        connector = RSSConnector(
            source_id="test-id",
            config={"feed_url": TEST_FEEDS["rss2"]},
            credentials={}
        )
        assert connector.get_source_type() == "rss"
        assert connector.get_required_credentials() == []
        assert "feed_url" in connector.get_required_config()
    
    @pytest.mark.asyncio
    async def test_validate_connection(self):
        """Test RSS feed connection validation"""
        connector = RSSConnector(
            source_id="test-id",
            config={"feed_url": TEST_FEEDS["rss2"]},
            credentials={}
        )
        is_valid = await connector.validate_connection()
        assert is_valid, "Valid RSS feed should pass connection validation"
    
    @pytest.mark.asyncio
    async def test_fetch_content_rss2(self):
        """Test fetching content from RSS 2.0 feed"""
        connector = RSSConnector(
            source_id="test-id",
            config={"feed_url": TEST_FEEDS["rss2"]},
            credentials={}
        )
        contents = await connector.fetch_content()
        
        assert len(contents) > 0, "Should fetch at least one entry"
        
        # Verify content structure
        first_content = contents[0]
        assert first_content.title, "Content should have a title"
        assert first_content.url, "Content should have a URL"
        assert first_content.content, "Content should have content text"
        assert first_content.metadata, "Content should have metadata"
        
        # Verify metadata
        assert "feed_title" in first_content.metadata
        assert "feed_type" in first_content.metadata
    
    @pytest.mark.asyncio
    async def test_fetch_content_atom(self):
        """Test fetching content from Atom feed"""
        connector = RSSConnector(
            source_id="test-id",
            config={"feed_url": TEST_FEEDS["atom"]},
            credentials={}
        )
        contents = await connector.fetch_content()
        
        assert len(contents) > 0, "Should fetch at least one entry from Atom feed"
        
        # Verify Atom-specific fields are handled
        first_content = contents[0]
        assert first_content.title, "Atom entry should have a title"
        assert first_content.url, "Atom entry should have a URL"
    
    @pytest.mark.asyncio
    async def test_delta_crawl(self):
        """Test delta crawl with 'since' parameter"""
        from datetime import datetime, timedelta
        
        connector = RSSConnector(
            source_id="test-id",
            config={"feed_url": TEST_FEEDS["rss2"]},
            credentials={}
        )
        
        # Fetch all content
        all_contents = await connector.fetch_content()
        
        # Fetch only recent content (last 7 days)
        since = datetime.utcnow() - timedelta(days=7)
        recent_contents = await connector.fetch_content(since=since)
        
        # Recent should be less than or equal to all
        assert len(recent_contents) <= len(all_contents)
    
    @pytest.mark.asyncio
    async def test_invalid_feed_url(self):
        """Test handling of invalid feed URL"""
        connector = RSSConnector(
            source_id="test-id",
            config={"feed_url": "https://invalid-feed-url-that-does-not-exist.com/feed"},
            credentials={}
        )
        
        is_valid = await connector.validate_connection()
        assert not is_valid, "Invalid feed should fail validation"
        
        contents = await connector.fetch_content()
        assert len(contents) == 0, "Invalid feed should return empty list"
    
    @pytest.mark.asyncio
    async def test_missing_feed_url(self):
        """Test handling when feed_url is missing from config"""
        connector = RSSConnector(
            source_id="test-id",
            config={},
            credentials={}
        )
        
        is_valid = await connector.validate_connection()
        assert not is_valid, "Missing feed_url should fail validation"
        
        contents = await connector.fetch_content()
        assert len(contents) == 0, "Missing feed_url should return empty list"


class TestRSSFormats:
    """Test handling of various RSS formats"""
    
    @pytest.mark.asyncio
    async def test_rss_2_0_format(self):
        """Test RSS 2.0 format parsing"""
        connector = RSSConnector(
            source_id="test-id",
            config={"feed_url": TEST_FEEDS["rss2"]},
            credentials={}
        )
        contents = await connector.fetch_content()
        
        assert len(contents) > 0
        # RSS 2.0 should have these fields
        first = contents[0]
        assert first.title
        assert first.content or first.metadata.get('summary')
    
    @pytest.mark.asyncio
    async def test_atom_format(self):
        """Test Atom format parsing"""
        connector = RSSConnector(
            source_id="test-id",
            config={"feed_url": TEST_FEEDS["atom"]},
            credentials={}
        )
        contents = await connector.fetch_content()
        
        assert len(contents) > 0
        # Atom should have these fields
        first = contents[0]
        assert first.title
        assert first.url
    
    @pytest.mark.asyncio
    async def test_metadata_extraction(self):
        """Test metadata extraction from RSS feeds"""
        connector = RSSConnector(
            source_id="test-id",
            config={"feed_url": TEST_FEEDS["rss2"]},
            credentials={}
        )
        contents = await connector.fetch_content()
        
        assert len(contents) > 0
        first = contents[0]
        
        # Check metadata fields
        assert "feed_title" in first.metadata
        assert "feed_type" in first.metadata
        assert "tags" in first.metadata
        assert isinstance(first.metadata["tags"], list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
