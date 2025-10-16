"""
Source connectors package.
Import all connectors here to register them with SourceRegistry.
"""

from app.services.sources.base import SourceRegistry, BaseSourceConnector, SourceContent
from app.services.sources.rss_connector import RSSConnector

# Conditionally import Twitter connector if tweepy is available
# This prevents startup failures on Python 3.13 where tweepy has compatibility issues
try:
    from app.services.sources.twitter_connector import TwitterConnector
    _twitter_available = True
except (ImportError, ModuleNotFoundError) as e:
    print(f"Warning: Twitter connector not available: {e}")
    TwitterConnector = None
    _twitter_available = False

# Conditionally import YouTube connector if google-api-python-client is available
try:
    from app.services.sources.youtube_connector import YouTubeConnector
    _youtube_available = True
except (ImportError, ModuleNotFoundError) as e:
    print(f"Warning: YouTube connector not available: {e}")
    YouTubeConnector = None
    _youtube_available = False

# Import new custom source connectors
try:
    from app.services.sources.substack_connector import SubstackConnector
    _substack_available = True
except (ImportError, ModuleNotFoundError) as e:
    print(f"Warning: Substack connector not available: {e}")
    SubstackConnector = None
    _substack_available = False

try:
    from app.services.sources.medium_connector import MediumConnector
    _medium_available = True
except (ImportError, ModuleNotFoundError) as e:
    print(f"Warning: Medium connector not available: {e}")
    MediumConnector = None
    _medium_available = False

try:
    from app.services.sources.linkedin_connector import LinkedInConnector
    _linkedin_available = True
except (ImportError, ModuleNotFoundError) as e:
    print(f"Warning: LinkedIn connector not available: {e}")
    LinkedInConnector = None
    _linkedin_available = False

try:
    from app.services.sources.github_connector import GitHubConnector
    _github_available = True
except (ImportError, ModuleNotFoundError) as e:
    print(f"Warning: GitHub connector not available: {e}")
    GitHubConnector = None
    _github_available = False

try:
    from app.services.sources.reddit_connector import RedditConnector
    _reddit_available = True
except (ImportError, ModuleNotFoundError) as e:
    print(f"Warning: Reddit connector not available: {e}")
    RedditConnector = None
    _reddit_available = False

__all__ = [
    "SourceRegistry",
    "BaseSourceConnector",
    "SourceContent",
    "RSSConnector",
]

# Only export connectors if they're available
if _twitter_available:
    __all__.append("TwitterConnector")
if _youtube_available:
    __all__.append("YouTubeConnector")
if _substack_available:
    __all__.append("SubstackConnector")
if _medium_available:
    __all__.append("MediumConnector")
if _linkedin_available:
    __all__.append("LinkedInConnector")
if _github_available:
    __all__.append("GitHubConnector")
if _reddit_available:
    __all__.append("RedditConnector")
