"""
Script to diagnose why Elo recalculation is not updating any players for the current gameweek.
Checks:
- Current gameweek from SystemSettings
- Number of Player records for that week
- Example Player and their Elo
- Number of PlayerMatch records for that player
- Prints out a summary for debugging
"""



# Django setup for standalone script with error handling
import os
import sys
import traceback
# Add project root to sys.path so Django and apps can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')
    import django
    django.setup()
except Exception as e:
    print("Django setup failed:")
    traceback.print_exc()
    sys.exit(1)


from MyApi.models import Player, PlayerMatch, SystemSettings
from django.db.models import Max

def diagnose_elo_recalculation():
    settings = SystemSettings.get_settings()
    current_week = settings.current_gameweek
    print(f"Current gameweek from SystemSettings: {current_week}")

    # Find the latest gameweek in Player table based on the most recent date (if available)
    # Try to use a 'date' or 'updated' field if it exists, otherwise just show the max week
    print("\n--- Player Table Gameweek Diagnostics ---")
    # List all unique week values
    unique_weeks = Player.objects.values_list('week', flat=True).distinct()
    print(f"Unique week values in Player table: {list(unique_weeks)}")

    # Try to get the latest by date if possible
    if hasattr(Player, 'date'):
        latest = Player.objects.all().order_by('-date').first()
        if latest:
            print(f"Latest Player record by date: week={latest.week}, date={latest.date}")
    else:
        # Fallback: just show the max week value
        max_week = Player.objects.aggregate(Max('week'))['week__max']
        print(f"Max week value in Player table: {max_week}")

    player_count = Player.objects.filter(week=current_week).count()
    print(f"\nNumber of Player records for week {current_week}: {player_count}")

    if player_count == 0:
        print("No Player records found for this week. Import player data first.")
        return

    # Get an example player
    player = Player.objects.filter(week=current_week).first()
    print(f"Example player: {player.name} (Elo: {player.elo})")

    # Get PlayerMatch records for this player
    match_count = PlayerMatch.objects.filter(player_name=player.name).count()
    print(f"Number of PlayerMatch records for {player.name}: {match_count}")
    if match_count == 0:
        print(f"No PlayerMatch records found for {player.name}. Import match data first.")
    else:
        matches = PlayerMatch.objects.filter(player_name=player.name).order_by('date')[:5]
        print(f"First 5 matches for {player.name}:")
        for m in matches:
            print(f"  Date: {m.date}, Points: {m.points}, Competition: {m.competition}")

if __name__ == "__main__":
    diagnose_elo_recalculation()
