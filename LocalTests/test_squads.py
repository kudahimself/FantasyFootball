"""
Quick test script to verify squad generation works correctly.
"""

import os
import sys
import django

# Setup Django
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')
django.setup()

from fantasy_models.squad_db import SquadSelector


def test_squad_generation():
    """
    Test squad generation and print the results.
    """
    print("Testing squad generation...\n")
    
    try:
        squad_selector = SquadSelector(week=4)
        squads = squad_selector.generate_squads()
        
        print(f"Generated {len(squads)} squads")
        
        for squad in squads:
            print(f"\nSquad {squad['squad_number']}:")
            print(f"  Positions: {squad['positions']} (GK-DEF-MID-FWD)")
            
            total_cost = 0
            total_elo = 0
            total_players = 0
            
            for position, players in squad['players'].items():
                print(f"  {position.capitalize()}: {len(players)} players")
                for player in players:
                    print(f"    - {player['name']} (£{player['cost']}m, Elo: {player['elo']})")
                    total_cost += player['cost']
                    total_elo += player['elo']
                    total_players += 1
            
            print(f"  Total: {total_players} players, £{total_cost:.1f}m, {total_elo:.1f} Elo")
        
        print(f"\n✓ Squad generation successful!")
        return True
        
    except Exception as e:
        print(f"✗ Error in squad generation: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_squad_generation()