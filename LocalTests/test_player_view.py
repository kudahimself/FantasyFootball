#!/usr/bin/env python
"""
Test the player_info view to see if team information is being passed correctly
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
from MyApp.views import player_info
from MyApi.models import PlayerMatch, Player

def test_player_info_view():
    """Test the player_info view with a real player"""
    try:
        # Get a player we know exists
        player_match = PlayerMatch.objects.filter(player_name="Mohamed Salah").first()
        if not player_match:
            print("Mohamed Salah not found in PlayerMatch")
            return
            
        player_name = player_match.player_name
        print(f"Testing with player: {player_name}")
        
        # Create a request
        factory = RequestFactory()
        request = factory.get(f'/player/{player_name}/')
        
        # Call the view
        response = player_info(request, player_name)
        
        # Check if response is successful
        if response.status_code == 200:
            print("✅ View executed successfully")
            
            # Check the context (we can't easily access it, but we can check the Player model directly)
            player = Player.objects.filter(name=player_name).first()
            if player:
                print(f"✅ Player found: {player.name}")
                print(f"✅ Team: {player.team}")
            else:
                print("❌ Player not found in Player model")
        else:
            print(f"❌ View failed with status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing view: {e}")

if __name__ == "__main__":
    test_player_info_view()