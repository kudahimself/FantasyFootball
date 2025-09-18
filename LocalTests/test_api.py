#!/usr/bin/env python
import requests
import json

def test_squads_api():
    """
    Test the squads API endpoint to see what's being returned.
    """
    print("🧪 Testing squads API endpoint...")
    
    try:
        # Test the API endpoint
        url = "http://localhost:8000/api/squads/"
        response = requests.get(url, timeout=10)
        
        print(f"📡 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API call successful!")
            print()
            
            # Check if squads are returned
            if 'squads' in data:
                squads = data['squads']
                print(f"📊 Number of squads returned: {len(squads)}")
                
                if len(squads) > 0:
                    print("✅ Squads are being generated!")
                    
                    # Check first squad structure
                    first_squad = squads[0]
                    print(f"🔍 First squad structure:")
                    print(f"   - Has squad_number: {'squad_number' in first_squad}")
                    print(f"   - Has positions: {'positions' in first_squad}")
                    print(f"   - Has players: {'players' in first_squad}")
                    
                    if 'players' in first_squad:
                        players = first_squad['players']
                        print(f"   - Goalkeepers: {len(players.get('goalkeepers', []))}")
                        print(f"   - Defenders: {len(players.get('defenders', []))}")
                        print(f"   - Midfielders: {len(players.get('midfielders', []))}")
                        print(f"   - Forwards: {len(players.get('forwards', []))}")
                        
                        # Show a sample player
                        if players.get('goalkeepers'):
                            sample_player = players['goalkeepers'][0]
                            print(f"   - Sample goalkeeper: {sample_player}")
                    
                    print()
                    print("🎯 This suggests the backend is working correctly.")
                    print("   If the frontend isn't showing squads, the issue is likely:")
                    print("   1. JavaScript console errors")
                    print("   2. Frontend not calling the API")
                    print("   3. Frontend expecting different data structure")
                        
                else:
                    print("❌ No squads returned in the response")
                    print("   Check the backend squad generation logic")
            else:
                print("❌ No 'squads' key in response")
                print(f"   Response data: {data}")
                
            # Check formation and counts
            if 'formation' in data:
                print(f"📐 Formation: {data['formation']}")
            if 'counts' in data:
                print(f"🔢 Position counts: {data['counts']}")
                
        else:
            print(f"❌ API call failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the server")
        print("   Make sure Django server is running on localhost:8000")
    except Exception as e:
        print(f"❌ Error testing API: {e}")

if __name__ == "__main__":
    test_squads_api()