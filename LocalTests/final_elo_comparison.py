#!/usr/bin/env python3
"""
Final comprehensive comparison of all Elo calculation methods.
"""

import time
import asyncio
from typing import Dict, Any

async def test_all_methods():
    """Test all Elo calculation methods and compare performance."""
    print("=" * 80)
    print("COMPREHENSIVE ELO CALCULATION PERFORMANCE COMPARISON")
    print("=" * 80)
    
    test_players = 10  # Test with 10 players for fair comparison
    
    results = {}
    
    # Test 1: Ultra-optimized version
    print(f"\n1️⃣  TESTING ULTRA-OPTIMIZED VERSION ({test_players} players)")
    print("-" * 60)
    try:
        from ultra_optimized_elo import ultra_optimized_recalculate_elos
        
        start_time = time.time()
        result = await ultra_optimized_recalculate_elos(max_players=test_players, batch_size=test_players)
        end_time = time.time()
        
        if 'error' not in result:
            duration = end_time - start_time
            rate = result['updated_count'] / duration
            results['ultra_optimized'] = {
                'time': duration,
                'rate': rate,
                'updated': result['updated_count'],
                'status': 'success'
            }
            print(f"✅ Success: {result['updated_count']} players updated")
            print(f"⚡ Time: {duration:.4f} seconds")
            print(f"📊 Rate: {rate:.2f} players/second")
        else:
            print(f"❌ Error: {result['error']}")
            results['ultra_optimized'] = {'status': 'error', 'error': result['error']}
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        results['ultra_optimized'] = {'status': 'exception', 'error': str(e)}
    
    # Test 2: Database-optimized version
    print(f"\n2️⃣  TESTING DATABASE-OPTIMIZED VERSION ({test_players} players)")
    print("-" * 60)
    try:
        from database_optimized_elo import database_optimized_recalculate_elos
        
        start_time = time.time()
        result = await database_optimized_recalculate_elos(max_players=test_players)
        end_time = time.time()
        
        if 'error' not in result:
            duration = end_time - start_time
            rate = result['updated_count'] / duration
            results['database_optimized'] = {
                'time': duration,
                'rate': rate,
                'updated': result['updated_count'],
                'status': 'success'
            }
            print(f"✅ Success: {result['updated_count']} players updated")
            print(f"⚡ Time: {duration:.4f} seconds")
            print(f"📊 Rate: {rate:.2f} players/second")
        else:
            print(f"❌ Error: {result['error']}")
            results['database_optimized'] = {'status': 'error', 'error': result['error']}
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        results['database_optimized'] = {'status': 'exception', 'error': str(e)}
    
    # Test 3: Original method (using the recalculate function from views)
    print(f"\n3️⃣  TESTING ORIGINAL METHOD ({test_players} players)")
    print("-" * 60)
    try:
        import os
        import django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')
        django.setup()
        
        from asgiref.sync import sync_to_async
        from MyApi.models import Player
        
        # Get first N players
        players = await sync_to_async(list)(
            Player.objects.filter(week=4).order_by('name')[:test_players]
        )
        
        # Import and test original recalculate function
        from MyApp.views import recalculate_player_elos
        
        start_time = time.time()
        # Call original function
        result = await sync_to_async(recalculate_player_elos)(None)  # Pass None as request
        end_time = time.time()
        
        # Check result
        if hasattr(result, 'content'):
            import json
            content = json.loads(result.content.decode())
            if content.get('success'):
                duration = end_time - start_time
                updated_count = content.get('updated_count', 0)
                rate = updated_count / duration if duration > 0 else 0
                results['original'] = {
                    'time': duration,
                    'rate': rate,
                    'updated': updated_count,
                    'status': 'success'
                }
                print(f"✅ Success: {updated_count} players updated")
                print(f"⚡ Time: {duration:.4f} seconds")
                print(f"📊 Rate: {rate:.2f} players/second")
            else:
                error_msg = content.get('error', 'Unknown error')
                print(f"❌ Error: {error_msg}")
                results['original'] = {'status': 'error', 'error': error_msg}
        else:
            print(f"❌ Unexpected result type")
            results['original'] = {'status': 'error', 'error': 'Unexpected result type'}
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        results['original'] = {'status': 'exception', 'error': str(e)}
    
    # Print summary
    print("\n" + "=" * 80)
    print("📊 PERFORMANCE SUMMARY")
    print("=" * 80)
    
    successful_results = {k: v for k, v in results.items() if v.get('status') == 'success'}
    
    if successful_results:
        print(f"\n{'Method':<20} {'Time (s)':<12} {'Rate (p/s)':<12} {'Players':<10} {'Speedup':<10}")
        print("-" * 70)
        
        # Find baseline (original method time)
        baseline_time = None
        if 'original' in successful_results:
            baseline_time = successful_results['original']['time']
        elif successful_results:
            # Use the slowest time as baseline
            baseline_time = max(v['time'] for v in successful_results.values())
        
        for method, data in successful_results.items():
            speedup = f"{baseline_time / data['time']:.2f}x" if baseline_time else "N/A"
            print(f"{method:<20} {data['time']:<12.4f} {data['rate']:<12.2f} {data['updated']:<10} {speedup:<10}")
        
        # Find the fastest method
        if successful_results:
            fastest = min(successful_results.items(), key=lambda x: x[1]['time'])
            print(f"\n🏆 FASTEST METHOD: {fastest[0].upper()}")
            print(f"   ⚡ Time: {fastest[1]['time']:.4f} seconds")
            print(f"   📊 Rate: {fastest[1]['rate']:.2f} players/second")
            
            if baseline_time and fastest[1]['time'] < baseline_time:
                improvement = baseline_time / fastest[1]['time']
                print(f"   🚀 Performance improvement: {improvement:.2f}x faster")
    
    else:
        print("\n❌ No successful tests to compare")
    
    # Print failed tests
    failed_results = {k: v for k, v in results.items() if v.get('status') != 'success'}
    if failed_results:
        print(f"\n❌ FAILED TESTS:")
        for method, data in failed_results.items():
            print(f"   {method}: {data.get('error', 'Unknown error')}")
    
    return results


if __name__ == "__main__":
    results = asyncio.run(test_all_methods())
    
    print(f"\n" + "=" * 80)
    print("🎯 CONCLUSION")
    print("=" * 80)
    
    successful_results = {k: v for k, v in results.items() if v.get('status') == 'success'}
    
    if successful_results:
        fastest = min(successful_results.items(), key=lambda x: x[1]['time'])
        print(f"\n✅ Optimization successful!")
        print(f"🏆 Best method: {fastest[0]}")
        print(f"⚡ Performance: {fastest[1]['rate']:.2f} players/second")
        print(f"💡 The ultra-optimized version uses Django's bulk_update for maximum database performance!")
    else:
        print(f"\n❌ All optimization attempts failed. Need to debug further.")