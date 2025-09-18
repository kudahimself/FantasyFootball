"""
FPL Cost Update Utility

This module handles updating player costs from the FPL API.
Keeps cost management separate from Elo calculations for better code organization.

Key features:
- Fetches real-time player costs from FPL API
- Updates database costs without affecting Elo ratings
- Handles individual player lookups and bulk updates
- Proper error handling and progress tracking
"""

import time
import aiohttp
from typing import Dict, List, Any, Optional
from asgiref.sync import sync_to_async


async def get_player_cost_from_fpl(player_name: str) -> Optional[float]:
    """
    Get player cost from FPL API
    
    Args:
        player_name (str): Player name to search for
        
    Returns:
        Optional[float]: Player cost in millions (e.g., 9.0 for £9.0m) or None if not found
    """
    try:
        from fpl import FPL
        
        async with aiohttp.ClientSession() as session:
            fpl = FPL(session)
            players = await fpl.get_players()
            
            for player in players:
                full_name = f"{player.first_name} {player.second_name}"
                if full_name.lower() == player_name.lower():
                    # FPL API returns cost in tenths (e.g., 90 for £9.0m)
                    cost = round(player.now_cost / 10, 1)
                    return cost
            
            return None
    except Exception as e:
        print(f"Error getting FPL cost for {player_name}: {e}")
        return None


async def update_player_cost(player_name: str, current_week: int = None) -> Dict[str, Any]:
    """
    Update cost for a single player from FPL API
    
    Args:
        player_name (str): Name of the player to update
        current_week (int, optional): Game week to update cost for
    
    Returns:
        Dict[str, Any]: Update result with status and details
    """
    try:
        # Import models here to avoid circular imports
        from MyApi.models import Player, SystemSettings
        
        # Get current week if not provided
        if current_week is None:
            settings = await sync_to_async(SystemSettings.get_settings)()
            current_week = settings.current_gameweek
        
        # Get player record
        try:
            player_obj = await sync_to_async(Player.objects.get)(
                name=player_name, week=current_week
            )
        except Player.DoesNotExist:
            return {
                'success': False,
                'error': f'Player {player_name} not found in week {current_week}',
                'player_name': player_name
            }
        
        # Get FPL cost
        fpl_cost = await get_player_cost_from_fpl(player_name)
        
        if fpl_cost is None:
            return {
                'success': False,
                'error': f'Could not fetch FPL cost for {player_name}',
                'player_name': player_name
            }
        
        # Update if there's a significant difference
        old_cost = player_obj.cost
        cost_change = fpl_cost - old_cost
        
        if abs(cost_change) > 0.05:  # Only update if difference > £0.05m
            player_obj.cost = fpl_cost
            await sync_to_async(player_obj.save)()
            
            return {
                'success': True,
                'player_name': player_name,
                'old_cost': old_cost,
                'new_cost': fpl_cost,
                'cost_change': cost_change,
                'updated': True
            }
        else:
            return {
                'success': True,
                'player_name': player_name,
                'old_cost': old_cost,
                'new_cost': fpl_cost,
                'cost_change': cost_change,
                'updated': False,
                'message': 'No significant cost change'
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'player_name': player_name
        }


async def update_all_player_costs_from_fpl(current_week: int = None, show_progress: bool = True) -> Dict[str, Any]:
    """
    Update all player costs from FPL API without affecting Elo ratings
    
    Args:
        current_week (int, optional): Game week to update costs for
        show_progress (bool): Whether to show progress output
    
    Returns:
        Dict[str, Any]: Summary of cost updates
    """
    if show_progress:
        print(f"🏷️  Starting FPL Cost Update")
    
    start_time = time.time()
    
    # Import models here to avoid circular imports
    from MyApi.models import Player, SystemSettings
    
    try:
        # Get current week from system settings if not provided
        if current_week is None:
            settings = await sync_to_async(SystemSettings.get_settings)()
            current_week = settings.current_gameweek
        
        # Get all unique players for the current week
        unique_players = await sync_to_async(list)(
            Player.objects.filter(week=current_week).values_list('name', flat=True).distinct()
        )
        
        total_players = len(unique_players)
        
        if show_progress:
            print(f"👥 Total players to update costs for: {total_players}")
            print(f"📅 Week: {current_week}")
        
        successful_updates = 0
        failed_updates = 0
        cost_changes = []
        players_updated = 0
        
        # Process each player individually
        for i, player_name in enumerate(unique_players, 1):
            result = await update_player_cost(player_name, current_week)
            
            if result['success']:
                successful_updates += 1
                
                if result.get('updated', False):
                    players_updated += 1
                    cost_changes.append({
                        'player': player_name,
                        'old_cost': result['old_cost'],
                        'new_cost': result['new_cost'],
                        'change': result['cost_change']
                    })
                    
                    # Show progress for significant changes
                    if show_progress and abs(result['cost_change']) > 0.5:
                        print(f"💰 {player_name}: £{result['old_cost']:.1f}m → £{result['new_cost']:.1f}m")
            else:
                failed_updates += 1
                if show_progress and failed_updates <= 5:  # Show first few failures
                    print(f"❌ {result.get('error', 'Unknown error')}")
            
            # Show progress every 100 players
            if show_progress and (i % 100 == 0 or i == total_players):
                print(f"🔄 Progress: {i}/{total_players} players processed")
        
        # Summary
        end_time = time.time()
        duration = end_time - start_time
        processing_rate = total_players / duration if duration > 0 else 0
        
        if show_progress:
            print(f"✅ Cost update complete!")
            print(f"   Processed: {successful_updates}/{total_players} players")
            print(f"   Updated: {players_updated} players")
            print(f"   Failed: {failed_updates} players")
            print(f"   Significant changes: {len([c for c in cost_changes if abs(c['change']) > 0.5])}")
            print(f"   Duration: {duration:.2f} seconds")
            print(f"   Rate: {processing_rate:.2f} players/second")
        
        return {
            'success': True,
            'total_players': total_players,
            'successful_updates': successful_updates,
            'failed_updates': failed_updates,
            'players_updated': players_updated,
            'cost_changes': cost_changes,
            'duration': duration,
            'processing_rate': processing_rate,
            'week': current_week
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


async def check_player_costs_vs_fpl(player_names: List[str], current_week: int = None) -> Dict[str, Any]:
    """
    Compare database costs vs FPL API costs for specific players
    
    Args:
        player_names (List[str]): List of player names to check
        current_week (int, optional): Game week to check
    
    Returns:
        Dict[str, Any]: Comparison results
    """
    from MyApi.models import Player, SystemSettings
    
    # Get current week if not provided
    if current_week is None:
        settings = await sync_to_async(SystemSettings.get_settings)()
        current_week = settings.current_gameweek
    
    results = []
    
    for player_name in player_names:
        try:
            # Get database cost
            player = await sync_to_async(Player.objects.get)(
                name=player_name, week=current_week
            )
            db_cost = player.cost
            
            # Get FPL cost
            fpl_cost = await get_player_cost_from_fpl(player_name)
            
            if fpl_cost is not None:
                difference = fpl_cost - db_cost
                results.append({
                    'player_name': player_name,
                    'db_cost': db_cost,
                    'fpl_cost': fpl_cost,
                    'difference': difference,
                    'match': abs(difference) < 0.1,
                    'status': 'success'
                })
            else:
                results.append({
                    'player_name': player_name,
                    'db_cost': db_cost,
                    'fpl_cost': None,
                    'difference': None,
                    'match': False,
                    'status': 'fpl_not_found'
                })
                
        except Player.DoesNotExist:
            results.append({
                'player_name': player_name,
                'db_cost': None,
                'fpl_cost': None,
                'difference': None,
                'match': False,
                'status': 'player_not_found'
            })
        except Exception as e:
            results.append({
                'player_name': player_name,
                'db_cost': None,
                'fpl_cost': None,
                'difference': None,
                'match': False,
                'status': 'error',
                'error': str(e)
            })
    
    return {
        'success': True,
        'results': results,
        'week': current_week
    }


# Convenience function for standalone execution
async def run_cost_update(current_week: int = None) -> Dict[str, Any]:
    """
    Convenience function to run the cost update
    
    Args:
        current_week (int, optional): Game week to update costs for
    
    Returns:
        Dict[str, Any]: Result summary
    """
    return await update_all_player_costs_from_fpl(current_week)


if __name__ == "__main__":
    import asyncio
    import os
    import django
    
    # Setup Django if running standalone
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')
    django.setup()
    
    # Run the cost update
    result = asyncio.run(run_cost_update())
    print(f"\n📊 Final Summary: {result.get('players_updated', 0)} players updated out of {result.get('total_players', 0)}")