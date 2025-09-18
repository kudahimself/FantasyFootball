#!/usr/bin/env python3
"""
Test calculating Elo for all players using the corrected ultra-optimized function.
"""

import os
import django
import asyncio
import time
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')
django.setup()

from MyApi.models import PlayerMatch, Player


async def test_all_players_elo():
    """Test the ultra-optimized Elo calculation for all players."""
    from asgiref.sync import sync_to_async
    
    print("🚀 TESTING ELO CALCULATION FOR ALL PLAYERS")
    print("=" * 60)
    
    # Get initial stats using sync_to_async
    total_matches = await sync_to_async(PlayerMatch.objects.count)()
    unique_players = await sync_to_async(
        PlayerMatch.objects.values_list('player_name', flat=True).distinct().count
    )()
    
    print(f"📊 Database Stats:")
    print(f"   • Total PlayerMatch records: {total_matches:,}")
    print(f"   • Unique players: {unique_players:,}")
    print(f"   • Average matches per player: {total_matches/unique_players:.1f}")
    
    print(f"\n⏰ Starting full Elo recalculation at {datetime.now().strftime('%H:%M:%S')}")
    
    try:
        from ultra_optimized_elo import ultra_optimized_recalculate_elos
        
        # Record start time
        start_time = time.time()
        
        # Run the ultra-optimized calculation for ALL players
        result = await ultra_optimized_recalculate_elos(
            max_players=None,  # Process all players
            batch_size=50      # Process in batches of 50
        )
        
        # Record end time
        end_time = time.time()
        total_time = end_time - start_time
        
        if 'error' in result:
            print(f"❌ Error: {result['error']}")
            return
        
        print(f"\n✅ SUCCESS!")
        print(f"   • Players processed: {result['updated_count']:,}")
        print(f"   • Total time: {total_time:.2f} seconds")
        print(f"   • Processing rate: {result['updated_count']/total_time:.2f} players/second")
        print(f"   • Current week: {result['week']}")
        print(f"   • Method: {result['method']}")
        
        # Get some sample results
        print(f"\n📊 Sample Results:")
        
        # Top 10 players by Elo
        top_players = await sync_to_async(list)(
            Player.objects.filter(week=result['week']).order_by('-elo')[:10]
        )
        print(f"\n🏆 Top 10 Players by Elo:")
        for i, player in enumerate(top_players, 1):
            print(f"   {i:2d}. {player.name:25s} - {player.elo:7.1f} ({player.position})")
        
        # Bottom 10 players by Elo  
        bottom_players = await sync_to_async(list)(
            Player.objects.filter(week=result['week']).order_by('elo')[:10]
        )
        print(f"\n📉 Bottom 10 Players by Elo:")
        for i, player in enumerate(bottom_players, 1):
            print(f"   {i:2d}. {player.name:25s} - {player.elo:7.1f} ({player.position})")
        
        # Check specific players we tested before
        print(f"\n🎯 Previously Tested Players:")
        test_players = ['Viktor Gyökeres', 'Martin Ødegaard']
        for player_name in test_players:
            try:
                player = await sync_to_async(Player.objects.get)(name=player_name, week=result['week'])
                print(f"   • {player_name:20s}: {player.elo:7.1f} Elo")
            except Player.DoesNotExist:
                print(f"   • {player_name:20s}: Not found")
        
        # Position averages
        print(f"\n📊 Average Elo by Position:")
        positions = ['Keeper', 'Defender', 'Midfielder', 'Attacker']
        for position in positions:
            players_in_pos = await sync_to_async(list)(
                Player.objects.filter(week=result['week'], position=position)
            )
            if players_in_pos:
                avg_elo = sum(p.elo for p in players_in_pos) / len(players_in_pos)
                print(f"   • {position:12s}: {avg_elo:7.1f} (count: {len(players_in_pos)})")
        
        return result
        
    except Exception as e:
        print(f"❌ Exception during calculation: {e}")
        import traceback
        traceback.print_exc()
        return None


async def check_data_consistency():
    """Check data consistency after Elo calculation."""
    from asgiref.sync import sync_to_async
    import django.db.models
    
    print(f"\n🔍 CHECKING DATA CONSISTENCY")
    print("=" * 40)
    
    try:
        # Check for missing elo_before_match values
        missing_before = await sync_to_async(
            PlayerMatch.objects.filter(elo_before_match__isnull=True).count
        )()
        print(f"   • Missing elo_before_match: {missing_before}")
        
        # Check for missing elo_after_match values  
        missing_after = await sync_to_async(
            PlayerMatch.objects.filter(elo_after_match__isnull=True).count
        )()
        print(f"   • Missing elo_after_match: {missing_after}")
        
        # Check Elo range
        total_matches = await sync_to_async(PlayerMatch.objects.count)()
        if total_matches > 0:
            min_elo_result = await sync_to_async(
                PlayerMatch.objects.aggregate
            )(min_elo=django.db.models.Min('elo_after_match'))
            max_elo_result = await sync_to_async(
                PlayerMatch.objects.aggregate
            )(max_elo=django.db.models.Max('elo_after_match'))
            
            min_elo = min_elo_result['min_elo']
            max_elo = max_elo_result['max_elo']
            print(f"   • Elo range: {min_elo:.1f} to {max_elo:.1f}")
        
        # Check for extreme Elo values (possible errors)
        extreme_low = await sync_to_async(
            PlayerMatch.objects.filter(elo_after_match__lt=500).count
        )()
        extreme_high = await sync_to_async(
            PlayerMatch.objects.filter(elo_after_match__gt=4000).count
        )()
        print(f"   • Extreme low Elo (<500): {extreme_low}")
        print(f"   • Extreme high Elo (>4000): {extreme_high}")
        
        if missing_before == 0 and missing_after == 0:
            print(f"   ✅ All Elo fields populated correctly")
        else:
            print(f"   ⚠️ Some Elo fields are missing")
            
    except Exception as e:
        print(f"   ❌ Error checking consistency: {e}")


async def main():
    """Main test function."""
    print("🧪 FULL ELO CALCULATION TEST")
    print("=" * 60)
    print("This will calculate Elo ratings for all players in the database")
    print("Using the corrected algorithm that allows players to lose Elo")
    print("=" * 60)
    
    # Run the full calculation
    result = await test_all_players_elo()
    
    if result:
        # Check data consistency
        await check_data_consistency()
        
        print(f"\n🎉 FULL ELO CALCULATION COMPLETE!")
        print(f"   • {result['updated_count']} players processed successfully")
        print(f"   • Algorithm: Proper Elo formula with league ratings")
        print(f"   • Players can gain AND lose Elo based on performance")
        print(f"   • Database optimized with bulk operations")
    else:
        print(f"\n❌ Elo calculation failed")
    
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())