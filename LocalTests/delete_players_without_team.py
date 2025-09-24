# Delete all Player records without a team name
# Usage: python LocalTests/delete_players_without_team.py

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

from MyApi.models import Player

def delete_players_without_team():
    # Delete players where team or position is NULL, empty, or only whitespace
    qs = (
        Player.objects.filter(team__isnull=True) |
        Player.objects.filter(team__exact='') |
        Player.objects.filter(team__regex=r'^\s+$') |
        Player.objects.filter(position__isnull=True) |
        Player.objects.filter(position__exact='') |
        Player.objects.filter(position__regex=r'^\s+$')
    )
    count = qs.count()
    if count:
        print(f"Deleting {count} players without a team name or with empty/whitespace position...")
        qs.delete()
    else:
        print("No players without a team name or with empty/whitespace position found.")

if __name__ == '__main__':
    delete_players_without_team()
