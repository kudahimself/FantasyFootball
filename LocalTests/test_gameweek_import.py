#!/usr/bin/env python
"""
Test        if result['success']:
            print('✅ Gameweek import system is working correctly!')
            print(f'Result keys: {list(result.keys())}')
            # Print all available data
            for key, value in result.items():
                if key != 'success':
                    print(f'{key}: {value}')
        else:
            print(f'❌ Import failed: {result.get("error", "Unknown error")}')or gameweek import functionality
"""
import os
import django
import asyncio

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')
django.setup()

from MyApi.utils.gameweek_importer import get_current_gameweek_data
from MyApi.models import PlayerMatch

def test_gameweek_import():
    print('Testing gameweek import functionality...')
    
    # Get current count
    initial_count = PlayerMatch.objects.count()
    print(f'Initial PlayerMatch count: {initial_count}')
    
    # Test the import
    try:
        result = asyncio.run(get_current_gameweek_data())
        print(f'\nImport result success: {result["success"]}')
        
        # Get final count
        final_count = PlayerMatch.objects.count()
        print(f'Final PlayerMatch count: {final_count}')
        print(f'New matches added: {final_count - initial_count}')
        
        if result['success']:
            print('\n✅ Gameweek import system is working correctly!')
            stats = result['stats']
            print(f'Current gameweek: {stats["current_gameweek"]}')
            print(f'Total players processed: {stats["total_players"]}')
            print(f'New matches: {stats["new_matches"]}')
            print(f'Updated matches: {stats["updated_matches"]}')
        else:
            print(f'❌ Import failed: {result["error"]}')
            
    except Exception as e:
        print(f'❌ Error during test: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_gameweek_import()