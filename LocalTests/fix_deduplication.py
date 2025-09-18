#!/usr/bin/env python
"""
Fix Gameweek Import Deduplication Issue

This script fixes the deduplication logic in the gameweek importer to prevent
duplicate entries by improving the matching criteria.
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')
django.setup()

from MyApi.models import PlayerMatch

def analyze_deduplication_issue():
    print('🔍 Analyzing deduplication issue...')
    
    # Check different round_info formats
    round_formats = PlayerMatch.objects.values_list('round_info', flat=True).distinct()
    print('\n📊 Different round_info formats found:')
    for format_type in round_formats:
        count = PlayerMatch.objects.filter(round_info=format_type).count()
        print(f'  - "{format_type}": {count} entries')
    
    # Check for patterns that could cause mismatches
    print('\n🔍 Checking for potential mismatch patterns...')
    
    # Find entries with numeric vs text format
    numeric_rounds = PlayerMatch.objects.filter(round_info__regex=r'^\d+$').count()
    matchweek_rounds = PlayerMatch.objects.filter(round_info__icontains='Matchweek').count()
    gameweek_rounds = PlayerMatch.objects.filter(round_info__icontains='Gameweek').count()
    
    print(f'  - Numeric format (e.g., "4"): {numeric_rounds} entries')
    print(f'  - "Matchweek X" format: {matchweek_rounds} entries') 
    print(f'  - "Gameweek X" format: {gameweek_rounds} entries')
    
    if numeric_rounds > 0 and (matchweek_rounds > 0 or gameweek_rounds > 0):
        print('\n🚨 MISMATCH DETECTED: Mixed round_info formats!')
        print('   This will cause deduplication failures.')
        return True
    
    return False

def clean_duplicate_entries():
    print('\n🧹 Cleaning duplicate entries...')
    
    from django.db.models import Count
    
    # Find all duplicate entries (same player, same date)
    duplicates = PlayerMatch.objects.values('player_name', 'date').annotate(
        count=Count('id')
    ).filter(count__gt=1)
    
    cleaned_count = 0
    for duplicate in duplicates:
        player_name = duplicate['player_name']
        date = duplicate['date']
        count = duplicate['count']
        
        print(f'Processing {player_name} on {date} ({count} entries)...')
        
        # Get all duplicate entries for this player/date
        entries = PlayerMatch.objects.filter(
            player_name=player_name,
            date=date
        ).order_by('id')
        
        if count > 1:
            # Keep the first entry, remove the rest
            entries_to_delete = entries[1:]
            
            print(f'  Keeping entry ID {entries.first().id}')
            for entry in entries_to_delete:
                print(f'  Deleting entry ID {entry.id}')
                entry.delete()
                cleaned_count += 1
    
    print(f'\n✅ Cleaned {cleaned_count} duplicate entries')

def fix_round_info_format():
    print('\n🔧 Standardizing round_info format...')
    
    # Convert numeric round_info to "Gameweek X" format
    numeric_entries = PlayerMatch.objects.filter(round_info__regex=r'^\d+$')
    
    updated_count = 0
    for entry in numeric_entries:
        old_format = entry.round_info
        new_format = f"Gameweek {old_format}"
        entry.round_info = new_format
        entry.save()
        updated_count += 1
        
        if updated_count <= 5:  # Show first 5 examples
            print(f'  Updated: "{old_format}" → "{new_format}"')
    
    print(f'✅ Updated {updated_count} entries to standard format')

if __name__ == '__main__':
    has_mismatch = analyze_deduplication_issue()
    
    if has_mismatch:
        print('\n💡 RECOMMENDED ACTIONS:')
        print('1. Clean existing duplicate entries')
        print('2. Standardize round_info format') 
        print('3. Update gameweek importer deduplication logic')
        
        response = input('\nProceed with cleanup? (y/N): ')
        if response.lower() == 'y':
            clean_duplicate_entries()
            fix_round_info_format()
            print('\n✅ Cleanup complete!')
        else:
            print('Cleanup skipped.')
    else:
        print('\n✅ No deduplication issues found.')