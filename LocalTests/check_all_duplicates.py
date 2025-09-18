#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')
django.setup()

from MyApi.models import Player, PlayerMatch

print("🔍 Checking for other players with underscore/space duplicates...")
print()

# Get all unique player names from PlayerMatch with underscores
underscore_names = PlayerMatch.objects.filter(
    player_name__contains='_'
).values('player_name').distinct()

potential_duplicates = []

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

if potential_duplicates:
    print(f"⚠️  Found {len(potential_duplicates)} players with potential duplicates:")
    for dup in potential_duplicates:
        print(f"  - '{dup['space_name']}' ({dup['space_count']} matches) vs '{dup['underscore_name']}' ({dup['underscore_count']} matches)")
        
        # Check if there's a Player record
        player = Player.objects.filter(name=dup['space_name']).first()
        if player:
            print(f"    Player table Elo: {player.elo}")
            
            # Get latest match Elo for both versions
            space_latest = PlayerMatch.objects.filter(player_name=dup['space_name']).order_by('-date').first()
            underscore_latest = PlayerMatch.objects.filter(player_name=dup['underscore_name']).order_by('-date').first()
            
            if space_latest:
                print(f"    Latest space match Elo: {space_latest.elo_after_match}")
            if underscore_latest:
                print(f"    Latest underscore match Elo: {underscore_latest.elo_after_match}")
        else:
            print(f"    ❌ No Player record found for '{dup['space_name']}'")
        print()
else:
    print("✅ No other duplicate players found!")