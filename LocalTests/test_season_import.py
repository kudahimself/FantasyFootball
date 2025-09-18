#!/usr/bin/env python
"""
Test Season Gameweek Import

This script tests the season gameweek import functionality
to ensure it works correctly before using it in production.
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')
django.setup()

from MyApi.models import PlayerMatch
from MyApi.utils.season_gameweek_importer import import_specific_gameweeks
import asyncio

def test_season_import():
    print('🧪 Testing Season Gameweek Import...')
    
    # Get current data count
    initial_count = PlayerMatch.objects.count()
    print(f'Initial PlayerMatch count: {initial_count:,}')
    
    # Test importing just gameweek 1 and 2 as a test
    test_gameweeks = [1, 2]
    print(f'\\nTesting import of gameweeks: {test_gameweeks}')
    
    try:
        # Run the import
        result = asyncio.run(import_specific_gameweeks(test_gameweeks))
        
        # Get final count
        final_count = PlayerMatch.objects.count()
        new_entries = final_count - initial_count
        
        print(f'\\n📊 Import Results:')
        print(f'Success: {result["success"]}')
        
        if result['success']:
            print(f'Season: {result["season"]}')
            print(f'Gameweeks processed: {result["gameweeks_processed"]}')
            print(f'Total new matches: {result["total_new_matches"]}')
            print(f'Total updated matches: {result["total_updated_matches"]}')
            print(f'Total skipped matches: {result["total_skipped_matches"]}')
            print(f'Total errors: {result["total_errors"]}')
            print(f'Database entries added: {new_entries:,}')
            
            # Check data quality
            print(f'\\n🔍 Data Quality Check:')
            
            # Check for proper opponent format
            numeric_opponents = PlayerMatch.objects.filter(
                opponent__regex=r'^\\d+$',
                round_info__startswith='Gameweek'
            ).count()
            
            text_opponents = PlayerMatch.objects.filter(
                round_info__startswith='Gameweek'
            ).exclude(opponent__regex=r'^\\d+$').count()
            
            print(f'New season data with numeric opponents: {numeric_opponents}')
            print(f'New season data with text opponents: {text_opponents}')
            
            # Show sample of new data
            sample_matches = PlayerMatch.objects.filter(
                round_info__in=['Gameweek 1', 'Gameweek 2']
            ).order_by('?')[:5]
            
            print(f'\\n📋 Sample imported data:')
            for match in sample_matches:
                print(f'  - {match.player_name} vs {match.opponent} (GW: {match.round_info}, Points: {match.points})')
            
            print(f'\\n✅ Test import successful!')
            
        else:
            print(f'❌ Import failed: {result.get("error", "Unknown error")}')
            
    except Exception as e:
        print(f'❌ Test failed with exception: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_season_import()