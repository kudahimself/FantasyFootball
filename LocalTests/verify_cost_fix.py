#!/usr/bin/env python3
"""
Quick verification that the cost issue has been resolved.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')
django.setup()

from MyApi.models import Player

def verify_costs():
    """Check that costs have been updated correctly."""
    
    print("🔍 Cost Update Verification")
    print("=" * 50)
    
    test_players = [
        "Viktor Gyökeres",
        "Mohamed Salah", 
        "Erling Haaland",
        "Bukayo Saka",
        "Cole Palmer"
    ]
    
    current_week = 4
    
    print(f"{'Player Name':<25} {'Cost':<10} {'Status'}")
    print("-" * 50)
    
    for player_name in test_players:
        try:
            player = Player.objects.get(name=player_name, week=current_week)
            cost = player.cost
            
            # Check if cost looks reasonable (not the old calculated value)
            if player_name == "Viktor Gyökeres":
                status = "✅ Fixed" if cost < 12.0 else "❌ Still wrong"
            elif player_name == "Cole Palmer":
                status = "✅ Fixed" if cost > 8.0 else "❌ Still wrong"
            elif player_name == "Bukayo Saka":
                status = "✅ Fixed" if cost > 8.0 else "❌ Still wrong"
            else:
                # For others, just check it's not 15.0 (the max calculated value)
                status = "✅ Updated" if cost < 15.0 else "❌ Still calculated"
            
            print(f"{player_name:<25} £{cost:.1f}m     {status}")
            
        except Player.DoesNotExist:
            print(f"{player_name:<25} Not found  ❌")
    
    # Check top players to see if they look reasonable
    print(f"\n📊 Top 5 Players by Elo (Cost Check)")
    print("-" * 50)
    
    top_players = Player.objects.filter(week=current_week).order_by('-elo')[:5]
    
    for player in top_players:
        # Check if cost is reasonable vs calculated value
        calculated_cost = max(4.0, min(15.0, 4.0 + (player.elo - 1200) / 100))
        is_fpl_cost = abs(player.cost - calculated_cost) > 1.0
        status = "✅ FPL Cost" if is_fpl_cost else "⚠️  Calculated"
        
        print(f"{player.name:<25} Elo: {player.elo:<7.1f} Cost: £{player.cost:.1f}m  {status}")

if __name__ == "__main__":
    verify_costs()