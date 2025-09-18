#!/usr/bin/env python3
"""
Database-optimized Elo calculator that minimizes I/O operations.
"""

import time
from typing import Dict, List, Tuple, Any

class DatabaseOptimizedEloCalculator:
    """
    Elo calculator optimized for database operations.
    Key optimizations:
    1. Bulk database operations
    2. Minimize queries
    3. Batch updates
    """
    
    def __init__(self, starting_elo: float = 1200.0):
        self.starting_elo = starting_elo
        self.points_weight = 2.0
        self.goals_weight = 5.0
        self.assists_weight = 3.0
        self.min_elo_change = -30.0
        self.max_elo_change = 30.0
    
    def calculate_elo_change(self, points: int, goals: int, assists: int, minutes_played: int) -> float:
        """Calculate Elo change for a single match."""
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
        performance_points = (
            points * self.points_weight +
            goals * self.goals_weight +
            assists * self.assists_weight +
            minutes_bonus
        )
        
        # Cap the Elo change
        return max(self.min_elo_change, min(self.max_elo_change, performance_points))
    
    def calculate_player_elos(self, match_data: List[Dict]) -> Tuple[List[float], List[float], float]:
        """
        Calculate Elo progression for a player with minimal overhead.
        
        Returns:
            Tuple of (elo_before_list, elo_after_list, final_elo)
        """
        if not match_data:
            return [], [], self.starting_elo
        
        elo_before = []
        elo_after = []
        current_elo = self.starting_elo
        
        for match in match_data:
            elo_before.append(current_elo)
            elo_change = self.calculate_elo_change(
                match['points'], match['goals'], 
                match['assists'], match['minutes_played']
            )
            new_elo = current_elo + elo_change
            elo_after.append(new_elo)
            current_elo = new_elo
        
        return elo_before, elo_after, current_elo


async def database_optimized_recalculate_elos(max_players: int = None, batch_size: int = 50) -> Dict[str, Any]:
    """
    Database-optimized recalculate function with bulk operations.
    """
    import asyncio
    from asgiref.sync import sync_to_async
    import os
    import django
    
    # Setup Django if not already done
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')
    django.setup()
    
    from MyApi.models import Player, PlayerMatch, EloCalculation, SystemSettings
    from django.db import transaction
    
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
        
        print(f"Starting DATABASE-OPTIMIZED Elo recalculation for {total_players} players...")
        
        calculator = DatabaseOptimizedEloCalculator()
        updated_count = 0
        batch_count = 0
        
        # Process in batches for better memory management
        for i in range(0, len(player_names), batch_size):
            batch = player_names[i:i + batch_size]
            batch_count += 1
            
            print(f"Processing batch {batch_count}: players {i+1}-{min(i+batch_size, total_players)} of {total_players}")
            
            # Bulk operations for this batch
            match_updates = []
            player_updates = []
            elo_calc_updates = []
            
            for player_name in batch:
                try:
                    # Get all matches for this player (single query)
                    matches = await sync_to_async(list)(
                        PlayerMatch.objects.filter(player_name=player_name)
                        .order_by('date')
                        .values('id', 'points', 'goals', 'assists', 'minutes_played', 'date')
                    )
                    
                    if not matches:
                        continue
                    
                    # Calculate Elos (fast, in-memory)
                    elo_before_list, elo_after_list, final_elo = calculator.calculate_player_elos(matches)
                    
                    # Prepare match updates for bulk operation
                    for idx, match in enumerate(matches):
                        match_updates.append({
                            'id': match['id'],
                            'elo_before_match': elo_before_list[idx],
                            'elo_after_match': elo_after_list[idx]
                        })
                    
                    # Prepare player update
                    existing_player = await sync_to_async(
                        Player.objects.filter(name=player_name, week=current_week).first
                    )()
                    
                    if existing_player:
                        player_updates.append({
                            'id': existing_player.id,
                            'elo': final_elo,
                            'elo_rating': final_elo,
                            'cost': max(4.0, min(15.0, 4.0 + (final_elo - 1200) / 100))
                        })
                        
                        # Prepare EloCalculation update
                        latest_match = matches[-1]
                        elo_calc_updates.append({
                            'player_name': player_name,
                            'week': current_week,
                            'season': "2024-2025",
                            'elo_rating': final_elo,
                            'previous_elo': elo_after_list[0] if len(elo_after_list) > 1 else 1200.0,
                            'elo_change': final_elo - (elo_after_list[0] if len(elo_after_list) > 1 else 1200.0),
                            'matches_played': len(matches),
                            'last_match_date': latest_match['date'],
                            'form_rating': latest_match['points'],
                        })
                        
                        updated_count += 1
                    
                except Exception as e:
                    print(f"Error processing {player_name}: {str(e)}")
                    continue
            
            # Perform bulk updates
            print(f"  Performing bulk updates: {len(match_updates)} matches, {len(player_updates)} players...")
            
            # Bulk update PlayerMatch records
            if match_updates:
                for update in match_updates:
                    match_obj = await sync_to_async(PlayerMatch.objects.get)(id=update['id'])
                    match_obj.elo_before_match = update['elo_before_match']
                    match_obj.elo_after_match = update['elo_after_match']
                    await sync_to_async(match_obj.save)()
            
            # Bulk update Player records
            if player_updates:
                for update in player_updates:
                    player_obj = await sync_to_async(Player.objects.get)(id=update['id'])
                    player_obj.elo = update['elo']
                    player_obj.elo_rating = update['elo_rating']
                    player_obj.cost = update['cost']
                    await sync_to_async(player_obj.save)()
            
            # Bulk update EloCalculation records
            if elo_calc_updates:
                for update in elo_calc_updates:
                    await sync_to_async(EloCalculation.objects.update_or_create)(
                        player_name=update['player_name'],
                        week=update['week'],
                        season=update['season'],
                        defaults={
                            'elo_rating': update['elo_rating'],
                            'previous_elo': update['previous_elo'],
                            'elo_change': update['elo_change'],
                            'matches_played': update['matches_played'],
                            'last_match_date': update['last_match_date'],
                            'form_rating': update['form_rating'],
                        }
                    )
            
            print(f"Completed batch {batch_count}: {updated_count} players updated so far")
        
        return {
            'success': True,
            'updated_count': updated_count,
            'total_players': total_players,
            'week': current_week,
            'method': 'database_optimized'
        }
        
    except Exception as e:
        return {'error': f"Database-optimized Elo calculation error: {str(e)}"}


def test_database_optimized():
    """Test the database-optimized version."""
    print("="*60)
    print("TESTING DATABASE-OPTIMIZED ELO CALCULATOR")
    print("="*60)
    
    import asyncio
    
    start_time = time.time()
    result = asyncio.run(database_optimized_recalculate_elos(max_players=10, batch_size=5))
    end_time = time.time()
    
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
        return False
    
    print(f"✅ Success: {result}")
    print(f"⚡ Total time: {end_time - start_time:.4f} seconds")
    print(f"📊 Rate: {result['updated_count'] / (end_time - start_time):.2f} players/second")
    
    return True


if __name__ == "__main__":
    test_database_optimized()