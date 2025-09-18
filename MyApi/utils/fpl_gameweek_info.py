"""
FPL Gameweek Information Utility

This module handles fetching current gameweek information from the FPL API.
Provides simple functions to get current gameweek data for display purposes.
"""

import asyncio
import aiohttp
from typing import Dict, Any, Optional
from asgiref.sync import sync_to_async


async def get_current_gameweek_info() -> Dict[str, Any]:
    """
    Fetch current gameweek information from FPL API
    
    Returns:
        Dict[str, Any]: Current gameweek information including:
            - success: bool
            - current_gameweek: int
            - gameweek_name: str
            - is_current: bool
            - deadline_time: str
            - finished: bool
            - error: str (if failed)
    """
    try:
        from fpl import FPL
        
        async with aiohttp.ClientSession() as session:
            fpl = FPL(session)
            
            # Get all gameweeks
            gameweeks = await fpl.get_gameweeks()
            
            # Find current gameweek
            current_gw = None
            for gw in gameweeks:
                if gw.is_current:
                    current_gw = gw
                    break
            
            if not current_gw:
                # If no current gameweek, find the next one
                for gw in gameweeks:
                    if not gw.finished:
                        current_gw = gw
                        break
            
            if current_gw:
                # Handle deadline_time formatting safely
                deadline_str = 'TBD'
                if hasattr(current_gw, 'deadline_time') and current_gw.deadline_time:
                    if hasattr(current_gw.deadline_time, 'strftime'):
                        deadline_str = current_gw.deadline_time.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        deadline_str = str(current_gw.deadline_time)
                
                return {
                    'success': True,
                    'current_gameweek': current_gw.id,
                    'gameweek_name': f"Gameweek {current_gw.id}",
                    'is_current': current_gw.is_current,
                    'deadline_time': deadline_str,
                    'finished': current_gw.finished,
                    'data_checked': getattr(current_gw, 'data_checked', False),
                    'average_entry_score': getattr(current_gw, 'average_entry_score', 0),
                    'highest_score': getattr(current_gw, 'highest_score', 0)
                }
            else:
                return {
                    'success': False,
                    'error': 'No gameweek information available'
                }
                
    except Exception as e:
        return {
            'success': False,
            'error': f'Failed to fetch gameweek info: {str(e)}'
        }


def get_current_gameweek_sync() -> Dict[str, Any]:
    """
    Synchronous wrapper for get_current_gameweek_info()
    Use this in Django views and templates
    
    Returns:
        Dict[str, Any]: Current gameweek information
    """
    return asyncio.run(get_current_gameweek_info())


async def get_gameweek_status() -> Dict[str, Any]:
    """
    Get a simple status of the current gameweek for display
    
    Returns:
        Dict[str, Any]: Simple gameweek status with:
            - gameweek_number: int
            - status: str ('live', 'finished', 'upcoming')
            - deadline: str
    """
    try:
        info = await get_current_gameweek_info()
        
        if not info['success']:
            return {
                'gameweek_number': 0,
                'status': 'error',
                'deadline': 'Unknown',
                'error': info['error']
            }
        
        # Determine status
        if info['finished']:
            status = 'finished'
        elif info['is_current']:
            status = 'live'
        else:
            status = 'upcoming'
        
        return {
            'gameweek_number': info['current_gameweek'],
            'status': status,
            'deadline': info['deadline_time'],
            'average_score': info.get('average_entry_score', 0),
            'highest_score': info.get('highest_score', 0)
        }
        
    except Exception as e:
        return {
            'gameweek_number': 0,
            'status': 'error',
            'deadline': 'Unknown',
            'error': str(e)
        }