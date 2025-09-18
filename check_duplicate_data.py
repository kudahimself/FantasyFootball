#!/usr/bin/env python
"""
Data Quality Check: Viktor Gyökeres Duplicate Entries

This script investigates duplicate entries for Viktor Gyökeres on Sep 13, 2025
to identify issues with the gameweek import deduplication logic.
"""
import os
import django
from datetime import date

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')
django.setup()

from MyApi.models import PlayerMatch, Player

def check_viktor_duplicates():
    print('🔍 Checking Viktor Gyökeres duplicate entries...')
    
    try:
        # Find Viktor Gyökeres
        viktor = Player.objects.filter(name__icontains='Gyökeres').first()
        if not viktor:
            print('❌ Viktor Gyökeres not found in database')
            return
            
        print(f'✅ Found player: {viktor.name} (ID: {viktor.id})')
        
        # Check for duplicate entries on Sep 13, 2025
        sep_13_matches = PlayerMatch.objects.filter(
            player_name=viktor.name,
            date=date(2025, 9, 13)
        ).order_by('id')
        
        print(f'\n📊 Matches for Sep 13, 2025: {sep_13_matches.count()}')
        
        if sep_13_matches.count() <= 1:
            print('✅ No duplicates found')
            if sep_13_matches.count() == 1:
                match = sep_13_matches.first()
                print(f'Single entry found: GW={match.round_info}, Points={match.points}')
            return
            
        print('\n🚨 DUPLICATE ENTRIES DETECTED:')
        for i, match in enumerate(sep_13_matches, 1):
            print(f'Entry {i}:')
            print(f'  - ID: {match.id}')
            print(f'  - Gameweek: {match.round_info}')
            print(f'  - Points: {match.points}')
            print(f'  - Team: {match.position}')
            print(f'  - Opposition: {match.opponent}')
            print(f'  - Minutes: {match.minutes_played}')
            print(f'  - Goals: {match.goals}')
            print(f'  - Assists: {match.assists}')
            print()
            
        # Check if all entries are identical (indicating import bug)
        if sep_13_matches.count() > 1:
            first_match = sep_13_matches.first()
            all_identical = True
            
            for match in sep_13_matches[1:]:
                if (match.round_info != first_match.round_info or 
                    match.points != first_match.points or
                    match.opponent != first_match.opponent):
                    all_identical = False
                    break
                    
            if all_identical:
                print('🔥 ALL ENTRIES ARE IDENTICAL - This is a deduplication bug!')
                print('   The import system failed to detect existing records.')
            else:
                print('ℹ️  Entries have different data - may be legitimate multiple matches.')
                
        # Check other recent dates for similar issues
        print('\n🔍 Checking for other duplicate dates...')
        from django.db.models import Count
        duplicate_dates = PlayerMatch.objects.filter(
            player_name=viktor.name
        ).values('date').annotate(
            count=Count('id')
        ).filter(count__gt=1).order_by('-date')
        
        if duplicate_dates:
            print(f'Found {duplicate_dates.count()} dates with duplicates:')
            for item in duplicate_dates:
                date_str = item['date'].strftime('%Y-%m-%d')
                count = item['count']
                print(f'  - {date_str}: {count} entries')
        else:
            print('✅ No other duplicate dates found')
            
    except Exception as e:
        print(f'❌ Error during check: {e}')
        import traceback
        traceback.print_exc()


def suggest_fix():
    print('\n💡 SUGGESTED FIXES:')
    print('1. Update gameweek_importer.py deduplication logic')
    print('2. Use get_or_create() instead of checking existence separately')
    print('3. Add unique constraint in database model')
    print('4. Clean up existing duplicates before next import')


if __name__ == '__main__':
    check_viktor_duplicates()
    suggest_fix()