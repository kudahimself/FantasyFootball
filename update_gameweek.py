#!/usr/bin/env python
"""
Get current gameweek information from FPL API and update SystemSettings
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
from MyApi.utils.fpl_gameweek_info import get_current_gameweek_sync

def update_current_gameweek():
    """Update current gameweek using FPL API"""
    try:
        # Get FPL gameweek info
        fpl_info = get_current_gameweek_sync()
        
        if fpl_info and 'current_gameweek' in fpl_info:
            current_gw = fpl_info['current_gameweek']
            
            # Get settings
            settings = SystemSettings.get_settings()
            
            print(f"Current gameweek before update: {settings.current_gameweek}")
            print(f"FPL current gameweek: {current_gw}")
            
            # Update gameweek
            settings.current_gameweek = current_gw
            settings.save()
            
            print(f"Current gameweek after update: {settings.current_gameweek}")
            print("✅ Gameweek updated successfully!")
        else:
            print("❌ Could not get current gameweek from FPL API")
            
    except Exception as e:
        print(f"❌ Error updating gameweek: {e}")

if __name__ == "__main__":
    update_current_gameweek()