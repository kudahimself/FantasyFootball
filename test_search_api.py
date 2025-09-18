#!/usr/bin/env python3
"""
Test script to check if the team selection search functionality is working
"""
import requests
import json

def test_api_endpoint():
    """Test the /api/all-players/ endpoint"""
    try:
        print("Testing /api/all-players/ endpoint...")
        response = requests.get('http://127.0.0.1:8000/api/all-players/')
        
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'Not specified')}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ API Response successful!")
            
            if 'error' in data:
                print(f"❌ API returned error: {data['error']}")
                return False
            
            if 'players' in data:
                players_data = data['players']
                print(f"\n📊 Players data structure:")
                
                total_players = 0
                for position, players in players_data.items():
                    count = len(players) if players else 0
                    total_players += count
                    print(f"  {position}: {count} players")
                    
                    # Show first few players in each position
                    if players and count > 0:
                        print(f"    Sample players:")
                        for i, player in enumerate(players[:3]):
                            print(f"      {i+1}. {player.get('name', 'Unknown')} - £{player.get('cost', 0)}m - ELO: {player.get('elo', 'N/A')}")
                        if count > 3:
                            print(f"      ... and {count-3} more")
                
                print(f"\n🎯 Total players: {total_players}")
                
                # Test sorting by ELO
                all_players = []
                for position, players in players_data.items():
                    for player in players:
                        player['position'] = position
                        all_players.append(player)
                
                # Sort by ELO (highest first)
                sorted_players = sorted(all_players, key=lambda x: x.get('elo', 0), reverse=True)
                
                print(f"\n🏆 Top 10 highest ELO players:")
                for i, player in enumerate(sorted_players[:10]):
                    print(f"  {i+1}. {player.get('name', 'Unknown')} ({player.get('position', 'Unknown')}) - ELO: {player.get('elo', 'N/A')} - £{player.get('cost', 0)}m")
                
                return True
            else:
                print("❌ No 'players' key in response")
                print(f"Response keys: {list(data.keys())}")
                return False
        else:
            print(f"❌ API returned status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - is the Django server running on port 8000?")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_current_squad_api():
    """Test the current squad API"""
    try:
        print("\n" + "="*50)
        print("Testing /api/current_squad/ endpoint...")
        response = requests.get('http://127.0.0.1:8000/api/current_squad/')
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Current squad API working!")
            
            if 'current_squad' in data:
                squad = data['current_squad']
                print(f"\n📋 Current squad:")
                
                total_squad_players = 0
                for position, players in squad.items():
                    count = len(players) if players else 0
                    total_squad_players += count
                    print(f"  {position}: {count} players")
                    
                    if players:
                        for player in players:
                            print(f"    - {player.get('name', 'Unknown')} - £{player.get('cost', 0)}m")
                
                print(f"\n👥 Total squad size: {total_squad_players}")
                return True
            else:
                print("❌ No 'current_squad' in response")
                return False
        else:
            print(f"❌ Current squad API returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing current squad: {e}")
        return False

def test_search_functionality():
    """Test search functionality by simulating JavaScript behavior"""
    try:
        print("\n" + "="*50)
        print("Testing search functionality...")
        
        response = requests.get('http://127.0.0.1:8000/api/all-players/')
        if response.status_code != 200:
            print("❌ Cannot test search - API not working")
            return False
        
        data = response.json()
        if 'players' not in data:
            print("❌ Cannot test search - no players data")
            return False
        
        # Simulate the JavaScript processing
        all_players = []
        for position, players in data['players'].items():
            for player in players:
                all_players.append({**player, 'position': position})
        
        print(f"✅ Processed {len(all_players)} players for search")
        
        # Test search for "Arsenal"
        search_term = "arsenal"
        matches = [p for p in all_players if 
                  search_term in p.get('name', '').lower() or 
                  search_term in p.get('team', '').lower()]
        
        print(f"\n🔍 Search for '{search_term}': {len(matches)} matches")
        for i, player in enumerate(matches[:5]):
            print(f"  {i+1}. {player.get('name')} ({player.get('team')}) - {player.get('position')}")
        
        # Test top ELO players
        sorted_players = sorted(all_players, key=lambda x: x.get('elo', 0), reverse=True)
        top_20 = sorted_players[:20]
        
        print(f"\n⭐ Top 20 ELO players (what should show by default):")
        for i, player in enumerate(top_20):
            print(f"  {i+1}. {player.get('name')} - ELO: {player.get('elo', 'N/A')} - {player.get('position')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing search: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Fantasy Football Search Functionality")
    print("=" * 50)
    
    # Test the APIs
    api_works = test_api_endpoint()
    squad_works = test_current_squad_api()
    search_works = test_search_functionality()
    
    print("\n" + "="*50)
    print("📋 SUMMARY:")
    print(f"All Players API: {'✅ Working' if api_works else '❌ Failed'}")
    print(f"Current Squad API: {'✅ Working' if squad_works else '❌ Failed'}")
    print(f"Search Logic: {'✅ Working' if search_works else '❌ Failed'}")
    
    if api_works and squad_works:
        print("\n🎉 APIs are working! The issue is likely in the JavaScript frontend.")
        print("\n💡 Possible issues:")
        print("   - JavaScript not loading properly")
        print("   - CSRF token issues")
        print("   - DOM elements not found")
        print("   - Event listeners not attached")
    else:
        print("\n⚠️ API issues found - need to fix backend first!")
    
    print("\n🔗 Next steps:")
    print("   1. Check browser console for JavaScript errors")
    print("   2. Verify that elements like 'players-list' exist in HTML")
    print("   3. Test if initializePlayerSelection() is being called")