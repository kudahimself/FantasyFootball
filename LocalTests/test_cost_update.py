#!/usr/bin/env python3
"""
Test the FPL cost update functionality in the utility module.
"""

import os
import sys
import django
import asyncio

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')
django.setup()

from MyApi.models import Player
from MyApi.utils.fpl_cost_updater import get_player_cost_from_fpl, update_all_player_costs_from_fpl, check_player_costs_vs_fpl

async def test_individual_cost_lookup():
    """Test getting individual player costs from FPL."""
    
    print("🧪 Testing Individual FPL Cost Lookup")
    print("=" * 50)
    
    test_players = [
        "Viktor Gyökeres",
        "Mohamed Salah", 
        "Erling Haaland",
        "Bukayo Saka",
        "Cole Palmer"
    ]
    
    # Use the new comparison function
    result = await check_player_costs_vs_fpl(test_players, current_week=4)
    
    if result['success']:
        print(f"{'Player Name':<20} {'DB Cost':<10} {'FPL Cost':<10} {'Diff':<8} {'Status'}")
        print("-" * 60)
        
        for player_result in result['results']:
            name = player_result['player_name']
            
            if player_result['status'] == 'success':
                db_cost = f"£{player_result['db_cost']:.1f}m"
                fpl_cost = f"£{player_result['fpl_cost']:.1f}m"
                diff = f"£{abs(player_result['difference']):.1f}m"
                status = "✅ Match" if player_result['match'] else "❌ Mismatch"
            elif player_result['status'] == 'fpl_not_found':
                db_cost = f"£{player_result['db_cost']:.1f}m" if player_result['db_cost'] else "N/A"
                fpl_cost = "Not found"
                diff = "N/A"
                status = "❌ FPL N/F"
            elif player_result['status'] == 'player_not_found':
                db_cost = "Not found"
                fpl_cost = "N/A"
                diff = "N/A"
                status = "❌ DB N/F"
            else:
                db_cost = "Error"
                fpl_cost = "Error"
                diff = "N/A"
                status = "❌ Error"
            
            print(f"{name:<20} {db_cost:<10} {fpl_cost:<10} {diff:<8} {status}")
    else:
        print(f"❌ Comparison failed: {result.get('error')}")

async def test_bulk_cost_update():
    """Test the bulk cost update function."""
    
    print("\n" + "=" * 50)
    print("🏷️  Testing Bulk FPL Cost Update")
    print("=" * 50)
    
    # Run the bulk update
    result = await update_all_player_costs_from_fpl(current_week=4)
    
    if result.get('success'):
        print(f"\n📊 Update Summary:")
        print(f"   Total players: {result['total_players']}")
        print(f"   Successful updates: {result['successful_updates']}")
        print(f"   Failed updates: {result['failed_updates']}")
        print(f"   Duration: {result['duration']:.2f} seconds")
        
        significant_changes = [c for c in result['cost_changes'] if abs(c['change']) > 0.5]
        if significant_changes:
            print(f"\n💰 Significant Cost Changes:")
            for change in significant_changes[:10]:  # Show first 10
                print(f"   {change['player']}: £{change['old_cost']:.1f}m → £{change['new_cost']:.1f}m")
    else:
        print(f"❌ Bulk update failed: {result.get('error')}")

async def verify_gyokeres_cost():
    """Specifically check Viktor Gyökeres cost after update."""
    
    print("\n" + "=" * 50)
    print("🎯 Verifying Viktor Gyökeres Cost")
    print("=" * 50)
    
    try:
        from asgiref.sync import sync_to_async
        
        player = await sync_to_async(Player.objects.get)(name="Viktor Gyökeres", week=4)
        db_cost = player.cost
        fpl_cost = await get_player_cost_from_fpl("Viktor Gyökeres")
        
        print(f"Viktor Gyökeres:")
        print(f"  Database cost: £{db_cost:.1f}m")
        print(f"  FPL API cost:  £{fpl_cost:.1f}m" if fpl_cost else "  FPL API cost:  Not found")
        
        if fpl_cost and abs(db_cost - fpl_cost) < 0.1:
            print("  ✅ Costs match - Issue resolved!")
        else:
            print(f"  ❌ Still mismatch - Difference: £{abs(db_cost - fpl_cost):.1f}m")
            
    except Exception as e:
        print(f"❌ Error: {e}")

async def main():
    """Run all cost update tests."""
    await test_individual_cost_lookup()
    await test_bulk_cost_update() 
    await verify_gyokeres_cost()

if __name__ == "__main__":
    asyncio.run(main())