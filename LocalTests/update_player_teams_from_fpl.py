# Update Player.team using FPL API player data and Teams table
# Usage: python LocalTests/update_player_teams_from_fpl.py

import os
import sys
import django
import requests

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def setup_django():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')
    django.setup()

setup_django()

from MyApi.models import Player, Team

def fetch_fpl_players():
    url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()
    return data['elements']

def main():
    # Build FPL player name -> (fpl_team_id, web_name, full_name) mapping
    fpl_players = fetch_fpl_players()
    fpl_name_map = {}
    for p in fpl_players:
        # Try both web_name and full name for matching
        fpl_name_map[p['web_name'].lower()] = (p['team'], p['web_name'], p['first_name'] + ' ' + p['second_name'])
        fpl_name_map[(p['first_name'] + ' ' + p['second_name']).lower()] = (p['team'], p['web_name'], p['first_name'] + ' ' + p['second_name'])
    # Build FPL team id -> canonical name
    id_to_name = {t.fpl_team_id: t.name for t in Team.objects.all()}
    updated = 0
    missing = 0
    for player in Player.objects.all():
        # Try to match by name (case-insensitive)
        name_key = player.name.strip().lower()
        fpl_info = fpl_name_map.get(name_key)
        if not fpl_info:
            # Try partial match (web_name only)
            fpl_info = next((v for k, v in fpl_name_map.items() if k in name_key or name_key in k), None)
        if fpl_info:
            fpl_team_id = fpl_info[0]
            canonical_name = id_to_name.get(fpl_team_id)
            if canonical_name and player.team != canonical_name:
                player.team = canonical_name
                player.save(update_fields=['team'])
                updated += 1
        else:
            missing += 1
            print(f"[WARN] Could not match FPL player for: {player.name}")
    print(f"Updated {updated} players to canonical team names from FPL. {missing} players could not be matched.")

if __name__ == '__main__':
    main()
