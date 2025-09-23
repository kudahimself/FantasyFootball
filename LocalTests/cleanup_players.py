#!/usr/bin/env python
"""
Django management command to clean up duplicate players and fix name inconsistencies.
This addresses the issue where we have multiple players with similar names in the database.
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')
django.setup()

from django.db import transaction
from MyApi.models import Player, PlayerMatch, EloCalculation

def cleanup_duplicate_players():
    """Clean up duplicate players and fix name inconsistencies"""
    
    print("🧹 Starting player data cleanup...")
    
    # Step 1: Find and fix known problematic cases like Marc Cucurella
    problematic_cases = [
        {
            'short_name': 'Marc Cucurella',
            'full_name': 'Marc Cucurella Saseta',
            'keep_full_name': True  # Which one to keep
        },
        # Add more cases as discovered
    ]
    
    with transaction.atomic():
        for case in problematic_cases:
            short_name = case['short_name']
            full_name = case['full_name']
            keep_full_name = case['keep_full_name']
            
            print(f"\n📝 Processing: '{short_name}' vs '{full_name}'")
            
            # Get both player records
            short_players = Player.objects.filter(name=short_name)
            full_players = Player.objects.filter(name=full_name)
            
            if short_players.exists() and full_players.exists():
                if keep_full_name:
                    # Delete the short name player (usually from elos.csv)
                    short_player = short_players.first()
                    full_player = full_players.first()
                    
                    print(f"  ❌ Deleting duplicate: '{short_name}' (Elo: {short_player.elo})")
                    print(f"  ✅ Keeping: '{full_name}' (Elo: {full_player.elo})")
                    
                    short_players.delete()
                else:
                    # Keep short name, delete full name
                    full_players.delete()
                    print(f"  ✅ Keeping: '{short_name}'")
                    print(f"  ❌ Deleting: '{full_name}'")
        
        # Step 2: Find players in Player table who don't have match data
        players_without_matches = []
        all_players = Player.objects.all()
        
        for player in all_players:
            # Check if this player has any matches
            has_matches = PlayerMatch.objects.filter(player_name=player.name).exists()
            if not has_matches:
                # Try with underscores/spaces swapped
                alt_name = player.name.replace(' ', '_') if ' ' in player.name else player.name.replace('_', ' ')
                has_alt_matches = PlayerMatch.objects.filter(player_name=alt_name).exists()
                
                if has_alt_matches:
                    # Update player name to match PlayerMatch records
                    print(f"  🔄 Updating player name: '{player.name}' -> '{alt_name}'")
                    player.name = alt_name
                    player.save()
                else:
                    players_without_matches.append(player.name)
        
        if players_without_matches:
            print(f"\n⚠️  Found {len(players_without_matches)} players without match data:")
            for name in players_without_matches[:10]:  # Show first 10
                print(f"    - {name}")
            
            # Option to delete players without match data
            response = input(f"\nDelete {len(players_without_matches)} players without match data? (y/N): ")
            if response.lower() == 'y':
                Player.objects.filter(name__in=players_without_matches).delete()
                print(f"  ❌ Deleted {len(players_without_matches)} players without match data")
        
        # Step 3: Verify data consistency
        print(f"\n📊 Final verification:")
        total_players = Player.objects.count()
        players_with_matches = 0
        
        for player in Player.objects.all():
            if PlayerMatch.objects.filter(player_name=player.name).exists():
                players_with_matches += 1
        
        print(f"  - Total players: {total_players}")
        print(f"  - Players with match data: {players_with_matches}")
        print(f"  - Players without match data: {total_players - players_with_matches}")
        
    print("\n✅ Player data cleanup completed!")

if __name__ == '__main__':
    cleanup_duplicate_players()