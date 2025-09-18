#!/usr/bin/env python
"""
Test script for FPL gameweek info utility
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')
django.setup()

from MyApi.utils.fpl_gameweek_info import get_current_gameweek_sync

def test_gameweek_info():
    print('Testing FPL gameweek info utility...')
    
    try:
        result = get_current_gameweek_sync()
        
        print('\nGameweek info result:')
        for key, value in result.items():
            print(f'{key}: {value}')
        
        print()
        if result['success']:
            print('✅ Gameweek utility is working correctly!')
            current_gw = result['current_gameweek']
            print(f'Current gameweek: {current_gw}')
            
            # Determine status
            if result['finished']:
                status = 'Finished'
            elif result['is_current']:
                status = 'Live'
            else:
                status = 'Upcoming'
            
            print(f'Status: {status}')
            print(f'Deadline: {result["deadline_time"]}')
            
            if result.get('average_entry_score', 0) > 0:
                print(f'Average Score: {result["average_entry_score"]}')
                print(f'Highest Score: {result["highest_score"]}')
                
        else:
            error = result['error']
            print(f'❌ Error: {error}')
            
    except Exception as e:
        print(f'❌ Exception during test: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_gameweek_info()