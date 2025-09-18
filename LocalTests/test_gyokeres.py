#!/usr/bin/env python3
"""
Test Victor Gyökeres Elo calculation and validate duplicate date constraints.
"""

import os
import django
import asyncio
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')
django.setup()

from MyApi.models import PlayerMatch, Player
import pandas as pd


def find_gyokeres():
    """Find Victor Gyökeres in the database with various spellings."""
    print("🔍 Searching for Victor Gyökeres...")
    
    # Look specifically for Viktor Gyökeres
    viktor_matches = PlayerMatch.objects.filter(
        player_name='Viktor Gyökeres'
    ).order_by('date')
    
    if viktor_matches.exists():
        exact_name = viktor_matches.first().player_name
        print(f"✅ Found: {exact_name}")
        return exact_name
    
    # Try alternative spellings
    alternatives = [
        'Victor Gyökeres',
        'Viktor Gyokeres', 
        'Victor Gyokeres'
    ]
    
    for alt_name in alternatives:
        matches = PlayerMatch.objects.filter(player_name=alt_name)
        if matches.exists():
            print(f"✅ Found: {alt_name}")
            return alt_name
    
    # Fallback - find any player with "gyök" in name
    gyok_matches = PlayerMatch.objects.filter(player_name__icontains='gyök')
    if gyok_matches.exists():
        unique_names = gyok_matches.values_list('player_name', flat=True).distinct()
        print(f"Found players with 'gyök': {list(unique_names)[:5]}")
        return unique_names[0]
    
    print("❌ Viktor Gyökeres not found in database")
    return None


def check_duplicate_dates(player_name):
    """Check for duplicate match dates for a player."""
    print(f"\n📅 Checking duplicate dates for {player_name}...")
    
    matches = PlayerMatch.objects.filter(player_name=player_name).order_by('date')
    
    if not matches.exists():
        print("❌ No matches found")
        return []
    
    # Convert to DataFrame for easier analysis
    data = list(matches.values('date', 'opponent', 'points', 'goals', 'assists', 'competition'))
    df = pd.DataFrame(data)
    
    # Group by date and count
    date_counts = df.groupby('date').size()
    duplicates = date_counts[date_counts > 1]
    
    if len(duplicates) > 0:
        print(f"❌ FOUND {len(duplicates)} DATES WITH MULTIPLE MATCHES:")
        duplicate_dates = []
        
        for date, count in duplicates.items():
            print(f"\n   📅 {date} ({count} matches):")
            matches_on_date = matches.filter(date=date)
            for match in matches_on_date:
                print(f"      vs {match.opponent} ({match.competition}) - {match.points}pts, {match.goals}G, {match.assists}A")
            duplicate_dates.append(date)
        
        return duplicate_dates
    else:
        print("✅ No duplicate dates found")
        return []


def analyze_player_performance(player_name):
    """Analyze player's performance data."""
    print(f"\n📊 Performance Analysis for {player_name}...")
    
    matches = PlayerMatch.objects.filter(player_name=player_name).order_by('date')
    
    if not matches.exists():
        print("❌ No matches found")
        return
    
    total_matches = matches.count()
    total_points = sum(match.points for match in matches)
    total_goals = sum(match.goals for match in matches)
    total_assists = sum(match.assists for match in matches)
    
    print(f"   📈 Total matches: {total_matches}")
    print(f"   ⚽ Total goals: {total_goals}")
    print(f"   🎯 Total assists: {total_assists}")
    print(f"   📊 Total fantasy points: {total_points}")
    print(f"   📊 Average points per match: {total_points/total_matches:.2f}")
    
    # Show best performances
    best_matches = matches.order_by('-points')[:5]
    print(f"\n   🏆 Top 5 performances:")
    for match in best_matches:
        print(f"      {match.date}: vs {match.opponent} - {match.points}pts ({match.goals}G, {match.assists}A)")
    
    # Show recent performances
    recent_matches = matches.order_by('-date')[:5]
    print(f"\n   📅 Recent 5 matches:")
    for match in recent_matches:
        print(f"      {match.date}: vs {match.opponent} - {match.points}pts ({match.goals}G, {match.assists}A)")


def simulate_elo_calculation(player_name):
    """Simulate Elo calculation for a specific player."""
    print(f"\n🎲 Simulating Elo calculation for {player_name}...")
    
    matches = PlayerMatch.objects.filter(player_name=player_name).order_by('date')
    
    if not matches.exists():
        print("❌ No matches found")
        return None
    
    def calculate_elo_change(points, goals, assists, minutes_played):
        """Calculate Elo change based on performance."""
        # Minutes bonus
        if minutes_played >= 90:
            minutes_bonus = 2
        elif minutes_played >= 60:
            minutes_bonus = 1
        elif minutes_played == 0:
            minutes_bonus = -2
        else:
            minutes_bonus = 0
        
        # Performance points
        performance_points = points * 2 + goals * 5 + assists * 3 + minutes_bonus
        
        # Cap the Elo change
        return max(-30, min(30, performance_points))
    
    # Start with base Elo
    current_elo = 1200.0
    print(f"   📈 Starting Elo: {current_elo}")
    
    match_count = 0
    significant_changes = []
    
    for match in matches:
        elo_change = calculate_elo_change(
            match.points, match.goals, match.assists, match.minutes_played
        )
        new_elo = current_elo + elo_change
        
        # Track significant changes
        if abs(elo_change) >= 20:
            significant_changes.append({
                'date': match.date,
                'opponent': match.opponent,
                'change': elo_change,
                'new_elo': new_elo,
                'performance': f"{match.points}pts, {match.goals}G, {match.assists}A"
            })
        
        current_elo = new_elo
        match_count += 1
    
    print(f"   📊 Final Elo: {current_elo:.1f}")
    print(f"   📈 Total change: {current_elo - 1200:.1f}")
    print(f"   🎮 Matches processed: {match_count}")
    
    # Show significant Elo changes
    if significant_changes:
        print(f"\n   🔥 Significant Elo changes (±20):")
        for change in significant_changes[-10:]:  # Show last 10
            print(f"      {change['date']}: vs {change['opponent']} ({change['performance']}) → {change['change']:+.1f} → {change['new_elo']:.1f}")
    
    return current_elo


async def test_ultra_optimized_for_player(player_name):
    """Test the ultra-optimized function specifically for one player."""
    print(f"\n🚀 Testing ultra-optimized calculation for {player_name}...")
    
    try:
        from ultra_optimized_elo import ultra_optimized_recalculate_elos
        
        # Get the exact player name for filtering
        exact_matches = PlayerMatch.objects.filter(player_name=player_name)
        if not exact_matches.exists():
            print("❌ Player not found for ultra-optimized test")
            return
        
        # Run ultra-optimized for just this player would require modifying the function
        # For now, let's run it for a small batch including this player
        print("   Running ultra-optimized calculation for small batch...")
        
        # Get a few players including our target
        player_names = PlayerMatch.objects.values_list('player_name', flat=True).distinct()
        target_players = [name for name in player_names if player_name.lower() in name.lower()][:3]
        
        if target_players:
            print(f"   Testing with players: {target_players}")
            # For now, test with limited players
            result = await ultra_optimized_recalculate_elos(max_players=5, batch_size=5)
            print(f"   ✅ Ultra-optimized result: {result}")
        
    except Exception as e:
        print(f"   ❌ Error in ultra-optimized test: {e}")


def check_database_constraints():
    """Check database constraints for duplicate dates."""
    print("\n🛡️ Checking database constraints...")
    
    # Check if there are any violations of unique_together constraint
    try:
        # This query will find duplicate combinations
        from django.db import connection
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT player_name, date, opponent, COUNT(*) as count
                FROM player_matches 
                GROUP BY player_name, date, opponent
                HAVING COUNT(*) > 1
                ORDER BY count DESC
            """)
            
            duplicates = cursor.fetchall()
            
            if duplicates:
                print(f"❌ Found {len(duplicates)} constraint violations:")
                for player_name, date, opponent, count in duplicates[:10]:
                    print(f"   {player_name} vs {opponent} on {date}: {count} records")
            else:
                print("✅ No constraint violations found")
                
    except Exception as e:
        print(f"❌ Error checking constraints: {e}")


def main():
    """Main test function."""
    print("="*60)
    print("🧪 VICTOR GYÖKERES ELO TEST & DUPLICATE DATE VALIDATION")
    print("="*60)
    
    # 1. Find Victor Gyökeres
    player_name = find_gyokeres()
    
    if player_name:
        # 2. Check for duplicate dates
        duplicates = check_duplicate_dates(player_name)
        
        # 3. Analyze performance
        analyze_player_performance(player_name)
        
        # 4. Simulate Elo calculation
        final_elo = simulate_elo_calculation(player_name)
        
        # 5. Test ultra-optimized function
        asyncio.run(test_ultra_optimized_for_player(player_name))
        
        # 6. Expected vs Actual
        print(f"\n🎯 FINAL ASSESSMENT:")
        print(f"   Expected Elo: ~2800")
        print(f"   Calculated Elo: {final_elo:.1f}")
        if final_elo and abs(final_elo - 2800) < 200:
            print(f"   ✅ Elo is within reasonable range!")
        else:
            print(f"   ⚠️ Elo differs significantly from expected")
        
        if duplicates:
            print(f"   ❌ Found {len(duplicates)} dates with multiple matches")
        else:
            print(f"   ✅ No duplicate dates found")
    
    # 7. Check overall database constraints
    check_database_constraints()
    
    print("\n" + "="*60)
    print("🏁 TEST COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()