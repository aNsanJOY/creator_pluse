"""
GitHub API connector for CreatorPulse.
Fetches repository updates, releases, issues, and discussions.
Uses PyGithub library for GitHub API v3.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from app.services.sources.base import BaseSourceConnector, SourceContent
from app.core.config import settings

try:
    from github import Github, GithubException, RateLimitExceededException
    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False
    print("Warning: PyGithub not installed. Install with: pip install PyGithub")


class GitHubConnector(BaseSourceConnector):
    """
    GitHub connector using PyGithub library.
    
    GitHub API is free with rate limits:
    - Unauthenticated: 60 requests/hour
    - Authenticated: 5,000 requests/hour
    
    Supported fetch types:
    - releases: Repository releases
    - commits: Recent commits
    - issues: Repository issues
    - pull_requests: Pull requests
    - discussions: Repository discussions (if enabled)
    """
    
    def __init__(self, source_id: str, config: Dict[str, Any], credentials: Optional[Dict[str, Any]] = None):
        super().__init__(source_id, config, credentials)
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize GitHub client with user-provided credentials only."""
        if not GITHUB_AVAILABLE:
            print("PyGithub library not available")
            return
        
        try:
            # Get user-specific credentials only
            github_token = None
            if self.credentials:
                github_token = self.credentials.get("github_token")
            
            if github_token:
                print("Initializing GitHub client with authentication token")
                self.client = Github(github_token)
            else:
                print("Error: No GitHub token provided. Please provide a token when adding the source.")
                self.client = None
                
        except Exception as e:
            print(f"Error initializing GitHub client: {e}")
            self.client = None
    
    def get_source_type(self) -> str:
        """Return source type identifier."""
        return "github"
    
    def get_required_credentials(self) -> List[str]:
        """
        GitHub requires user-provided credentials:
        - github_token: GitHub personal access token (required)
        """
        return ["github_token"]
    
    def get_required_config(self) -> List[str]:
        """
        Required config:
        - repository: GitHub repository in format 'owner/repo' (e.g., 'angular/angular')
        - fetch_type: 'releases', 'commits', 'issues', 'pull_requests', or 'discussions'
        - max_results: Maximum items to fetch (default: 10, max: 100)
        """
        return ["repository", "fetch_type"]
    
    async def validate_connection(self) -> bool:
        """Validate GitHub API connection."""
        if not self.client:
            print("GitHub client not initialized")
            return False
        
        try:
            # Test connection by getting rate limit
            rate_limit = self.client.get_rate_limit()
            remaining = rate_limit.core.remaining
            limit = rate_limit.core.limit
            
            print(f"GitHub connection validated. Rate limit: {remaining}/{limit} requests remaining")
            
            # Also validate the repository exists
            repository = self.config.get("repository")
            if repository:
                repo = self.client.get_repo(repository)
                print(f"Repository '{repository}' validated: {repo.full_name}")
            
            return True
            
        except GithubException as e:
            print(f"GitHub connection validation failed: {e.status} - {e.data.get('message', str(e))}")
            if e.status == 401:
                print("Invalid GitHub token. Please check your credentials.")
            elif e.status == 404:
                print(f"Repository '{repository}' not found or not accessible.")
            return False
        except Exception as e:
            print(f"GitHub connection validation failed: {e}")
            return False
    
    async def fetch_content(self, since: Optional[datetime] = None) -> List[SourceContent]:
        """
        Fetch content from GitHub repository.
        
        Args:
            since: Only fetch content after this timestamp (delta crawl)
        
        Returns:
            List of SourceContent objects
        """
        if not self.client:
            raise ValueError("GitHub client not initialized")
        
        repository = self.config.get("repository")
        fetch_type = self.config.get("fetch_type", "releases")
        max_results = min(self.config.get("max_results", 10), 100)
        
        if not repository:
            raise ValueError("Repository is required in config (format: 'owner/repo')")
        
        contents = []
        
        try:
            repo = self.client.get_repo(repository)
            
            # Calculate since date for delta crawl (ensure timezone-aware)
            if since:
                # Ensure since is timezone-aware
                since_date = since if since.tzinfo else since.replace(tzinfo=timezone.utc)
            else:
                since_date = datetime.now(timezone.utc) - timedelta(days=30)
            
            # Fetch based on type
            if fetch_type == "releases":
                contents = await self._fetch_releases(repo, since_date, max_results)
            elif fetch_type == "commits":
                contents = await self._fetch_commits(repo, since_date, max_results)
            elif fetch_type == "issues":
                contents = await self._fetch_issues(repo, since_date, max_results)
            elif fetch_type == "pull_requests":
                contents = await self._fetch_pull_requests(repo, since_date, max_results)
            elif fetch_type == "discussions":
                contents = await self._fetch_discussions(repo, since_date, max_results)
            else:
                raise ValueError(f"Unsupported fetch_type: {fetch_type}")
            
            return contents
            
        except RateLimitExceededException as e:
            print(f"GitHub rate limit exceeded: {e}")
            rate_limit = self.client.get_rate_limit()
            reset_time = rate_limit.core.reset
            wait_seconds = (reset_time - datetime.now(timezone.utc)).total_seconds()
            print(f"Rate limit resets in {wait_seconds:.0f} seconds")
            await self.handle_rate_limit(retry_after=int(wait_seconds))
            return []
        except GithubException as e:
            error_msg = f"GitHub API error ({e.status}): {e.data.get('message', str(e))}"
            print(error_msg)
            if e.status == 401:
                raise ValueError("GitHub authentication failed. Please check your token.")
            elif e.status == 404:
                raise ValueError(f"Repository '{repository}' not found.")
            elif e.status == 403:
                raise ValueError("GitHub access forbidden. You may have hit rate limits or need authentication.")
            raise ValueError(error_msg)
        except Exception as e:
            print(f"Error fetching GitHub content: {e}")
            raise
    
    async def _fetch_releases(self, repo, since: datetime, max_results: int) -> List[SourceContent]:
        """Fetch repository releases."""
        contents = []
        
        try:
            releases = repo.get_releases()
            count = 0
            checked = 0
            
            for release in releases:
                checked += 1
                if checked > 1000:  # Safety limit to prevent infinite loops
                    break
                    
                if count >= max_results:
                    break
                
                # Filter by date - if too old, stop checking (releases are sorted by date)
                if release.created_at and release.created_at < since:
                    break
                
                content = SourceContent(
                    title=f"Release: {release.title or release.tag_name}",
                    content=release.body or f"New release {release.tag_name}",
                    url=release.html_url,
                    published_at=release.created_at,
                    metadata={
                        "type": "release",
                        "repository": repo.full_name,
                        "tag_name": release.tag_name,
                        "author": release.author.login if release.author else None,
                        "prerelease": release.prerelease,
                        "draft": release.draft,
                        "assets_count": len(release.get_assets().get_page(0)) if release.get_assets() else 0
                    }
                )
                contents.append(content)
                count += 1
                
        except Exception as e:
            print(f"Error fetching releases: {e}")
        
        return contents
    
    async def _fetch_commits(self, repo, since: datetime, max_results: int) -> List[SourceContent]:
        """Fetch recent commits."""
        contents = []
        
        try:
            commits = repo.get_commits(since=since)
            count = 0
            
            for commit in commits:
                if count >= max_results:
                    break
                
                commit_data = commit.commit
                
                content = SourceContent(
                    title=f"Commit: {commit_data.message.split('\n')[0][:100]}",
                    content=commit_data.message,
                    url=commit.html_url,
                    published_at=commit_data.author.date,
                    metadata={
                        "type": "commit",
                        "repository": repo.full_name,
                        "sha": commit.sha,
                        "author": commit_data.author.name,
                        "author_email": commit_data.author.email,
                        "stats": {
                            "additions": commit.stats.additions if commit.stats else 0,
                            "deletions": commit.stats.deletions if commit.stats else 0,
                            "total": commit.stats.total if commit.stats else 0
                        }
                    }
                )
                contents.append(content)
                count += 1
                
        except Exception as e:
            print(f"Error fetching commits: {e}")
        
        return contents
    
    async def _fetch_issues(self, repo, since: datetime, max_results: int) -> List[SourceContent]:
        """Fetch repository issues."""
        contents = []
        
        try:
            issues = repo.get_issues(state="all", since=since, sort="created", direction="desc")
            count = 0
            checked = 0
            
            for issue in issues:
                checked += 1
                if checked > 1000:  # Safety limit to prevent infinite loops
                    break
                    
                if count >= max_results:
                    break
                
                # Skip pull requests (they appear in issues API)
                if issue.pull_request:
                    continue
                
                content = SourceContent(
                    title=f"Issue #{issue.number}: {issue.title}",
                    content=issue.body or "No description provided",
                    url=issue.html_url,
                    published_at=issue.created_at,
                    metadata={
                        "type": "issue",
                        "repository": repo.full_name,
                        "number": issue.number,
                        "state": issue.state,
                        "author": issue.user.login if issue.user else None,
                        "labels": [label.name for label in issue.labels],
                        "comments": issue.comments,
                        "reactions": {
                            "+1": issue.get_reactions().totalCount if hasattr(issue, 'get_reactions') else 0
                        }
                    }
                )
                contents.append(content)
                count += 1
                
        except Exception as e:
            print(f"Error fetching issues: {e}")
        
        return contents
    
    async def _fetch_pull_requests(self, repo, since: datetime, max_results: int) -> List[SourceContent]:
        """Fetch pull requests."""
        contents = []
        
        try:
            pulls = repo.get_pulls(state="all", sort="created", direction="desc")
            count = 0
            checked = 0
            
            for pr in pulls:
                checked += 1
                if checked > 1000:  # Safety limit to prevent infinite loops
                    break
                    
                if count >= max_results:
                    break
                
                # Filter by date - if too old, stop checking (PRs are sorted by created date desc)
                if pr.created_at < since:
                    break
                
                content = SourceContent(
                    title=f"PR #{pr.number}: {pr.title}",
                    content=pr.body or "No description provided",
                    url=pr.html_url,
                    published_at=pr.created_at,
                    metadata={
                        "type": "pull_request",
                        "repository": repo.full_name,
                        "number": pr.number,
                        "state": pr.state,
                        "author": pr.user.login if pr.user else None,
                        "merged": pr.merged,
                        "mergeable": pr.mergeable,
                        "labels": [label.name for label in pr.labels],
                        "comments": pr.comments,
                        "commits": pr.commits,
                        "additions": pr.additions,
                        "deletions": pr.deletions
                    }
                )
                contents.append(content)
                count += 1
                
        except Exception as e:
            print(f"Error fetching pull requests: {e}")
        
        return contents
    
    async def _fetch_discussions(self, repo, since: datetime, max_results: int) -> List[SourceContent]:
        """Fetch repository discussions (requires GraphQL API)."""
        # Note: Discussions require GraphQL API which is more complex
        # For now, return empty list with a note
        print("Note: GitHub Discussions fetching requires GraphQL API implementation")
        print("Consider using issues or releases instead")
        return []
    
    async def handle_rate_limit(self, retry_after: Optional[int] = None):
        """
        Handle GitHub rate limiting.
        GitHub has rate limits:
        - Unauthenticated: 60 requests/hour
        - Authenticated: 5,000 requests/hour
        """
        import asyncio
        wait_time = retry_after or 3600  # Default to 1 hour
        print(f"Rate limit exceeded. Waiting {wait_time} seconds...")
        await asyncio.sleep(wait_time)


# Register the connector
from app.services.sources.base import SourceRegistry
SourceRegistry.register("github", GitHubConnector)
