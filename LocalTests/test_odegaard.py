#!/usr/bin/env python3
"""
Test Martin Ødegaard Elo calculation and performance analysis.
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


def find_odegaard():
    """Find Martin Ødegaard in the database with various spellings."""
    print("🔍 Searching for Martin Ødegaard...")
    
    # Try different spellings
    search_terms = [
        'Martin Ødegaard',
        'Martin Odegaard', 
        'Ødegaard',
        'Odegaard'
    ]
    
    for name in search_terms:
        matches = PlayerMatch.objects.filter(player_name=name)
        if matches.exists():
            print(f"✅ Found: {name}")
            return name
    
    # Fallback - search for any player with "degaard" in name
    odegaard_matches = PlayerMatch.objects.filter(player_name__icontains='degaard')
    if odegaard_matches.exists():
        unique_names = list(odegaard_matches.values_list('player_name', flat=True).distinct())
        print(f"Found players with 'degaard': {unique_names}")
        return unique_names[0]
    
    print("❌ Martin Ødegaard not found in database")
    return None


def analyze_odegaard_performance(player_name):
    """Analyze Ødegaard's performance data."""
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
    print(f"   🎯 Goals per match: {total_goals/total_matches:.2f}")
    print(f"   🎯 Assists per match: {total_assists/total_matches:.2f}")
    
    # Analyze by season/competition
    competitions = matches.values('competition').distinct()
    print(f"\n   🏆 Competitions played:")
    for comp in competitions:
        comp_name = comp['competition']
        comp_matches = matches.filter(competition=comp_name)
        comp_goals = sum(match.goals for match in comp_matches)
        comp_assists = sum(match.assists for match in comp_matches)
        comp_points = sum(match.points for match in comp_matches)
        print(f"      {comp_name}: {comp_matches.count()} matches, {comp_goals}G, {comp_assists}A, {comp_points}pts")
    
    # Show best performances
    best_matches = matches.order_by('-points')[:10]
    print(f"\n   🏆 Top 10 performances:")
    for i, match in enumerate(best_matches, 1):
        print(f"      {i:2d}. {match.date}: vs {match.opponent} - {match.points}pts ({match.goals}G, {match.assists}A) [{match.competition}]")
    
    # Show worst performances (0 points)
    worst_matches = matches.filter(points=0).order_by('date')
    if worst_matches.exists():
        print(f"\n   💔 Zero-point matches ({worst_matches.count()}):")
        for match in worst_matches[:5]:
            print(f"      {match.date}: vs {match.opponent} - {match.points}pts ({match.goals}G, {match.assists}A) [{match.competition}]")
        if worst_matches.count() > 5:
            print(f"      ... and {worst_matches.count() - 5} more")
    
    # Show recent form
    recent_matches = matches.order_by('-date')[:10]
    print(f"\n   📅 Recent 10 matches:")
    for match in recent_matches:
        print(f"      {match.date}: vs {match.opponent} - {match.points}pts ({match.goals}G, {match.assists}A)")


def simulate_odegaard_elo(player_name):
    """Simulate Elo calculation for Ødegaard."""
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
    elo_history = []
    
    for match in matches:
        elo_change = calculate_elo_change(
            match.points, match.goals, match.assists, match.minutes_played
        )
        new_elo = current_elo + elo_change
        
        # Track all changes for analysis
        elo_history.append({
            'date': match.date,
            'opponent': match.opponent,
            'elo_before': current_elo,
            'elo_change': elo_change,
            'elo_after': new_elo,
            'performance': f"{match.points}pts, {match.goals}G, {match.assists}A",
            'competition': match.competition
        })
        
        # Track significant changes
        if abs(elo_change) >= 15:
            significant_changes.append(elo_history[-1])
        
        current_elo = new_elo
        match_count += 1
    
    print(f"   📊 Final Elo: {current_elo:.1f}")
    print(f"   📈 Total change: {current_elo - 1200:.1f}")
    print(f"   🎮 Matches processed: {match_count}")
    
    # Calculate Elo statistics
    max_elo = max(h['elo_after'] for h in elo_history)
    min_elo = min(h['elo_after'] for h in elo_history)
    print(f"   📈 Peak Elo: {max_elo:.1f}")
    print(f"   📉 Lowest Elo: {min_elo:.1f}")
    print(f"   📊 Elo Range: {max_elo - min_elo:.1f}")
    
    # Show significant Elo changes
    if significant_changes:
        print(f"\n   🔥 Significant Elo changes (±15):")
        for change in significant_changes[-15:]:  # Show last 15
            print(f"      {change['date']}: vs {change['opponent']} ({change['performance']}) → {change['elo_change']:+.1f} → {change['elo_after']:.1f}")
    
    # Show Elo progression over time
    print(f"\n   📈 Elo progression (every 20 matches):")
    for i in range(0, len(elo_history), 20):
        h = elo_history[i]
        print(f"      Match {i+1:3d} ({h['date']}): {h['elo_after']:.1f}")
    
    return current_elo


def compare_with_gyokeres():
    """Compare Ødegaard with Viktor Gyökeres."""
    print(f"\n⚖️ Comparison with Viktor Gyökeres...")
    
    # Get Viktor Gyökeres data
    viktor_matches = PlayerMatch.objects.filter(player_name='Viktor Gyökeres')
    odegaard_matches = PlayerMatch.objects.filter(player_name__icontains='degaard')
    
    if not odegaard_matches.exists():
        print("❌ Ødegaard not found for comparison")
        return
    
    odegaard_name = odegaard_matches.first().player_name
    
    print(f"   📊 Match Count:")
    print(f"      Ødegaard: {odegaard_matches.count()}")
    print(f"      Gyökeres: {viktor_matches.count()}")
    
    print(f"   📊 Goals:")
    odegaard_goals = sum(match.goals for match in odegaard_matches)
    viktor_goals = sum(match.goals for match in viktor_matches)
    print(f"      Ødegaard: {odegaard_goals}")
    print(f"      Gyökeres: {viktor_goals}")
    
    print(f"   📊 Assists:")
    odegaard_assists = sum(match.assists for match in odegaard_matches)
    viktor_assists = sum(match.assists for match in viktor_matches)
    print(f"      Ødegaard: {odegaard_assists}")
    print(f"      Gyökeres: {viktor_assists}")
    
    print(f"   📊 Fantasy Points:")
    odegaard_points = sum(match.points for match in odegaard_matches)
    viktor_points = sum(match.points for match in viktor_matches)
    print(f"      Ødegaard: {odegaard_points}")
    print(f"      Gyökeres: {viktor_points}")
    
    print(f"   📊 Per Match Averages:")
    if odegaard_matches.count() > 0:
        print(f"      Ødegaard: {odegaard_points/odegaard_matches.count():.2f} pts/match")
    if viktor_matches.count() > 0:
        print(f"      Gyökeres: {viktor_points/viktor_matches.count():.2f} pts/match")


def main():
    """Main test function."""
    print("="*60)
    print("🧪 MARTIN ØDEGAARD ELO TEST & PERFORMANCE ANALYSIS")
    print("="*60)
    
    # 1. Find Martin Ødegaard
    player_name = find_odegaard()
    
    if player_name:
        # 2. Analyze performance
        analyze_odegaard_performance(player_name)
        
        # 3. Simulate Elo calculation
        final_elo = simulate_odegaard_elo(player_name)
        
        # 4. Compare with Gyökeres
        compare_with_gyokeres()
        
        # 5. Final assessment
        print(f"\n🎯 FINAL ASSESSMENT:")
        print(f"   Player: {player_name}")
        print(f"   Final Elo: {final_elo:.1f}")
        
        if final_elo:
            if final_elo > 2000:
                print(f"   🌟 Elite player (Elo > 2000)")
            elif final_elo > 1500:
                print(f"   ⭐ Strong player (Elo > 1500)")
            elif final_elo > 1200:
                print(f"   📈 Above average (Elo > 1200)")
            else:
                print(f"   📉 Below average (Elo < 1200)")
        
    else:
        print("\n❌ Could not find Martin Ødegaard in database")
        
        # Show some midfielder examples
        print("\n🔍 Sample midfielders in database:")
        midfield_matches = PlayerMatch.objects.filter(
            player_name__icontains='martin'
        ).values_list('player_name', flat=True).distinct()[:10]
        
        for name in midfield_matches:
            print(f"   - {name}")
    
    print("\n" + "="*60)
    print("🏁 TEST COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()