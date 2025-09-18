#!/usr/bin/env python3
"""
Debug the Elo recalculation logging issue to find where 58160 is coming from.
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')
django.setup()

from MyApi.models import PlayerMatch


def debug_player_counts():
    """Debug where the 58160 count is coming from."""
    print("🔍 DEBUGGING ELO RECALCULATION COUNTS")
    print("="*50)
    
    # Count total PlayerMatch records
    total_matches = PlayerMatch.objects.count()
    print(f"Total PlayerMatch records: {total_matches}")
    
    # Count unique players
    unique_players = PlayerMatch.objects.values_list('player_name', flat=True).distinct().count()
    print(f"Unique players: {unique_players}")
    
    # Test different query methods
    print(f"\n🔍 Testing different query methods:")
    
    # Method 1: values_list().distinct()
    player_names_1 = PlayerMatch.objects.values_list('player_name', flat=True).distinct()
    count_1 = len(list(player_names_1))
    print(f"Method 1 - values_list().distinct(): {count_1} players")
    
    # Method 2: Using .distinct().count()
    count_2 = PlayerMatch.objects.values_list('player_name', flat=True).distinct().count()
    print(f"Method 2 - .distinct().count(): {count_2} players")
    
    # Method 3: Check if there's a bug with slicing
    all_names = PlayerMatch.objects.values_list('player_name', flat=True).distinct()
    print(f"Method 3 - All unique names count: {all_names.count()}")
    
    # Check if slicing is causing issues
    first_50 = PlayerMatch.objects.values_list('player_name', flat=True).distinct()[:50]
    first_50_list = list(first_50)
    print(f"Method 4 - First 50 players slice: {len(first_50_list)} players")
    
    # Check if someone is accidentally using all matches instead of unique players
    print(f"\n⚠️ POTENTIAL BUGS:")
    if total_matches == 58160:
        print(f"   • 58160 matches found - this might be what's being counted incorrectly")
    
    if unique_players != count_1:
        print(f"   • Mismatch between .count() and len(list()) methods")
    
    print(f"\n✅ CORRECT COUNTS:")
    print(f"   • Total matches: {total_matches}")
    print(f"   • Unique players: {unique_players}")
    print(f"   • Expected log: 'Starting ... recalculation for {unique_players} players...'")


def test_ultra_optimized_logging():
    """Test the ultra-optimized function logging specifically."""
    print(f"\n🚀 Testing Ultra-Optimized Function Logging")
    print("="*50)
    
    try:
        import asyncio
        from ultra_optimized_elo import ultra_optimized_recalculate_elos
        
        # Test with max_players to see if logging is correct
        print("Testing with max_players=5...")
        result = asyncio.run(ultra_optimized_recalculate_elos(max_players=5, batch_size=5))
        print(f"Result: {result}")
        
        print(f"\nTesting with max_players=None (all players)...")
        print("This should show 596 players, not 58160...")
        
        # Just test the counting logic without full execution
        async def test_count_only():
            from asgiref.sync import sync_to_async
            player_names_query = PlayerMatch.objects.values_list('player_name', flat=True).distinct()
            player_names = await sync_to_async(list)(player_names_query)
            total_players = len(player_names)
            print(f"Ultra-optimized count: {total_players} players")
            return total_players
        
        count = asyncio.run(test_count_only())
        
        if count == 58160:
            print("❌ FOUND THE BUG: Ultra-optimized is counting matches, not players!")
        elif count == 596:
            print("✅ Ultra-optimized counting is correct")
        else:
            print(f"⚠️ Unexpected count: {count}")
            
    except Exception as e:
        print(f"❌ Error testing ultra-optimized: {e}")


def check_all_functions():
    """Check all recalculation functions for correct counting."""
    print(f"\n🔍 Checking All Functions")
    print("="*50)
    
    # Expected count
    expected_count = PlayerMatch.objects.values_list('player_name', flat=True).distinct().count()
    print(f"Expected player count: {expected_count}")
    
    functions_to_check = [
        "recalculate_player_elos",
        "recalculate_player_elos_optimized", 
        "recalculate_player_elos_ultra_optimized"
    ]
    
    print(f"\n📝 Functions that should log '{expected_count} players':")
    for func_name in functions_to_check:
        print(f"   • {func_name}")
    
    print(f"\n⚠️ If you see '58160 players' in logs, check which endpoint you're calling:")
    print(f"   • /api/recalculate_elos/ - Original function")
    print(f"   • /api/recalculate_elos_optimized/ - NumPy optimized function") 
    print(f"   • /api/recalculate_elos_ultra_optimized/ - Ultra optimized function")


def main():
    """Main debug function."""
    debug_player_counts()
    test_ultra_optimized_logging()
    check_all_functions()
    
    print(f"\n" + "="*50)
    print("🎯 SOLUTION:")
    print("If you're still seeing '58160 players' in logs:")
    print("1. Make sure you're calling the RIGHT endpoint")
    print("2. Check that all functions use .distinct() properly")
    print("3. Verify you're not accidentally counting matches instead of players")
    print("="*50)


if __name__ == "__main__":
    main()