"""
Quick test script for Source Management API endpoints
Run this after starting the FastAPI server to verify Phase 3.1 implementation
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_sources_api():
    """Test the sources API endpoints"""
    
    print("=" * 60)
    print("Testing Source Management API - Phase 3.1")
    print("=" * 60)
    
    # Step 1: Health check
    print("\n1. Testing health check...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    # Step 2: Create a test user (signup)
    print("\n2. Creating test user...")
    signup_data = {
        "email": "test_sources@example.com",
        "password": "TestPassword123!",
        "full_name": "Test User"
    }
    response = requests.post(f"{BASE_URL}/api/auth/signup", json=signup_data)
    
    if response.status_code == 201:
        token_data = response.json()
        token = token_data["access_token"]
        print(f"   ✓ User created successfully")
        print(f"   Token: {token[:20]}...")
    elif response.status_code == 400 and "already registered" in response.text:
        # User exists, try login
        print("   User already exists, logging in...")
        login_data = {
            "email": signup_data["email"],
            "password": signup_data["password"]
        }
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        token_data = response.json()
        token = token_data["access_token"]
        print(f"   ✓ Logged in successfully")
    else:
        print(f"   ✗ Failed: {response.status_code} - {response.text}")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 3: Get all sources (should be empty initially)
    print("\n3. Getting all sources...")
    response = requests.get(f"{BASE_URL}/api/sources", headers=headers)
    print(f"   Status: {response.status_code}")
    sources = response.json()
    print(f"   Sources count: {len(sources)}")
    
    # Step 4: Create an RSS source
    print("\n4. Creating RSS source...")
    rss_source = {
        "source_type": "rss",
        "name": "TechCrunch",
        "url": "https://techcrunch.com/feed/",
        "config": {"polling_frequency": "daily"}
    }
    response = requests.post(f"{BASE_URL}/api/sources", json=rss_source, headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 201:
        created_source = response.json()
        source_id = created_source["id"]
        print(f"   ✓ RSS source created: {created_source['name']}")
        print(f"   Source ID: {source_id}")
    else:
        print(f"   ✗ Failed: {response.text}")
        return
    
    # Step 5: Create a YouTube source
    print("\n5. Creating YouTube source...")
    youtube_source = {
        "source_type": "youtube",
        "name": "Fireship",
        "url": "https://www.youtube.com/@Fireship",
        "config": {}
    }
    response = requests.post(f"{BASE_URL}/api/sources", json=youtube_source, headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 201:
        yt_source = response.json()
        print(f"   ✓ YouTube source created: {yt_source['name']}")
    else:
        print(f"   Response: {response.text}")
    
    # Step 6: Get all sources again
    print("\n6. Getting all sources again...")
    response = requests.get(f"{BASE_URL}/api/sources", headers=headers)
    sources = response.json()
    print(f"   Status: {response.status_code}")
    print(f"   Sources count: {len(sources)}")
    for src in sources:
        print(f"   - {src['name']} ({src['source_type']}) - Status: {src['status']}")
    
    # Step 7: Get specific source
    print(f"\n7. Getting source by ID: {source_id}...")
    response = requests.get(f"{BASE_URL}/api/sources/{source_id}", headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        source = response.json()
        print(f"   ✓ Source: {source['name']}")
        print(f"   URL: {source['url']}")
        print(f"   Status: {source['status']}")
    
    # Step 8: Check source status
    print(f"\n8. Checking source status...")
    response = requests.get(f"{BASE_URL}/api/sources/{source_id}/status", headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        status_info = response.json()
        print(f"   ✓ Source status: {status_info['status']}")
        print(f"   Is healthy: {status_info['is_healthy']}")
    
    # Step 9: Update source
    print(f"\n9. Updating source...")
    update_data = {
        "name": "TechCrunch (Updated)",
        "config": {"polling_frequency": "hourly"}
    }
    response = requests.put(f"{BASE_URL}/api/sources/{source_id}", json=update_data, headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        updated_source = response.json()
        print(f"   ✓ Source updated: {updated_source['name']}")
    
    # Step 10: Test validation - invalid RSS feed
    print("\n10. Testing validation with invalid RSS feed...")
    invalid_source = {
        "source_type": "rss",
        "name": "Invalid Feed",
        "url": "https://example.com/not-a-feed"
    }
    response = requests.post(f"{BASE_URL}/api/sources", json=invalid_source, headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 400:
        print(f"   ✓ Validation working: {response.json()['detail']}")
    
    # Step 11: Delete source
    print(f"\n11. Deleting source...")
    response = requests.delete(f"{BASE_URL}/api/sources/{source_id}", headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 204:
        print(f"   ✓ Source deleted successfully")
    
    # Step 12: Verify deletion
    print(f"\n12. Verifying deletion...")
    response = requests.get(f"{BASE_URL}/api/sources/{source_id}", headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 404:
        print(f"   ✓ Source not found (as expected)")
    
    print("\n" + "=" * 60)
    print("✓ All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_sources_api()
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Could not connect to the API server.")
        print("Make sure the FastAPI server is running on http://localhost:8000")
        print("Run: cd backend && python -m uvicorn app.main:app --reload")
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
