#!/usr/bin/env python3
"""
Test the fixed ultra-optimized Elo calculation with constraint handling.
"""

import os
import django
import asyncio

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')
django.setup()

from MyApi.models import EloCalculation


async def test_constraint_fix():
    """Test that the constraint fix works properly."""
    print("🧪 Testing Constraint Fix for Elo Calculations")
    print("=" * 50)
    
    try:
        from ultra_optimized_elo import ultra_optimized_recalculate_elos
        
        # First, check existing EloCalculation records
        existing_count = await sync_to_async(EloCalculation.objects.count)()
        print(f"📊 Existing EloCalculation records: {existing_count}")
        
        # Test with a small number of players first
        print("\n🔧 Testing with 5 players...")
        result1 = await ultra_optimized_recalculate_elos(max_players=5, batch_size=5)
        
        if 'error' in result1:
            print(f"❌ First test failed: {result1['error']}")
            return
        else:
            print(f"✅ First test passed: {result1}")
        
        # Check how many records we have now
        new_count = await sync_to_async(EloCalculation.objects.count)()
        print(f"📊 EloCalculation records after first run: {new_count}")
        
        # Test running again (should not cause constraint violations)
        print("\n🔧 Testing duplicate run (should not fail)...")
        result2 = await ultra_optimized_recalculate_elos(max_players=5, batch_size=5)
        
        if 'error' in result2:
            print(f"❌ Duplicate test failed: {result2['error']}")
            return
        else:
            print(f"✅ Duplicate test passed: {result2}")
        
        # Check count again (should be the same since we're updating, not creating new)
        final_count = await sync_to_async(EloCalculation.objects.count)()
        print(f"📊 EloCalculation records after duplicate run: {final_count}")
        
        if final_count == new_count:
            print("✅ Constraint handling working correctly - no duplicate records created")
        else:
            print(f"⚠️ Warning: Record count changed from {new_count} to {final_count}")
        
        # Now test with all players
        print(f"\n🚀 Testing with ALL {result1.get('total_players', 'unknown')} players...")
        result3 = await ultra_optimized_recalculate_elos()
        
        if 'error' in result3:
            print(f"❌ Full test failed: {result3['error']}")
        else:
            print(f"✅ Full test PASSED: {result3}")
            print(f"🎉 Successfully calculated Elo for {result3['updated_count']} players!")
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()


def check_elo_results():
    """Check the results of Elo calculations."""
    print("\n📊 Checking Elo Calculation Results")
    print("=" * 40)
    
    try:
        # Get top 10 players by Elo
        top_players = EloCalculation.objects.filter(
            week=4, season="2024-2025"
        ).order_by('-elo_rating')[:10]
        
        print("🏆 Top 10 Players by Elo:")
        for i, calc in enumerate(top_players, 1):
            print(f"  {i:2d}. {calc.player_name}: {calc.elo_rating:.1f} (change: {calc.elo_change:+.1f})")
        
        # Get some specific players we tested
        test_players = ['Viktor Gyökeres', 'Martin Ødegaard']
        print(f"\n🎯 Specific Test Players:")
        for player_name in test_players:
            try:
                calc = EloCalculation.objects.get(
                    player_name=player_name, week=4, season="2024-2025"
                )
                print(f"  {player_name}: {calc.elo_rating:.1f} (change: {calc.elo_change:+.1f}, matches: {calc.matches_played})")
            except EloCalculation.DoesNotExist:
                print(f"  {player_name}: No record found")
        
        # Statistics
        total_calcs = EloCalculation.objects.filter(week=4, season="2024-2025").count()
        avg_elo = EloCalculation.objects.filter(week=4, season="2024-2025").aggregate(
            avg_elo=models.Avg('elo_rating')
        )['avg_elo']
        
        print(f"\n📈 Statistics:")
        print(f"  Total players: {total_calcs}")
        print(f"  Average Elo: {avg_elo:.1f}")
        
    except Exception as e:
        print(f"❌ Error checking results: {e}")


async def main():
    """Main test function."""
    print("🧪 ULTRA-OPTIMIZED ELO CALCULATION TEST")
    print("=" * 60)
    print("Testing constraint fix and full player calculation")
    print("=" * 60)
    
    await test_constraint_fix()
    check_elo_results()
    
    print("\n" + "=" * 60)
    print("🏁 TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    from asgiref.sync import sync_to_async
    from django.db import models
    
    asyncio.run(main())