# Script to print one FPL fixture and try to match to PlayerFixture creation logic
# Usage: python LocalTests/debug_fixture_matching.py

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

from MyApi.models import Player, Team, PlayerFixture, SystemSettings

def main():
    # Fetch one FPL fixture
    fpl_fixtures = requests.get('https://fantasy.premierleague.com/api/fixtures/').json()
    if not fpl_fixtures:
        print("No FPL fixtures found!")
        return
    fixture = fpl_fixtures[0]
    print("Sample FPL fixture:")
    print(fixture)

    # Map FPL team IDs to canonical names
    id_to_name = {t.fpl_team_id: t.name for t in Team.objects.all()}
    print("\nTeam mapping:")
    print(id_to_name)

    # Try to find players in our DB for the home and away teams for the current week
    current_gw = SystemSettings.get_current_gameweek()
    home_team_id = fixture['team_h']
    away_team_id = fixture['team_a']
    home_team_name = id_to_name.get(home_team_id)
    away_team_name = id_to_name.get(away_team_id)
    print(f"\nHome team: {home_team_id} -> {home_team_name}")
    print(f"Away team: {away_team_id} -> {away_team_name}")

    home_players = Player.objects.filter(team=home_team_name, week=current_gw)
    away_players = Player.objects.filter(team=away_team_name, week=current_gw)
    print(f"\nPlayers for home team ({home_team_name}): {[p.name for p in home_players]}")
    print(f"Players for away team ({away_team_name}): {[p.name for p in away_players]}")

    # Show if any PlayerFixture exists for this fixture
    pf_home = PlayerFixture.objects.filter(team=home_team_id, gameweek=fixture['event'])
    pf_away = PlayerFixture.objects.filter(team=away_team_id, gameweek=fixture['event'])
    print(f"\nPlayerFixtures for home team (team_id={home_team_id}, gw={fixture['event']}): {pf_home.count()}")
    print(f"PlayerFixtures for away team (team_id={away_team_id}, gw={fixture['event']}): {pf_away.count()}")

if __name__ == '__main__':
    main()
