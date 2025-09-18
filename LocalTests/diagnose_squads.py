#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')
django.setup()

from MyApi.models import SystemSettings, Player, PlayerMatch

def diagnose_squads_issue():
    """
    Diagnose why the squads page isn't showing squads.
    Check database state and player data availability.
    """
    print("🔍 Diagnosing squads page issue...")
    print()
    
    # Check SystemSettings
    try:
        settings = SystemSettings.get_settings()
        current_week = settings.current_gameweek
        print(f"📅 Current gameweek: {current_week}")
    except Exception as e:
        print(f"❌ Error getting SystemSettings: {e}")
        return
    
    # Check total players
    total_players = Player.objects.count()
    print(f"👥 Total players in database: {total_players}")
    
    # Check available weeks
    weeks = list(Player.objects.values_list('week', flat=True).distinct().order_by('week'))
    print(f"📊 Available weeks: {weeks}")
    
    # Check players for current week
    current_week_players = Player.objects.filter(week=current_week).count()
    print(f"🎯 Players for week {current_week}: {current_week_players}")
    
    if current_week_players == 0:
        print()
        print("❌ ISSUE FOUND: No players exist for the current gameweek!")
        print("   This is why the squads page shows no squads.")
        print()
        
        if weeks:
            print(f"💡 SOLUTION: Change current gameweek to an available week:")
            for week in weeks[:5]:  # Show first 5 weeks
                week_count = Player.objects.filter(week=week).count()
                print(f"   - Week {week}: {week_count} players")
            
            # Suggest updating to the most populated week
            week_counts = [(week, Player.objects.filter(week=week).count()) for week in weeks]
            best_week = max(week_counts, key=lambda x: x[1])
            print()
            print(f"🔧 Recommended: Set current gameweek to {best_week[0]} ({best_week[1]} players)")
            
            # Offer to fix it
            fix_it = input("\n❓ Would you like me to update the current gameweek? (y/n): ").lower().strip()
            if fix_it in ['y', 'yes']:
                settings.current_gameweek = best_week[0]
                settings.save()
                print(f"✅ Updated current gameweek to {best_week[0]}")
                print("🔄 Try the squads page again - it should work now!")
                return True
        else:
            print("❌ No player data found in any week!")
            print("   You may need to import player data first.")
            return False
    else:
        print("✅ Players exist for current gameweek")
        
        # Check players by position for current week
        print()
        print(f"📈 Players by position for week {current_week}:")
        for position in ['Keeper', 'Defender', 'Midfielder', 'Attacker']:
            count = Player.objects.filter(week=current_week, position=position).count()
            print(f"   - {position}: {count} players")
            
            if count == 0:
                print(f"      ❌ No {position}s found!")
            elif count < 5:
                print(f"      ⚠️  Only {count} {position}s (might need more for squad generation)")
        
        # Check if players have valid Elo ratings
        print()
        print("🔢 Elo ratings check:")
        players_with_elo = Player.objects.filter(week=current_week, elo__gt=0).count()
        players_without_elo = Player.objects.filter(week=current_week, elo__lte=0).count()
        print(f"   - Players with Elo > 0: {players_with_elo}")
        print(f"   - Players with Elo ≤ 0: {players_without_elo}")
        
        if players_without_elo > 0:
            print("   ⚠️  Some players have invalid Elo ratings")
        
        # Check cost data
        players_with_cost = Player.objects.filter(week=current_week, cost__gt=0).count()
        players_without_cost = Player.objects.filter(week=current_week, cost__lte=0).count()
        print(f"   - Players with cost > 0: {players_with_cost}")
        print(f"   - Players with cost ≤ 0: {players_without_cost}")
        
        if players_without_cost > 0:
            print("   ⚠️  Some players have invalid cost data")
        
        print()
        if players_with_elo > 0 and players_with_cost > 0:
            print("✅ Database looks good - squads should be generating")
            print("🔍 The issue might be in the frontend or API call")
            
            # Test the squad generation logic
            print()
            print("🧪 Testing squad generation...")
            try:
                keepers = Player.objects.filter(
                    position='Keeper', 
                    week=current_week,
                    elo__gt=0
                ).order_by('-elo')[:5]
                print(f"   - Found {keepers.count()} keepers")
                for keeper in keepers:
                    print(f"     • {keeper.name}: Elo {keeper.elo}, Cost {keeper.cost}")
                
                if keepers.count() == 0:
                    print("   ❌ No valid keepers found for squad generation!")
                else:
                    print("   ✅ Squad generation should work")
                    
            except Exception as e:
                print(f"   ❌ Error testing squad generation: {e}")
        else:
            print("❌ Invalid player data found - this could cause squad generation issues")
    
    return False

if __name__ == "__main__":
    diagnose_squads_issue()