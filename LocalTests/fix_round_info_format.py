#!/usr/bin/env python
"""
Fix Round Info Format

This script finds and fixes any round_info entries that are just numbers
and converts them to the proper "Gameweek X" format.
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')
django.setup()

from MyApi.models import PlayerMatch

def find_numeric_round_info():
    print('🔍 Finding entries with numeric round_info...')
    
    # Find entries with only numbers (1, 2, 3, etc.)
    numeric_entries = PlayerMatch.objects.filter(round_info__regex=r'^\d+$')
    
    if numeric_entries.count() == 0:
        print('✅ No numeric round_info entries found')
        return []
    
    print(f'📊 Found {numeric_entries.count()} entries with numeric round_info')
    
    # Group by round_info value to see what we have
    from django.db.models import Count
    round_counts = PlayerMatch.objects.filter(
        round_info__regex=r'^\d+$'
    ).values('round_info').annotate(
        count=Count('id')
    ).order_by('round_info')
    
    print('\n📋 Numeric round_info found:')
    for item in round_counts:
        round_num = item['round_info']
        count = item['count']
        print(f'  - "{round_num}": {count} entries')
    
    return list(numeric_entries)

def fix_numeric_round_info():
    print('\n🔧 Converting numeric round_info to "Gameweek X" format...')
    
    # Find all numeric entries
    numeric_entries = PlayerMatch.objects.filter(round_info__regex=r'^\d+$')
    
    if numeric_entries.count() == 0:
        print('✅ No entries to fix')
        return 0
    
    updated_count = 0
    examples_shown = 0
    
    for entry in numeric_entries:
        old_format = entry.round_info
        new_format = f"Gameweek {old_format}"
        
        # Update the entry
        entry.round_info = new_format
        entry.save()
        updated_count += 1
        
        # Show first 10 examples
        if examples_shown < 10:
            print(f'  Updated: "{old_format}" → "{new_format}" (Player: {entry.player_name})')
            examples_shown += 1
        elif examples_shown == 10:
            print('  ... (showing first 10 examples)')
            examples_shown += 1
    
    print(f'\n✅ Updated {updated_count} entries to standard format')
    return updated_count

def verify_no_numeric_entries():
    print('\n🔍 Verifying no numeric entries remain...')
    
    # Check for any remaining numeric entries
    remaining = PlayerMatch.objects.filter(round_info__regex=r'^\d+$').count()
    
    if remaining == 0:
        print('✅ All entries successfully converted to "Gameweek X" format')
        return True
    else:
        print(f'❌ {remaining} numeric entries still remain')
        return False

def show_round_info_summary():
    print('\n📊 Final round_info format summary:')
    
    from django.db.models import Count
    round_formats = PlayerMatch.objects.values('round_info').annotate(
        count=Count('id')
    ).order_by('round_info')
    
    gameweek_count = 0
    other_count = 0
    
    for item in round_formats:
        round_info = item['round_info']
        count = item['count']
        
        if round_info.startswith('Gameweek'):
            gameweek_count += count
        else:
            other_count += count
            if other_count <= 10:  # Show first 10 non-standard formats
                print(f'  - Non-standard: "{round_info}": {count} entries')
    
    print(f'\n📈 Summary:')
    print(f'  - "Gameweek X" format: {gameweek_count} entries')
    print(f'  - Other formats: {other_count} entries')
    
    if other_count == 0:
        print('🎉 All entries now use standard "Gameweek X" format!')

if __name__ == '__main__':
    print('🚀 Starting Round Info Format Fix...')
    
    # Find numeric entries
    numeric_entries = find_numeric_round_info()
    
    if len(numeric_entries) > 0:
        # Ask for confirmation
        response = input(f'\nConvert {len(numeric_entries)} numeric entries to "Gameweek X" format? (y/N): ')
        
        if response.lower() == 'y':
            # Fix the entries
            fixed_count = fix_numeric_round_info()
            
            # Verify the fix
            if verify_no_numeric_entries():
                print('\n🎉 Round info format fix completed successfully!')
            else:
                print('\n⚠️  Some entries may not have been updated correctly.')
        else:
            print('Fix cancelled.')
    
    # Show final summary
    show_round_info_summary()