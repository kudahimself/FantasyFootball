# remove_current_squad.py
"""
Script to delete the current squad from the database for a clean test/reset.
Usage: python remove_current_squad.py
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')
django.setup()

from MyApi.models import CurrentSquad

def main():
    try:
        squad = CurrentSquad.get_or_create_current_squad()
        if squad:
            squad.delete()
            print("✅ Current squad deleted.")
        else:
            print("No current squad found to delete.")
    except Exception as e:
        print(f"❌ Error deleting current squad: {e}")

if __name__ == "__main__":
    main()
