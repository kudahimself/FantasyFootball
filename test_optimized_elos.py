#!/usr/bin/env python3
"""
Test script for the optimized recalculate_player_elos functionality.
This script tests with a limited number of players to avoid long processing times.
"""

import requests
import json

def test_recalculate_elos_limited():
    """Test the recalculate Elo functionality with a limited number of players."""
    
    print("="*60)
    print("TESTING OPTIMIZED RECALCULATE ELO FUNCTIONALITY")
    print("="*60)
    
    # Test with only 10 players for speed
    test_params = {
        'max_players': 10,  # Only process 10 players
        'batch_size': 5     # Process in batches of 5
    }
    
    print(f"Testing with parameters: {test_params}")
    
    try:
        # Make the API request
        response = requests.post(
            'http://127.0.0.1:8000/api/recalculate_elos/',
            headers={'Content-Type': 'application/json'},
            data=json.dumps(test_params)
        )
        
        print(f"\nAPI Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"API Response: {json.dumps(result, indent=2)}")
            
            if result.get('success'):
                print(f"\n✅ SUCCESS!")
                print(f"   Updated: {result.get('updated_count', 0)} players")
                print(f"   Total processed: {result.get('total_players', 0)} players")
                print(f"   Week: {result.get('week', 'Unknown')}")
            else:
                print(f"\n❌ API Error: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"\n❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Connection Error: Make sure Django server is running on http://127.0.0.1:8000")
        return False
    except Exception as e:
        print(f"\n❌ Request Error: {str(e)}")
        return False
    
    return True

def test_recalculate_elos_all():
    """Test with all players (will take a long time)."""
    
    print("\n" + "="*60)
    print("TESTING WITH ALL PLAYERS (THIS WILL TAKE A LONG TIME)")
    print("="*60)
    
    test_params = {
        'batch_size': 50    # Process in batches of 50
        # No max_players limit - will process all
    }
    
    print(f"Testing with parameters: {test_params}")
    print("⚠️  This may take 10+ minutes with 596 players...")
    
    confirm = input("Do you want to proceed? (y/N): ")
    if confirm.lower() != 'y':
        print("Skipped.")
        return True
    
    try:
        # Make the API request
        response = requests.post(
            'http://127.0.0.1:8000/api/recalculate_elos/',
            headers={'Content-Type': 'application/json'},
            data=json.dumps(test_params)
        )
        
        print(f"\nAPI Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"API Response: {json.dumps(result, indent=2)}")
            
            if result.get('success'):
                print(f"\n✅ SUCCESS!")
                print(f"   Updated: {result.get('updated_count', 0)} players")
                print(f"   Total processed: {result.get('total_players', 0)} players")
                print(f"   Week: {result.get('week', 'Unknown')}")
            else:
                print(f"\n❌ API Error: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"\n❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"\n❌ Request Error: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    # First test with limited players
    success = test_recalculate_elos_limited()
    
    if success:
        print("\n" + "="*60)
        print("LIMITED TEST COMPLETED SUCCESSFULLY!")
        print("="*60)
        
        # Ask if user wants to test with all players
        full_test = input("\nDo you want to test with ALL players? This will take a long time (y/N): ")
        if full_test.lower() == 'y':
            test_recalculate_elos_all()
        else:
            print("\nTest completed. Use the optimized function with 'max_players' parameter to control processing time.")
    else:
        print("\n❌ Limited test failed. Check the error messages above.")