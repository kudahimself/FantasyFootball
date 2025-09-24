
# Audit Player.team values against Teams table
# Usage: python LocalTests/audit_player_teams.py

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

def audit_player_teams():
    # Build set of canonical team names (lowercase for comparison)
    canonical_teams = {t.name.lower() for t in Team.objects.all()}
    print(f"Loaded {len(canonical_teams)} canonical teams from Teams table.")

    # Find all players with missing or non-canonical team values
    mismatches = []
    for player in Player.objects.all():
        team = (player.team or '').strip()
        if not team or team.lower() not in canonical_teams:
            mismatches.append((player.name, player.team))

    if mismatches:
        print(f"Found {len(mismatches)} players with missing or non-canonical team values:")
        for name, team in mismatches:
            print(f"  Player: {name:30} | Team: {team}")
    else:
        print("All Player.team values are canonical.")

if __name__ == '__main__':
    audit_player_teams()
