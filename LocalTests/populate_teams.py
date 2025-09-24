

import os
import sys
import django

# Add workspace root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')
django.setup()

import requests
from MyApi.models import Team

def populate_teams_from_fpl():
    """
    Populate the Team table with canonical FPL team ID and name mapping from the FPL API.
    """
    url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    teams = data['teams']
    created, updated = 0, 0
    for team in teams:
        obj, was_created = Team.objects.update_or_create(
            fpl_team_id=team['id'],
            defaults={'name': team['name']}
        )
        if was_created:
            created += 1
        else:
            updated += 1
    print(f"Teams populated: {created} created, {updated} updated.")

if __name__ == "__main__":
    populate_teams_from_fpl()
