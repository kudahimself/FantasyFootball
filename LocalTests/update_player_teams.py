# Update Player.team to canonical name from Teams table using FPL team id
# Usage: python LocalTests/update_player_teams.py

import os
import sys
import django

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def setup_django():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')
    django.setup()

setup_django()

from MyApi.models import Player, Team

def update_player_teams():
    # Build mapping: fpl_team_id -> canonical team name
    id_to_name = {t.fpl_team_id: t.name for t in Team.objects.all()}
    name_to_id = {t.name.lower(): t.fpl_team_id for t in Team.objects.all()}
    updated = 0
    missing = 0
    for player in Player.objects.all():
        # Try to map current team string to fpl_team_id (if already canonical, this is fine)
        team_str = (player.team or '').strip().lower()
        fpl_team_id = name_to_id.get(team_str)
        if fpl_team_id:
            canonical_name = id_to_name[fpl_team_id]
            if player.team != canonical_name:
                player.team = canonical_name
                player.save(update_fields=['team'])
                updated += 1
        else:
            missing += 1
            print(f"[WARN] Could not map team for player: {player.name} (team: {player.team})")
    print(f"Updated {updated} players to canonical team names. {missing} players could not be mapped.")

if __name__ == '__main__':
    update_player_teams()
