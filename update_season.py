#!/usr/bin/env python
"""
Update the current season in SystemSettings to 2025/26
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

from MyApi.models import SystemSettings

def update_season():
    """Update the current season to 2025/26"""
    try:
        # Get or create settings
        settings = SystemSettings.get_settings()
        
        print(f"Current season before update: {settings.current_season}")
        print(f"Current gameweek before update: {settings.current_gameweek}")
        
        # Update the season
        settings.current_season = "2025/26"
        settings.save()
        
        print(f"Current season after update: {settings.current_season}")
        print(f"Current gameweek after update: {settings.current_gameweek}")
        
        print("✅ Season updated successfully!")
        
    except Exception as e:
        print(f"❌ Error updating season: {e}")

if __name__ == "__main__":
    update_season()