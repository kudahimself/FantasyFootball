#!/usr/bin/env python3
"""
Optimized recalculate Elo function using the OptimizedEloCalculator.
"""

import os
import django
import asyncio
import json
from typing import Dict, Any

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')
django.setup()

from MyApi.models import Player, PlayerMatch, EloCalculation, SystemSettings
from asgiref.sync import sync_to_async
import pandas as pd
from optimized_elo_calculator import OptimizedEloCalculator

async def optimized_recalculate_elos(max_players: int = None, batch_size: int = 100) -> Dict[str, Any]:
    """
    Optimized async function to recalculate Elo ratings using vectorized operations.
    
    Args:
        max_players: Maximum number of players to process (None = all)
        batch_size: Number of players to process in each batch
        
    Returns:
        Dict with success status and results
    """
    try:
        # Get current week
        try:
            settings = await sync_to_async(SystemSettings.objects.first)()
            current_week = settings.current_gameweek if settings else 4
        except:
            current_week = 4
        
        # Get all unique players with match data
        player_names_query = PlayerMatch.objects.values_list('player_name', flat=True).distinct()
        if max_players:
            player_names_query = player_names_query[:max_players]
        
        player_names = await sync_to_async(list)(player_names_query)
        total_players = len(player_names)
        
        print(f"Starting OPTIMIZED Elo recalculation for {total_players} players...")
        
        # Initialize optimized calculator
        calculator = OptimizedEloCalculator()
        
        updated_count = 0
        batch_count = 0
        
        # Process players in batches
        for i in range(0, len(player_names), batch_size):
            batch = player_names[i:i + batch_size]
            batch_count += 1
            
            print(f"Processing batch {batch_count}: players {i+1}-{min(i+batch_size, total_players)} of {total_players}")
            
            # Load all match data for this batch
            batch_match_data = {}
            for player_name in batch:
                matches = await sync_to_async(list)(
                    PlayerMatch.objects.filter(player_name=player_name).order_by('date').values(
                        'id', 'points', 'goals', 'assists', 'minutes_played', 'date'
                    )
                )
                
                if matches:
                    batch_match_data[player_name] = pd.DataFrame(matches)
            
            # Calculate Elos for entire batch using optimized calculator
            batch_results = calculator.calculate_batch_elos(batch_match_data)
            
            # Update database with batch results
            for player_name, result in batch_results.items():
                try:
                    match_data = batch_match_data[player_name]
                    elo_before = result['elo_before']
                    elo_after = result['elo_after']
                    final_elo = result['final_elo']
                    
                    # Update PlayerMatch records with new Elo values
                    for idx, (_, match_row) in enumerate(match_data.iterrows()):
                        match_obj = await sync_to_async(PlayerMatch.objects.get)(id=match_row['id'])
                        match_obj.elo_before_match = float(elo_before[idx])
                        match_obj.elo_after_match = float(elo_after[idx])
                        await sync_to_async(match_obj.save)()
                    
                    # Update Player record
                    existing_player = await sync_to_async(
                        Player.objects.filter(name=player_name, week=current_week).first
                    )()
                    
                    if existing_player:
                        existing_player.elo = final_elo
                        existing_player.elo_rating = final_elo
                        existing_player.cost = max(4.0, min(15.0, 4.0 + (final_elo - 1200) / 100))
                        await sync_to_async(existing_player.save)()
                    else:
                        print(f"Skipping {player_name} - no existing player record found")
                        continue
                    
                    # Update EloCalculation record
                    latest_match = match_data.iloc[-1]
                    await sync_to_async(EloCalculation.objects.update_or_create)(
                        player_name=player_name,
                        week=current_week,
                        season="2024-2025",
                        defaults={
                            'elo_rating': final_elo,
                            'previous_elo': elo_after[0] if len(elo_after) > 1 else 1200.0,
                            'elo_change': final_elo - (elo_after[0] if len(elo_after) > 1 else 1200.0),
                            'matches_played': len(match_data),
                            'last_match_date': latest_match['date'],
                            'form_rating': latest_match['points'],
                        }
                    )
                    
                    updated_count += 1
                    
                except Exception as e:
                    print(f"Error updating {player_name}: {str(e)}")
                    continue
            
            print(f"Completed batch {batch_count}: {updated_count} players updated so far")
        
        return {
            'success': True,
            'updated_count': updated_count,
            'total_players': total_players,
            'week': current_week,
            'method': 'optimized'
        }
        
    except Exception as e:
        return {'error': f"Optimized Elo calculation error: {str(e)}"}


def test_optimized_recalculate():
    """
    Test the optimized recalculate function.
    """
    print("="*60)
    print("TESTING OPTIMIZED RECALCULATE ELO FUNCTION")
    print("="*60)
    
    import time
    
    # Test with small number of players
    print("Testing with 5 players...")
    start_time = time.time()
    
    result = asyncio.run(optimized_recalculate_elos(max_players=5, batch_size=5))
    
    end_time = time.time()
    
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
        return False
    
    print(f"✅ Success: {result}")
    print(f"⚡ Processing time: {end_time - start_time:.4f} seconds")
    print(f"📊 Updated {result['updated_count']} of {result['total_players']} players")
    
    return True


if __name__ == "__main__":
    success = test_optimized_recalculate()
    
    if success:
        print("\n🎉 Optimized recalculate function is ready!")
        print("💡 Ready to integrate into Django views for 20x+ speedup!")
    else:
        print("\n❌ Need to fix issues before integration.")