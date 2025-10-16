"""
Test script to diagnose X (Twitter) API credential issues.
Run this to verify your X API setup.

Usage:
    python test_twitter_credentials.py
"""

import sys
import os
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    import tweepy
    print("✅ tweepy library installed")
except ImportError:
    print("❌ tweepy not installed. Run: pip install tweepy")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    print("✅ python-dotenv library installed")
except ImportError:
    print("❌ python-dotenv not installed. Run: pip install python-dotenv")
    sys.exit(1)

# Load environment variables
load_dotenv()

print("\n" + "="*60)
print("X (TWITTER) API CREDENTIALS TEST")
print("="*60 + "\n")

# Check if credentials exist
api_key = os.getenv('TWITTER_API_KEY')
api_secret = os.getenv('TWITTER_API_SECRET')
access_token = os.getenv('TWITTER_ACCESS_TOKEN')
access_secret = os.getenv('TWITTER_ACCESS_SECRET')

print("1. Checking .env file...")
print("-" * 60)

credentials_found = True

if api_key:
    print(f"✅ TWITTER_API_KEY: {api_key[:10]}...{api_key[-4:]} (length: {len(api_key)})")
else:
    print("❌ TWITTER_API_KEY: NOT FOUND")
    credentials_found = False

if api_secret:
    print(f"✅ TWITTER_API_SECRET: {api_secret[:10]}...{api_secret[-4:]} (length: {len(api_secret)})")
else:
    print("❌ TWITTER_API_SECRET: NOT FOUND")
    credentials_found = False

if access_token:
    print(f"✅ TWITTER_ACCESS_TOKEN: {access_token[:10]}...{access_token[-4:]} (length: {len(access_token)})")
else:
    print("❌ TWITTER_ACCESS_TOKEN: NOT FOUND")
    credentials_found = False

if access_secret:
    print(f"✅ TWITTER_ACCESS_SECRET: {access_secret[:10]}...{access_secret[-4:]} (length: {len(access_secret)})")
else:
    print("❌ TWITTER_ACCESS_SECRET: NOT FOUND")
    credentials_found = False

if not credentials_found:
    print("\n" + "="*60)
    print("❌ MISSING CREDENTIALS")
    print("="*60)
    print("\nPlease add the following to your backend/.env file:")
    print("""
TWITTER_API_KEY=your_api_key_here
TWITTER_API_SECRET=your_api_secret_here
TWITTER_ACCESS_TOKEN=your_access_token_here
TWITTER_ACCESS_SECRET=your_access_secret_here
    """)
    print("Get credentials from: https://developer.twitter.com/en/portal/dashboard")
    sys.exit(1)

print("\n2. Testing Twitter API connection...")
print("-" * 60)

try:
    # Create Tweepy client
    print("Creating Tweepy client...")
    client = tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_secret,
        wait_on_rate_limit=True
    )
    print("✅ Client created successfully")
    
    # Test authentication by getting authenticated user
    print("\nTesting authentication (get_me)...")
    me = client.get_me()
    
    if me.data:
        print(f"✅ Authentication successful!")
        print(f"   Authenticated as: @{me.data.username}")
        print(f"   User ID: {me.data.id}")
        print(f"   Name: {me.data.name}")
    else:
        print("❌ Authentication failed: No user data returned")
        sys.exit(1)
    
    # Test fetching tweets
    print("\nTesting tweet fetching (get_users_tweets)...")
    tweets = client.get_users_tweets(
        id=me.data.id,
        max_results=5,
        tweet_fields=["created_at", "public_metrics"]
    )
    
    if tweets and tweets.data:
        print(f"✅ Successfully fetched {len(tweets.data)} tweets")
        print("\nSample tweet:")
        tweet = tweets.data[0]
        print(f"   Text: {tweet.text[:100]}...")
        print(f"   Created: {tweet.created_at}")
        if hasattr(tweet, 'public_metrics'):
            print(f"   Likes: {tweet.public_metrics.get('like_count', 0)}")
    else:
        print("⚠️  No tweets found (this is OK if you haven't tweeted)")
    
    # Test fetching another user's tweets
    print("\nTesting public user fetch (get_user)...")
    test_user = client.get_user(username="twitter")
    if test_user.data:
        print(f"✅ Successfully fetched public user: @{test_user.data.username}")
    else:
        print("❌ Failed to fetch public user")
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)
    print("\nYour Twitter API credentials are working correctly.")
    print("You can now use Twitter sources in CreatorPulse.")
    
except tweepy.Unauthorized as e:
    print(f"\n❌ AUTHENTICATION FAILED (401 Unauthorized)")
    print("="*60)
    print(f"\nError: {e}")
    print("\n🔍 POSSIBLE CAUSES:")
    print("\n1. Invalid API credentials")
    print("   → Regenerate keys in X Developer Portal")
    print("   → https://developer.x.com/en/portal/dashboard")
    print("\n2. Expired or revoked access tokens")
    print("   → Go to 'Keys and tokens' tab")
    print("   → Click 'Regenerate' for Access Token & Secret")
    print("\n3. Insufficient API access level (MOST COMMON)")
    print("   → You need 'Basic' or 'Pro' tier, not just 'Free'")
    print("   → Free tier: Only 500 posts/month read (insufficient)")
    print("   → Basic tier: $200/month (as of Oct 2024, was $100)")
    print("   → Upgrade here: https://developer.x.com/en/portal/products")
    print("   → Access is immediate after payment (paid subscription)")
    print("\n4. App permissions issue")
    print("   → Ensure your app has 'Read' permissions")
    print("   → Settings → App permissions → Edit → Select 'Read'")
    print("   → Regenerate tokens after changing permissions")
    print("\n5. Incorrect authentication method")
    print("   → Some endpoints require OAuth 1.0a User Context")
    print("   → Make sure you're using Access Token & Secret, not just API keys")
    
    print("\n📝 NEXT STEPS:")
    print("1. Check your API access level in X Developer Portal")
    print("2. If it says 'Free', upgrade to 'Basic' ($200/month) or 'Pro' tier")
    print("3. Note: This requires payment - Basic tier is $200/month as of Oct 2024")
    print("4. Regenerate all tokens after upgrading")
    print("5. Update .env file with new tokens")
    print("6. Run this test script again")
    
    sys.exit(1)

except tweepy.Forbidden as e:
    print(f"\n❌ ACCESS FORBIDDEN (403)")
    print("="*60)
    print(f"\nError: {e}")
    print("\n🔍 POSSIBLE CAUSES:")
    print("\n1. Insufficient API access level")
    print("   → Upgrade to Basic ($200/month) or Pro tier")
    print("   → Free tier (500 posts/month) is insufficient for timeline endpoints")
    print("   → https://developer.x.com/en/portal/products")
    print("\n2. App doesn't have required permissions")
    print("   → Check app permissions in X Developer Portal")
    print("   → Ensure 'Read' is enabled")
    print("\n3. Trying to access protected content")
    print("   → Ensure the user account is public")
    
    sys.exit(1)

except tweepy.TooManyRequests as e:
    print(f"\n⚠️  RATE LIMIT EXCEEDED")
    print("="*60)
    print(f"\nError: {e}")
    print("\nYou've hit the Twitter API rate limit.")
    print("Wait 15 minutes and try again.")
    
    sys.exit(1)

except tweepy.TwitterServerError as e:
    print(f"\n❌ TWITTER SERVER ERROR")
    print("="*60)
    print(f"\nError: {e}")
    print("\nX's servers are having issues.")
    print("Check status: https://api.twitterstat.us/")
    print("Try again in a few minutes.")
    
    sys.exit(1)

except Exception as e:
    print(f"\n❌ UNEXPECTED ERROR")
    print("="*60)
    print(f"\nError type: {type(e).__name__}")
    print(f"Error message: {e}")
    print("\nPlease check:")
    print("1. Internet connection")
    print("2. X API status: https://api.twitterstat.us/")
    print("3. Firewall/proxy settings")
    
    import traceback
    print("\nFull traceback:")
    traceback.print_exc()
    
    sys.exit(1)
