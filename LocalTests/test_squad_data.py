#!/usr/bin/env python
"""
Test the current squad data to ensure cost and elo information is populated
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

from MyApi.models import CurrentSquad

def test_squad_data():
    """Test the current squad data structure"""
    try:
        # Get current squad
        squad_instance = CurrentSquad.get_or_create_current_squad()
        
        print("Current squad data:")
        print("=" * 50)
        
        squad_data = squad_instance.squad
        total_elo = 0
        total_cost = 0
        player_count = 0
        
        for position, players in squad_data.items():
            print(f"\n{position.upper()}:")
            if players:
                for player in players:
                    print(f"  {player}")
                    if isinstance(player, dict) and 'elo' in player and 'cost' in player:
                        total_elo += float(player['elo'])
                        total_cost += float(player['cost'])
                        player_count += 1
            else:
                print("  No players")
        
        print("\n" + "=" * 50)
        print(f"Total players: {player_count}")
        if player_count > 0:
            print(f"Average Elo: {total_elo / player_count:.1f}")
            print(f"Total Cost: £{total_cost:.1f}m")
        else:
            print("No player data to calculate totals")
        
        # Test refresh method
        print("\nRefreshing squad data...")
        squad_instance.refresh_squad_data()
        print("Squad data refreshed!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_squad_data()