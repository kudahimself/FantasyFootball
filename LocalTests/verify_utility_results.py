#!/usr/bin/env python3
"""
Quick verification script to check specific player Elo ratings after using the utility module.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')
django.setup()

from MyApi.models import Player, EloCalculation

def verify_top_players():
    """Verify that top players have reasonable Elo ratings."""
    
    print("🔍 Verifying top player Elo ratings after utility module recalculation")
    print("=" * 80)
    
    # Get current week
    current_week = 4
    
    # Get top 10 players by Elo
    top_players = Player.objects.filter(week=current_week).order_by('-elo')[:10]
    
    print(f"📊 Top 10 Players (Week {current_week}):")
    print(f"{'Rank':<4} {'Player Name':<30} {'Position':<12} {'Elo':<8} {'Cost':<6}")
    print("-" * 70)
    
    for i, player in enumerate(top_players, 1):
        print(f"{i:<4} {player.name:<30} {player.position:<12} {player.elo:<8.1f} £{player.cost:<6.1f}M")
    
    print("\n" + "=" * 80)
    
    # Check specific players we've been tracking
    test_players = [
        "Viktor Gyökeres",
        "Mohamed Salah",
        "Erling Haaland",
        "Bukayo Saka",
        "Cole Palmer"
    ]
    
    print("🎯 Specific Player Verification:")
    print(f"{'Player Name':<25} {'Elo':<8} {'Cost':<8} {'Status'}")
    print("-" * 50)
    
    for player_name in test_players:
        try:
            player = Player.objects.get(name=player_name, week=current_week)
            status = "✅ Found"
            print(f"{player_name:<25} {player.elo:<8.1f} £{player.cost:<6.1f}M {status}")
        except Player.DoesNotExist:
            print(f"{player_name:<25} {'N/A':<8} {'N/A':<8} ❌ Not found")
    
    print("\n" + "=" * 80)
    
    # Check EloCalculation records
    elo_calcs = EloCalculation.objects.filter(week=current_week).order_by('-elo')[:5]
    
    print("📈 EloCalculation Records (Top 5):")
    print(f"{'Player Name':<25} {'Elo':<8} {'Change':<8} {'Matches'}")
    print("-" * 50)
    
    for calc in elo_calcs:
        print(f"{calc.player_name:<25} {calc.elo:<8.1f} {calc.elo_change:<8.1f} {calc.matches_played}")
    
    print("\n🎉 Verification complete!")

if __name__ == "__main__":
    verify_top_players()