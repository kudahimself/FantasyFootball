#!/usr/bin/env python
"""
Test the current squad API endpoint to see what data is being returned
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')

# Setup Django
django.setup()

from django.test import RequestFactory
from MyApp.views import get_current_squad
import json

def test_current_squad_api():
    """Test the current squad API endpoint"""
    try:
        # Create a request
        factory = RequestFactory()
        request = factory.get('/api/current_squad/')
        
        # Call the view
        response = get_current_squad(request)
        
        # Check response
        if response.status_code == 200:
            print("✅ API call successful")
            
            # Parse JSON response
            data = json.loads(response.content.decode('utf-8'))
            print("Response structure:")
            print(json.dumps(data, indent=2))
            
            # Check if players have required fields
            current_squad = data.get('current_squad', {})
            total_players = 0
            players_with_data = 0
            
            for position, players in current_squad.items():
                for player in players:
                    total_players += 1
                    if isinstance(player, dict) and 'elo' in player and 'cost' in player:
                        players_with_data += 1
                        print(f"✅ {player['name']}: Elo={player['elo']}, Cost={player['cost']}")
                    else:
                        print(f"❌ {player}: Missing elo/cost data")
            
            print(f"\nSummary: {players_with_data}/{total_players} players have complete data")
            
        else:
            print(f"❌ API call failed with status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_current_squad_api()