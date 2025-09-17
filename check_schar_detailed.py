#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')
django.setup()

from MyApi.models import Player, PlayerMatch

print("🔍 Investigating Fabian Schar data - broader search...")
print()

# Search for any variation of the name
search_terms = ['schar', 'fabian', 'schär', 'Schär', 'Schar']

for term in search_terms:
    print(f"🔎 Searching for '{term}':")
    
    # Check Player table
    players = Player.objects.filter(name__icontains=term)
    print(f"  📊 Players table: {players.count()} matches")
    for player in players:
        print(f"    - {player.name}: {player.elo}")
    
    # Check PlayerMatch table
    matches = PlayerMatch.objects.filter(player_name__icontains=term).values('player_name').distinct()
    print(f"  📋 PlayerMatch table: {matches.count()} distinct names")
    for match in matches:
        player_name = match['player_name']
        count = PlayerMatch.objects.filter(player_name=player_name).count()
        print(f"    - {player_name}: {count} matches")
    print()

# Let's also check players with high ratings around 2937
print("🎯 Checking players with Elo rating around 2937...")
high_rated = Player.objects.filter(elo__gte=2900, elo__lte=2950)
for player in high_rated:
    print(f"  - {player.name}: {player.elo}")
print()

# And check players with rating around 1584
print("🎯 Checking players with Elo rating around 1584...")
mid_rated = Player.objects.filter(elo__gte=1580, elo__lte=1590)
for player in mid_rated:
    print(f"  - {player.name}: {player.elo}")
print()