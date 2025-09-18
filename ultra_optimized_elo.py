#!/usr/bin/env python3
"""
FINAL optimized Elo calculator using Django's bulk_update for maximum performance.
"""

import time
from typing import Dict, List, Tuple, Any

async def ultra_optimized_recalculate_elos(max_players: int = None, batch_size: int = 100) -> Dict[str, Any]:
    """
    Ultra-optimized recalculate function using Django's bulk_update.
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
    
    def calculate_elo_change(current_elo: float, points: int, goals: int, assists: int, 
                           minutes_played: int, competition: str, k: int = 20) -> float:
        """
        Proper Elo calculation based on elo_model.py logic.
        Players can lose Elo when they underperform.
        """
        # Get league rating based on competition
        if competition in ['Champions League', 'Champions Lg']:
            league_rating = 1600
        elif competition in ['Premier League', 'FA Cup', 'Europa League', 'Europa Lg']:
            league_rating = 1500
        elif competition in ['Bundesliga', 'La Liga', 'Serie A']:
            league_rating = 1300
        elif competition in ['Ligue 1', 'Eredivisie']:
            league_rating = 1250
        elif competition in ['Championship', 'Primeira Liga']:
            league_rating = 1000
        else:
            league_rating = 900
        
        # Calculate expected score based on Elo (normalized to points scale)
        E_a = round(k / (1 + 10**(league_rating / current_elo)), 2)
        
        # Calculate actual performance points (Pa)
        # This should match the points calculation in elo_model.py
        Pa = points  # Use the fantasy points directly
        
        # Calculate Elo change: Ra + k * (Pa - E_a)
        # This allows for both positive and negative changes
        elo_change = k * (Pa - E_a)
        
        # Cap the change to prevent extreme swings
        return max(-30, min(30, elo_change))
    
    try:
        # Get current week
        try:
            settings = await sync_to_async(SystemSettings.objects.first)()
            current_week = settings.current_gameweek if settings else 4
        except:
            current_week = 4
        
        # Get all unique players with match data
        player_names_count = await sync_to_async(
            PlayerMatch.objects.values_list('player_name', flat=True).distinct().count
        )()
        
        if max_players:
            # Get limited list of unique player names
            player_names = await sync_to_async(list)(
                PlayerMatch.objects.values_list('player_name', flat=True).distinct()[:max_players]
            )
            total_players = len(player_names)
        else:
            # Get all unique player names
            player_names = await sync_to_async(list)(
                PlayerMatch.objects.values_list('player_name', flat=True).distinct()
            )
            total_players = player_names_count  # Use the count, not len(list)
        
        print(f"Starting ULTRA-OPTIMIZED Elo recalculation for {total_players} players...")
        
        updated_count = 0
        batch_count = 0
        
        # Process in batches
        for i in range(0, len(player_names), batch_size):
            batch = player_names[i:i + batch_size]
            batch_count += 1
            
            # Calculate correct batch range
            batch_start = i + 1
            batch_end = min(i + len(batch), len(player_names))
            
            print(f"Processing batch {batch_count}: players {batch_start}-{batch_end} of {len(player_names)}")
            
            # Get all matches for this batch in one query
            batch_matches = await sync_to_async(list)(
                PlayerMatch.objects.filter(player_name__in=batch)
                .order_by('player_name', 'date')
                .select_related()
            )
            
            # Get all players for this batch in one query
            batch_players = await sync_to_async(list)(
                Player.objects.filter(name__in=batch, week=current_week)
            )
            
            # Group matches by player
            player_matches = {}
            for match in batch_matches:
                if match.player_name not in player_matches:
                    player_matches[match.player_name] = []
                player_matches[match.player_name].append(match)
            
            # Calculate Elos for all players in batch
            matches_to_update = []
            players_to_update = []
            elo_calcs_to_create = []
            
            player_lookup = {p.name: p for p in batch_players}
            
            for player_name in batch:
                if player_name not in player_matches or player_name not in player_lookup:
                    continue
                
                matches = player_matches[player_name]
                player_obj = player_lookup[player_name]
                
                # Calculate Elo progression
                current_elo = 1200.0
                
                for match in matches:
                    # Set elo_before_match
                    match.elo_before_match = current_elo
                    
                    # Calculate new elo using proper Elo formula
                    elo_change = calculate_elo_change(
                        current_elo, match.points, match.goals, match.assists, 
                        match.minutes_played, match.competition
                    )
                    new_elo = current_elo + elo_change
                    
                    # Set elo_after_match
                    match.elo_after_match = new_elo
                    current_elo = new_elo
                    
                    matches_to_update.append(match)
                
                # Update player record
                final_elo = current_elo
                player_obj.elo = final_elo
                player_obj.cost = max(4.0, min(15.0, 4.0 + (final_elo - 1200) / 100))
                players_to_update.append(player_obj)
                
                # Prepare EloCalculation
                latest_match = matches[-1]
                elo_calcs_to_create.append(EloCalculation(
                    player_name=player_name,
                    week=current_week,
                    season="2024-2025",
                    elo_rating=final_elo,
                    previous_elo=matches[0].elo_after_match if len(matches) > 1 else 1200.0,
                    elo_change=final_elo - (matches[0].elo_after_match if len(matches) > 1 else 1200.0),
                    matches_played=len(matches),
                    last_match_date=latest_match.date,
                    form_rating=latest_match.points,
                ))
                
                updated_count += 1
            
            # Bulk update all records
            print(f"  Bulk updating {len(matches_to_update)} matches, {len(players_to_update)} players...")
            
            # Use Django's bulk_update for maximum performance
            if matches_to_update:
                await sync_to_async(PlayerMatch.objects.bulk_update)(
                    matches_to_update, ['elo_before_match', 'elo_after_match'], batch_size=1000
                )
            
            if players_to_update:
                await sync_to_async(Player.objects.bulk_update)(
                    players_to_update, ['elo', 'cost'], batch_size=1000
                )
            
            # Delete existing EloCalculation records for this batch and create new ones
            if elo_calcs_to_create:
                # First, delete existing records for this batch to avoid constraint violations
                await sync_to_async(EloCalculation.objects.filter(
                    player_name__in=batch, week=current_week, season="2024-2025"
                ).delete)()
                
                # Then create new records
                try:
                    await sync_to_async(EloCalculation.objects.bulk_create)(
                        elo_calcs_to_create, batch_size=1000, ignore_conflicts=True
                    )
                except Exception as e:
                    # Fallback: create records one by one to handle any remaining conflicts
                    print(f"  Bulk create failed, using individual creates: {e}")
                    for elo_calc in elo_calcs_to_create:
                        try:
                            await sync_to_async(EloCalculation.objects.update_or_create)(
                                player_name=elo_calc.player_name,
                                week=elo_calc.week,
                                season=elo_calc.season,
                                defaults={
                                    'elo_rating': elo_calc.elo_rating,
                                    'previous_elo': elo_calc.previous_elo,
                                    'elo_change': elo_calc.elo_change,
                                    'matches_played': elo_calc.matches_played,
                                    'last_match_date': elo_calc.last_match_date,
                                    'form_rating': elo_calc.form_rating,
                                }
                            )
                        except Exception as inner_e:
                            print(f"  Failed to create EloCalculation for {elo_calc.player_name}: {inner_e}")
            
            print(f"Completed batch {batch_count}: {updated_count} players updated so far")
        
        return {
            'success': True,
            'updated_count': updated_count,
            'total_players': total_players,
            'week': current_week,
            'method': 'ultra_optimized'
        }
        
    except Exception as e:
        return {'error': f"Ultra-optimized Elo calculation error: {str(e)}"}


def test_ultra_optimized():
    """Test the ultra-optimized version."""
    print("="*60)
    print("TESTING ULTRA-OPTIMIZED ELO CALCULATOR")
    print("="*60)
    
    import asyncio
    
    start_time = time.time()
    result = asyncio.run(ultra_optimized_recalculate_elos(max_players=10, batch_size=10))
    end_time = time.time()
    
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
        return False
    
    print(f"✅ Success: {result}")
    print(f"⚡ Total time: {end_time - start_time:.4f} seconds")
    print(f"📊 Rate: {result['updated_count'] / (end_time - start_time):.2f} players/second")
    
    return True


if __name__ == "__main__":
    success = test_ultra_optimized()
    
    if success:
        print("\n🚀 Ultra-optimized version is ready!")
        print("💡 Uses Django's bulk_update for maximum database performance!")
    else:
        print("\n❌ Need to fix issues before use.")