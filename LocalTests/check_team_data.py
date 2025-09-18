#!/usr/bin/env python
"""
Check team data in the database
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')

# Setup Django
django.setup()

from MyApi.models import Player

def check_team_data():
    """Check what team data exists"""
    try:
        # Check total players with teams
        total_with_teams = Player.objects.filter(team__isnull=False).count()
        total_players = Player.objects.count()
        
        print(f"Players with team data: {total_with_teams}/{total_players}")
        
        # Check a few examples
        print("\nSample players with teams:")
        players = Player.objects.filter(team__isnull=False).values('name', 'team', 'week')[:10]
        for player in players:
            print(f"  {player['name']} - {player['team']} (Week {player['week']})")
            
        # Check for specific well-known players
        print("\nChecking well-known players:")
        test_names = ['Mohamed Salah', 'Mohamed_Salah', 'Harry Kane', 'Harry_Kane']
        for name in test_names:
            player = Player.objects.filter(name=name).first()
            if player:
                print(f"  {player.name} - Team: {player.team} (Week {player.week})")
            else:
                print(f"  {name} - Not found")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_team_data()