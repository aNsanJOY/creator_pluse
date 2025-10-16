"""
Base class for source connectors.
This enables a plugin-based architecture for adding new source types.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime


class SourceContent:
    """Represents a piece of content from a source"""
    
    def __init__(
        self,
        title: str,
        content: str,
        url: Optional[str] = None,
        published_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.title = title
        self.content = content
        self.url = url
        self.published_at = published_at
        self.metadata = metadata or {}


class BaseSourceConnector(ABC):
    """
    Abstract base class for all source connectors.
    
    To add a new source type:
    1. Create a new class that inherits from BaseSourceConnector
    2. Implement all abstract methods
    3. Register the connector in the SourceRegistry
    """
    
    def __init__(self, source_id: str, config: Dict[str, Any], credentials: Optional[Dict[str, Any]] = None):
        """
        Initialize the source connector.
        
        Args:
            source_id: Unique identifier for this source instance
            config: Source-specific configuration
            credentials: Source-specific credentials (OAuth tokens, API keys, etc.)
        """
        self.source_id = source_id
        self.config = config
        self.credentials = credentials or {}
    
    @abstractmethod
    async def validate_connection(self) -> bool:
        """
        Validate that the source connection is working.
        
        Returns:
            True if connection is valid, False otherwise
        """
        pass
    
    @abstractmethod
    async def fetch_content(self, since: Optional[datetime] = None) -> List[SourceContent]:
        """
        Fetch content from the source.
        
        Args:
            since: Only fetch content published after this timestamp (delta crawl)
        
        Returns:
            List of SourceContent objects
        """
        pass
    
    @abstractmethod
    def get_source_type(self) -> str:
        """
        Get the source type identifier.
        
        Returns:
            Source type string (e.g., 'twitter', 'youtube', 'rss', 'substack')
        """
        pass
    
    @abstractmethod
    def get_required_credentials(self) -> List[str]:
        """
        Get list of required credential fields for this source type.
        
        Returns:
            List of credential field names
        """
        pass
    
    @abstractmethod
    def get_required_config(self) -> List[str]:
        """
        Get list of required configuration fields for this source type.
        
        Returns:
            List of configuration field names
        """
        pass
    
    async def handle_rate_limit(self, retry_after: Optional[int] = None):
        """
        Handle rate limiting from the source API.
        
        Args:
            retry_after: Number of seconds to wait before retrying
        """
        # Default implementation - can be overridden
        import asyncio
        wait_time = retry_after or 60
        await asyncio.sleep(wait_time)
    
    def transform_content(self, raw_content: Any) -> SourceContent:
        """
        Transform raw content from the source into a SourceContent object.
        Can be overridden for source-specific transformations.
        
        Args:
            raw_content: Raw content from the source API
        
        Returns:
            SourceContent object
        """
        # Default implementation - should be overridden
        return SourceContent(
            title=str(raw_content.get('title', '')),
            content=str(raw_content.get('content', '')),
            url=raw_content.get('url'),
            published_at=raw_content.get('published_at'),
            metadata=raw_content.get('metadata', {})
        )


class SourceRegistry:
    """
    Registry for source connectors.
    Allows dynamic registration and retrieval of source types.
    """
    
    _connectors: Dict[str, type] = {}
    
    @classmethod
    def register(cls, source_type: str, connector_class: type):
        """
        Register a source connector.
        
        Args:
            source_type: Source type identifier (e.g., 'twitter', 'substack')
            connector_class: Connector class that inherits from BaseSourceConnector
        """
        if not issubclass(connector_class, BaseSourceConnector):
            raise ValueError(f"{connector_class} must inherit from BaseSourceConnector")
        
        cls._connectors[source_type.lower()] = connector_class
    
    @classmethod
    def get_connector(cls, source_type: str) -> Optional[type]:
        """
        Get a registered connector class by source type.
        
        Args:
            source_type: Source type identifier
        
        Returns:
            Connector class or None if not found
        """
        return cls._connectors.get(source_type.lower())
    
    @classmethod
    def get_all_source_types(cls) -> List[str]:
        """
        Get all registered source types.
        
        Returns:
            List of source type identifiers
        """
        return list(cls._connectors.keys())
    
    @classmethod
    def is_supported(cls, source_type: str) -> bool:
        """
        Check if a source type is supported.
        
        Args:
            source_type: Source type identifier
        
        Returns:
            True if supported, False otherwise
        """
        return source_type.lower() in cls._connectors
