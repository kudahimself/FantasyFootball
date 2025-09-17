#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')
django.setup()

from MyApi.models import Player, PlayerMatch
from django.db import transaction

def fix_underscore_duplicates():
    """
    Find and fix all players with underscore/space duplicate records.
    This handles cases where player names exist in both formats:
    - "Player Name" (with spaces)
    - "Player_Name" (with underscores)
    """
    print("🔍 Scanning for players with underscore/space duplicates...")
    print()

    # Get all unique player names from PlayerMatch with underscores
    underscore_names = PlayerMatch.objects.filter(
        player_name__contains='_'
    ).values('player_name').distinct()

    potential_duplicates = []
    fixed_players = []
    errors = []

    # Find potential duplicates
    for match in underscore_names:
        underscore_name = match['player_name']
        space_name = underscore_name.replace('_', ' ')
        
        # Check if there's also a version with spaces
        space_count = PlayerMatch.objects.filter(player_name=space_name).count()
        underscore_count = PlayerMatch.objects.filter(player_name=underscore_name).count()
        
        if space_count > 0 and underscore_count > 0:
            potential_duplicates.append({
                'space_name': space_name,
                'underscore_name': underscore_name,
                'space_count': space_count,
                'underscore_count': underscore_count
            })

    if not potential_duplicates:
        print("✅ No duplicate players found!")
        return

    print(f"⚠️  Found {len(potential_duplicates)} players with duplicates:")
    for dup in potential_duplicates:
        print(f"  - '{dup['space_name']}' ({dup['space_count']} matches) vs '{dup['underscore_name']}' ({dup['underscore_count']} matches)")

    print(f"\n🔧 Starting cleanup process...")
    print()

    # Process each duplicate
    for i, dup in enumerate(potential_duplicates, 1):
        space_name = dup['space_name']
        underscore_name = dup['underscore_name']
        
        print(f"[{i}/{len(potential_duplicates)}] Processing: {space_name}")
        
        try:
            with transaction.atomic():
                # Get the Player record (should exist with space name)
                player = Player.objects.filter(name=space_name).first()
                
                if not player:
                    print(f"  ❌ No Player record found for '{space_name}' - skipping")
                    errors.append(f"Missing Player record: {space_name}")
                    continue
                
                # Get latest match data from both versions
                space_matches = PlayerMatch.objects.filter(player_name=space_name)
                underscore_matches = PlayerMatch.objects.filter(player_name=underscore_name)
                
                space_latest = space_matches.order_by('-date').first()
                underscore_latest = underscore_matches.order_by('-date').first()
                
                # Compare dates to see which is more recent
                latest_elo = player.elo
                if space_latest and underscore_latest:
                    if underscore_latest.date > space_latest.date:
                        latest_elo = underscore_latest.elo_after_match
                        print(f"  📅 Using underscore version (more recent: {underscore_latest.date})")
                    else:
                        latest_elo = space_latest.elo_after_match
                        print(f"  📅 Using space version (more recent: {space_latest.date})")
                elif underscore_latest:
                    latest_elo = underscore_latest.elo_after_match
                    print(f"  📅 Only underscore version has data")
                elif space_latest:
                    latest_elo = space_latest.elo_after_match
                    print(f"  📅 Only space version has data")
                
                # Remove underscore version records
                deleted_count = underscore_matches.delete()[0]
                print(f"  🗑️  Deleted {deleted_count} underscore records")
                
                # Update Player Elo if significantly different
                if abs(player.elo - latest_elo) > 50:  # Allow small differences
                    old_elo = player.elo
                    player.elo = latest_elo
                    player.save()
                    print(f"  📈 Updated Player Elo: {old_elo} → {latest_elo}")
                else:
                    print(f"  ✅ Player Elo consistent: {player.elo}")
                
                fixed_players.append(space_name)
                print(f"  ✅ Fixed successfully")
                
        except Exception as e:
            error_msg = f"Error processing {space_name}: {str(e)}"
            print(f"  ❌ {error_msg}")
            errors.append(error_msg)
        
        print()

    # Final summary
    print("📊 CLEANUP SUMMARY:")
    print(f"  ✅ Successfully fixed: {len(fixed_players)} players")
    if fixed_players:
        for player in fixed_players:
            print(f"    - {player}")
    
    if errors:
        print(f"  ❌ Errors encountered: {len(errors)}")
        for error in errors:
            print(f"    - {error}")
    
    print(f"\n🎯 Final verification...")
    
    # Quick verification that no underscore duplicates remain
    remaining_duplicates = []
    for match in PlayerMatch.objects.filter(player_name__contains='_').values('player_name').distinct():
        underscore_name = match['player_name']
        space_name = underscore_name.replace('_', ' ')
        if PlayerMatch.objects.filter(player_name=space_name).exists():
            remaining_duplicates.append(underscore_name)
    
    if remaining_duplicates:
        print(f"  ⚠️  {len(remaining_duplicates)} duplicates still remain:")
        for name in remaining_duplicates:
            print(f"    - {name}")
    else:
        print("  ✅ No remaining duplicates found!")
    
    print("\n🏁 Underscore cleanup completed!")

if __name__ == "__main__":
    fix_underscore_duplicates()