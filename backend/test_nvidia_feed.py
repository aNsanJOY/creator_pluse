"""Test script to debug Nvidia RSS feed validation"""
import feedparser

url = "https://blogs.nvidia.com/blog/category/ai/feed/"

print(f"Testing RSS feed: {url}\n")

feed = feedparser.parse(url)

print(f"Bozo flag: {feed.bozo}")
if feed.bozo:
    print(f"Bozo exception: {feed.bozo_exception if hasattr(feed, 'bozo_exception') else 'None'}")

print(f"\nFeed version: {feed.version if hasattr(feed, 'version') else 'Unknown'}")
print(f"Has entries: {hasattr(feed, 'entries')}")
print(f"Entry count: {len(feed.entries) if hasattr(feed, 'entries') else 0}")

if hasattr(feed, 'feed'):
    print(f"\nFeed title: {feed.feed.get('title', 'N/A')}")
    print(f"Feed description: {feed.feed.get('description', 'N/A')[:100]}")

if hasattr(feed, 'entries') and len(feed.entries) > 0:
    print(f"\nFirst entry:")
    entry = feed.entries[0]
    print(f"  Title: {entry.get('title', 'N/A')}")
    print(f"  Link: {entry.get('link', 'N/A')}")
