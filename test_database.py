"""
Script to test the database migration and functionality.
"""

import os
import sys
import django

# Setup Django
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')
django.setup()

from MyApp.models import Player
from fantasy_models.squad_db import SquadSelector


def test_database_functionality():
    """
    Test that the database functionality works correctly.
    """
    print("Testing database functionality...\n")
    
    # Test 1: Check if Player model works
    print("1. Testing Player model...")
    try:
        player_count = Player.objects.count()
        print(f"   Total players in database: {player_count}")
        
        if player_count == 0:
            print("   No players found. You need to run the import command first.")
            print("   Run: python manage.py import_elo_data --week 4")
            return False
        else:
            print("   ✓ Player model is working")
    except Exception as e:
        print(f"   ✗ Error with Player model: {e}")
        return False
    
    # Test 2: Check if we have data for week 4
    print("\n2. Testing data for week 4...")
    try:
        week_4_players = Player.objects.filter(week=4).count()
        print(f"   Players for week 4: {week_4_players}")
        
        if week_4_players == 0:
            print("   No data for week 4. Run: python manage.py import_elo_data --week 4")
            return False
        else:
            print("   ✓ Week 4 data is available")
    except Exception as e:
        print(f"   ✗ Error checking week 4 data: {e}")
        return False
    
    # Test 3: Test SquadSelector with database
    print("\n3. Testing SquadSelector with database...")
    try:
        squad_selector = SquadSelector(week=4)
        print(f"   Loaded {len(squad_selector.df)} players from database")
        
        # Test getting top players
        top_goalkeepers = squad_selector.get_top_players('Keeper', 5)
        print(f"   Top 5 goalkeepers: {len(top_goalkeepers)}")
        
        if len(top_goalkeepers) > 0:
            print(f"   Best goalkeeper: {top_goalkeepers.iloc[0]['Player']} (Elo: {top_goalkeepers.iloc[0]['Elo']})")
            print("   ✓ SquadSelector is working with database")
        else:
            print("   ✗ No goalkeepers found")
            return False
            
    except Exception as e:
        print(f"   ✗ Error with SquadSelector: {e}")
        return False
    
    # Test 4: Test position statistics
    print("\n4. Testing position statistics...")
    try:
        for position, _ in Player.POSITION_CHOICES:
            count = Player.objects.filter(week=4, position=position).count()
            print(f"   {position}: {count} players")
        print("   ✓ Position statistics are working")
    except Exception as e:
        print(f"   ✗ Error getting position statistics: {e}")
        return False
    
    print("\n✓ All tests passed! The database migration is working correctly.")
    return True


if __name__ == "__main__":
    success = test_database_functionality()
    if success:
        print("\nYou can now use the database instead of CSV files!")
        print("\nNext steps:")
        print("1. Run migrations if you haven't: python manage.py migrate")
        print("2. Import data: python manage.py import_elo_data --week 4")
        print("3. Test the web interface")
    else:
        print("\nPlease fix the issues above before proceeding.")