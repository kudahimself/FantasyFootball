"""
Repair script to fix corrupted player position and team data
caused by the recalculate Elo function overwriting existing data.
"""

import os
import sys
import django
from collections import Counter

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')
django.setup()

from MyApi.models import Player, PlayerMatch, SystemSettings


def repair_player_positions():
    """
    Repair player positions by deriving them from PlayerMatch data.
    """
    settings = SystemSettings.get_settings()
    current_week = settings.current_gameweek
    
    # Position mapping from granular to broad categories
    position_mapping = {
        'GK': 'Keeper',
        'RB': 'Defender', 'LB': 'Defender', 'CB': 'Defender', 'WB': 'Defender',
        'DM': 'Midfielder', 'CM': 'Midfielder', 'AM': 'Midfielder', 'RM': 'Midfielder', 'LM': 'Midfielder',
        'RW': 'Attacker', 'LW': 'Attacker', 'CF': 'Attacker', 'ST': 'Attacker', 'FW': 'Attacker'
    }
    
    # Get all players with corrupted positions (position = '0')
    corrupted_players = Player.objects.filter(week=current_week, position='0')
    
    print(f"Found {corrupted_players.count()} players with corrupted positions")
    
    fixed_count = 0
    not_found_count = 0
    
    for player in corrupted_players:
        # Find all PlayerMatch records for this player to determine position
        player_matches = PlayerMatch.objects.filter(player_name=player.name)
        
        if not player_matches.exists():
            print(f"No match data found for {player.name}")
            not_found_count += 1
            continue
        
        # Get the most common position from recent matches
        recent_positions = []
        for match in player_matches.order_by('-date')[:10]:  # Last 10 matches
            if match.position:
                recent_positions.append(match.position)
        
        if not recent_positions:
            print(f"No position data in matches for {player.name}")
            not_found_count += 1
            continue
        
        # Find the most common granular position
        most_common_position = Counter(recent_positions).most_common(1)[0][0]
        
        # Map to broad category
        main_position = 'Midfielder'  # Default
        for key, value in position_mapping.items():
            if key in most_common_position:
                main_position = value
                break
        
        # Update the player
        player.position = main_position
        player.save()
        
        print(f"Fixed {player.name}: {most_common_position} -> {main_position}")
        fixed_count += 1
    
    print(f"\nRepair complete:")
    print(f"  Fixed: {fixed_count} players")
    print(f"  No data found: {not_found_count} players")


def repair_player_teams():
    """
    Try to restore team information from any available data.
    This is more challenging since PlayerMatch doesn't have team data.
    """
    settings = SystemSettings.get_settings()
    current_week = settings.current_gameweek
    
    # For now, we'll just count how many need fixing
    unknown_teams = Player.objects.filter(week=current_week, team='Unknown')
    print(f"\nPlayers with 'Unknown' team: {unknown_teams.count()}")
    
    # TODO: Could potentially derive team from opponent data or other sources
    print("Team repair not implemented yet - would need additional data sources")


if __name__ == "__main__":
    print("Starting player data repair...")
    repair_player_positions()
    repair_player_teams()
    print("Repair process completed!")