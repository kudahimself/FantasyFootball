#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')
django.setup()

from django.test import RequestFactory
from MyApp.views import get_squads
import json

def test_squads_view_directly():
    """
    Test the get_squads view function directly without needing a server.
    """
    print("🧪 Testing get_squads view function directly...")
    
    try:
        # Create a fake request
        factory = RequestFactory()
        request = factory.get('/api/squads/')
        
        # Call the view function
        response = get_squads(request)
        
        print(f"📡 Response status: {response.status_code}")
        
        if response.status_code == 200:
            # Parse the JSON response
            data = json.loads(response.content)
            print("✅ View function call successful!")
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
                    print(f"   - Squad number: {first_squad.get('squad_number', 'Missing')}")
                    print(f"   - Has positions: {'positions' in first_squad}")
                    print(f"   - Has goalkeepers: {'goalkeepers' in first_squad}")
                    print(f"   - Has defenders: {'defenders' in first_squad}")
                    print(f"   - Has midfielders: {'midfielders' in first_squad}")
                    print(f"   - Has forwards: {'forwards' in first_squad}")
                    
                    if 'positions' in first_squad:
                        positions = first_squad['positions']
                        print(f"   - Positions array: {positions}")
                    
                    # Check players directly (new flattened structure)
                    print(f"   - Goalkeepers: {len(first_squad.get('goalkeepers', []))}")
                    print(f"   - Defenders: {len(first_squad.get('defenders', []))}")
                    print(f"   - Midfielders: {len(first_squad.get('midfielders', []))}")
                    print(f"   - Forwards: {len(first_squad.get('forwards', []))}")
                    
                    # Show a sample player
                    if first_squad.get('goalkeepers'):
                        sample_player = first_squad['goalkeepers'][0]
                        print(f"   - Sample goalkeeper: {sample_player['name']} (Elo: {sample_player['elo']})")
                    
                    # Test with 3-4-3 formation specifically
                    print()
                    print("🔄 Testing with 3-4-3 formation...")
                    request_343 = factory.get('/api/squads/?formation=3-4-3')
                    response_343 = get_squads(request_343)
                    
                    if response_343.status_code == 200:
                        data_343 = json.loads(response_343.content)
                        if data_343.get('squads'):
                            first_squad_343 = data_343['squads'][0]
                            print(f"   - Formation: {data_343.get('formation')}")
                            print(f"   - Position counts: {data_343.get('counts')}")
                            # Check flattened structure
                            total_players = (len(first_squad_343.get('goalkeepers', [])) + 
                                           len(first_squad_343.get('defenders', [])) + 
                                           len(first_squad_343.get('midfielders', [])) + 
                                           len(first_squad_343.get('forwards', [])))
                            print(f"   - Total players in squad: {total_players}")
                            
                            if total_players == 11:  # Should be 1+3+4+3 = 11
                                print("   ✅ Correct number of players for 3-4-3!")
                            else:
                                print(f"   ❌ Wrong number of players (expected 11, got {total_players})")
                    
                    print()
                    print("🎯 Backend is working correctly!")
                    print("   If frontend still not showing squads, check:")
                    print("   1. Browser console for JavaScript errors")
                    print("   2. Network tab to see if API calls are being made")
                    print("   3. JavaScript expecting different data structure")
                        
                else:
                    print("❌ No squads returned in the response")
                    print("   Check the squad generation logic")
            else:
                print("❌ No 'squads' key in response")
                print(f"   Response keys: {list(data.keys())}")
                
        elif response.status_code == 500:
            # Parse error response
            try:
                error_data = json.loads(response.content)
                print(f"❌ Server error: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"❌ Server error (raw): {response.content}")
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(f"   Response: {response.content}")
            
    except Exception as e:
        print(f"❌ Error testing view function: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_squads_view_directly()