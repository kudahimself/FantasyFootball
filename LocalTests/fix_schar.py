#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')
django.setup()

from MyApi.models import Player, PlayerMatch
from django.db import transaction

print("🧹 Fixing Fabian Schär duplicate records...")

# Find the problematic PlayerMatch records
space_matches = PlayerMatch.objects.filter(player_name="Fabian Schär")
underscore_matches = PlayerMatch.objects.filter(player_name="Fabian_Schär")

print(f"📊 Found records:")
print(f"  - 'Fabian Schär' (space): {space_matches.count()} matches")
print(f"  - 'Fabian_Schär' (underscore): {underscore_matches.count()} matches")

if space_matches.count() > 0 and underscore_matches.count() > 0:
    print("\n🔧 Removing duplicate records with underscore...")
    
    with transaction.atomic():
        deleted_count = underscore_matches.delete()[0]
        print(f"✅ Deleted {deleted_count} duplicate 'Fabian_Schär' records")
        
        # Verify the Player record matches the remaining PlayerMatch records
        player = Player.objects.filter(name="Fabian Schär").first()
        remaining_matches = PlayerMatch.objects.filter(player_name="Fabian Schär")
        
        if player and remaining_matches.count() > 0:
            # Get the latest Elo from PlayerMatch and check if it differs significantly
            latest_match = remaining_matches.order_by('-date').first()
            if latest_match:
                print(f"📈 Player Elo: {player.elo}")
                print(f"📈 Latest match Elo: {latest_match.elo_after_match}")
                
                if abs(player.elo - latest_match.elo_after_match) > 100:
                    print(f"⚠️  Large difference detected!")
                    print(f"    Updating Player Elo from {player.elo} to {latest_match.elo_after_match}")
                    player.elo = latest_match.elo_after_match
                    player.save()
                    print("✅ Player Elo updated")
                else:
                    print("✅ Player and match Elos are consistent")
            
    print("\n🎯 Final verification:")
    final_player = Player.objects.filter(name="Fabian Schär").first()
    final_matches = PlayerMatch.objects.filter(player_name="Fabian Schär")
    
    if final_player and final_matches.count() > 0:
        print(f"  - Player: {final_player.name} = {final_player.elo}")
        print(f"  - Match records: {final_matches.count()}")
        print("✅ Fabian Schär cleanup completed successfully!")
    else:
        print("❌ Something went wrong during cleanup")

else:
    print("✅ No duplicate records found - already clean!")