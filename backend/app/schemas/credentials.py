"""
Credential schemas for different source types.
Defines what credentials each source type accepts.
"""

from pydantic import BaseModel
from typing import Optional, Dict, List
from enum import Enum


class CredentialFieldType(str, Enum):
    """Types of credential fields"""
    TEXT = "text"
    PASSWORD = "password"
    API_KEY = "api_key"
    OAUTH_TOKEN = "oauth_token"


class CredentialField(BaseModel):
    """Definition of a credential field"""
    name: str
    label: str
    type: CredentialFieldType
    required: bool = True
    placeholder: Optional[str] = None
    help_text: Optional[str] = None


class SourceCredentialSchema(BaseModel):
    """Schema defining credentials for a source type"""
    source_type: str
    fields: List[CredentialField]
    supports_global: bool = False  # Whether global credentials are available
    oauth_url: Optional[str] = None  # OAuth flow URL if applicable


# Define credential schemas for each source type
CREDENTIAL_SCHEMAS = {
    "rss": SourceCredentialSchema(
        source_type="rss",
        fields=[],
        supports_global=False
    ),
    
    "youtube": SourceCredentialSchema(
        source_type="youtube",
        fields=[
            CredentialField(
                name="api_key",
                label="YouTube API Key",
                type=CredentialFieldType.API_KEY,
                required=True,
                placeholder="AIzaSy...",
                help_text="Required: Get your API key from Google Cloud Console (https://console.cloud.google.com/)"
            )
        ],
        supports_global=False
    ),
    
    "twitter": SourceCredentialSchema(
        source_type="twitter",
        fields=[
            CredentialField(
                name="bearer_token",
                label="Bearer Token (OAuth 2.0)",
                type=CredentialFieldType.API_KEY,
                required=False,
                placeholder="Your Twitter Bearer Token",
                help_text="Option 1: Provide Bearer Token for read-only access (easier setup)"
            ),
            CredentialField(
                name="api_key",
                label="API Key (Consumer Key)",
                type=CredentialFieldType.API_KEY,
                required=False,
                placeholder="Your Twitter API Key",
                help_text="Option 2: OAuth 1.0a - Provide all 4 fields (api_key, api_secret, access_token, access_token_secret)"
            ),
            CredentialField(
                name="api_secret",
                label="API Secret (Consumer Secret)",
                type=CredentialFieldType.PASSWORD,
                required=False,
                placeholder="Your Twitter API Secret",
                help_text="Option 2: OAuth 1.0a - Get from Twitter Developer Portal (https://developer.twitter.com/)"
            ),
            CredentialField(
                name="access_token",
                label="Access Token",
                type=CredentialFieldType.OAUTH_TOKEN,
                required=False,
                placeholder="Your Access Token",
                help_text="Option 2: OAuth 1.0a - Get from Twitter Developer Portal"
            ),
            CredentialField(
                name="access_token_secret",
                label="Access Token Secret",
                type=CredentialFieldType.PASSWORD,
                required=False,
                placeholder="Your Access Token Secret",
                help_text="Option 2: OAuth 1.0a - Get from Twitter Developer Portal"
            )
        ],
        supports_global=False,
        oauth_url="/api/twitter/oauth"
    ),
    
    "substack": SourceCredentialSchema(
        source_type="substack",
        fields=[],
        supports_global=False
    ),
    
    "medium": SourceCredentialSchema(
        source_type="medium",
        fields=[],
        supports_global=False
    ),
    
    "linkedin": SourceCredentialSchema(
        source_type="linkedin",
        fields=[
            CredentialField(
                name="access_token",
                label="LinkedIn Access Token",
                type=CredentialFieldType.OAUTH_TOKEN,
                required=True,
                placeholder="OAuth 2.0 Access Token",
                help_text="Required: Get this from LinkedIn OAuth flow"
            ),
            CredentialField(
                name="refresh_token",
                label="Refresh Token",
                type=CredentialFieldType.OAUTH_TOKEN,
                required=False,
                placeholder="OAuth 2.0 Refresh Token",
                help_text="Optional: For automatic token refresh"
            )
        ],
        supports_global=False,
        oauth_url="/api/linkedin/oauth"
    ),
    
    "github": SourceCredentialSchema(
        source_type="github",
        fields=[
            CredentialField(
                name="github_token",
                label="GitHub Personal Access Token",
                type=CredentialFieldType.API_KEY,
                required=True,
                placeholder="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                help_text="Required: Get from https://github.com/settings/tokens (provides 5,000 req/hour)"
            )
        ],
        supports_global=False
    ),
    
    "reddit": SourceCredentialSchema(
        source_type="reddit",
        fields=[
            CredentialField(
                name="reddit_client_id",
                label="Reddit Client ID",
                type=CredentialFieldType.API_KEY,
                required=True,
                placeholder="Your Reddit app client ID",
                help_text="Required: Create app at https://www.reddit.com/prefs/apps"
            ),
            CredentialField(
                name="reddit_client_secret",
                label="Reddit Client Secret",
                type=CredentialFieldType.PASSWORD,
                required=True,
                placeholder="Your Reddit app client secret",
                help_text="Required: Get from your Reddit app settings"
            ),
            CredentialField(
                name="reddit_user_agent",
                label="User Agent",
                type=CredentialFieldType.TEXT,
                required=False,
                placeholder="CreatorPulse/1.0",
                help_text="Optional: Custom user agent string"
            )
        ],
        supports_global=False
    )
}


def get_credential_schema(source_type: str) -> Optional[SourceCredentialSchema]:
    """Get credential schema for a source type"""
    return CREDENTIAL_SCHEMAS.get(source_type.lower())


def get_all_credential_schemas() -> Dict[str, SourceCredentialSchema]:
    """Get all credential schemas"""
    return CREDENTIAL_SCHEMAS
