#!/usr/bin/env python3
"""
Test script to verify the Django API endpoint works with the new utility module.
"""

import requests
import json
import time

def test_recalculate_elos_api():
    """Test the recalculate player elos API endpoint using the new utility module."""
    
    url = "http://localhost:8000/api/recalculate_elos/"
    
    print("🧪 Testing Django API with new utility module...")
    print(f"📡 Calling: {url}")
    
    try:
        # Make POST request to the API
        start_time = time.time()
        response = requests.post(url, timeout=300)  # 5 minute timeout
        end_time = time.time()
        
        print(f"⏱️  Response time: {end_time - start_time:.2f} seconds")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API Response:")
            print(f"   Success: {data.get('success')}")
            print(f"   Message: {data.get('message')}")
            print(f"   Updated Players: {data.get('updated_count')}")
            print(f"   Total Players: {data.get('total_players')}")
            print(f"   Failed Players: {data.get('failed_count')}")
            print(f"   Duration: {data.get('duration')}")
            print(f"   Processing Rate: {data.get('processing_rate')}")
            print(f"   Week: {data.get('week')}")
            print(f"   Method: {data.get('method')}")
            
            if data.get('success'):
                print("\n🎉 Utility module integration successful!")
                return True
            else:
                print(f"\n❌ API returned error: {data.get('error')}")
                return False
        else:
            print(f"❌ HTTP Error {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def verify_server_running():
    """Check if the Django server is running."""
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        return True
    except:
        return False

if __name__ == "__main__":
    print("🚀 Testing Django API with MyApi.utils.elo_calculator module")
    
    # Check if server is running
    if not verify_server_running():
        print("❌ Django server not running on localhost:8000")
        print("Please start the server with: python manage.py runserver 8000")
        exit(1)
    
    print("✅ Django server is running")
    
    # Test the API
    success = test_recalculate_elos_api()
    
    if success:
        print("\n🎯 All tests passed! The utility module is working correctly.")
    else:
        print("\n💥 Tests failed. Check the server logs for details.")