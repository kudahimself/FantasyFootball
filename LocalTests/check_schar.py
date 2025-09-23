#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')
django.setup()

from MyApi.models import Player, PlayerMatch

print("🔍 Investigating Fabian Schar data...")
print()

# Check Player table
players = Player.objects.filter(name__icontains='schar')
print("📊 Players in Player table:")
for player in players:
    print(f"  - {player.name}: {player.elo}")
print()

# Check PlayerMatch table
matches = PlayerMatch.objects.filter(player_name__icontains='schar').values('player_name').distinct()
print("📋 Player names in PlayerMatch table:")
for match in matches:
    player_name = match['player_name']
    count = PlayerMatch.objects.filter(player_name=player_name).count()
    print(f"  - {player_name}: {count} matches")
print()

# Check for exact matches
schar_players = Player.objects.filter(name__icontains='schar')
for player in schar_players:
    print(f"🎯 Checking matches for Player: '{player.name}'")
    exact_matches = PlayerMatch.objects.filter(player_name=player.name).count()
    similar_matches = PlayerMatch.objects.filter(player_name__icontains='schar').count()
    print(f"  - Exact name matches: {exact_matches}")
    print(f"  - Similar name matches: {similar_matches}")
    
    if exact_matches == 0 and similar_matches > 0:
        print("  ⚠️  Found similar matches but no exact matches!")
        similar = PlayerMatch.objects.filter(player_name__icontains='schar').values('player_name').distinct()
        for s in similar:
            print(f"     Similar: '{s['player_name']}'")
    print()