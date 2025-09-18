#!/usr/bin/env python
"""
Fix Opponent Column - Convert Team IDs to Team Names

This script fixes the opponent column by converting numeric team IDs 
to actual team names for better readability.
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')
django.setup()

from MyApi.models import PlayerMatch
from django.db.models import Count

def analyze_opponent_data():
    print('🔍 Analyzing opponent column data...')
    
    from django.db.models import Count
    
    # Get all unique opponent values
    opponents = PlayerMatch.objects.values('opponent').annotate(
        count=Count('id')
    ).order_by('-count')
    
    print(f'\n📊 Found {opponents.count()} unique opponent values')
    
    numeric_opponents = 0
    text_opponents = 0
    
    print('\nTop opponent values:')
    for i, item in enumerate(opponents):
        opponent = item['opponent']
        count = item['count']
        
        # Check if it's numeric
        is_numeric = opponent and opponent.isdigit()
        if is_numeric:
            numeric_opponents += count
        else:
            text_opponents += count
        
        # Show top 20
        if i < 20:
            format_type = "🔢 Numeric ID" if is_numeric else "✅ Team Name"
            print(f'  {i+1:2d}. "{opponent}": {count:,} entries ({format_type})')
    
    print(f'\n📈 Summary:')
    print(f'  - Numeric IDs: {numeric_opponents:,} entries')
    print(f'  - Team names: {text_opponents:,} entries')
    
    return numeric_opponents > 0

def get_fpl_team_mapping():
    """Get mapping of FPL team IDs to team names"""
    # FPL 2024-25 season team mapping
    team_mapping = {
        '1': 'ARS',   # Arsenal
        '2': 'AVL',   # Aston Villa
        '3': 'BOU',   # Bournemouth
        '4': 'BRE',   # Brentford
        '5': 'BHA',   # Brighton
        '6': 'CHE',   # Chelsea
        '7': 'CRY',   # Crystal Palace
        '8': 'EVE',   # Everton
        '9': 'FUL',   # Fulham
        '10': 'IPS',  # Ipswich Town
        '11': 'LEI',  # Leicester City
        '12': 'LIV',  # Liverpool
        '13': 'MCI',  # Manchester City
        '14': 'MUN',  # Manchester United
        '15': 'NEW',  # Newcastle United
        '16': 'NFO',  # Nottingham Forest
        '17': 'SOU',  # Southampton
        '18': 'TOT',  # Tottenham
        '19': 'WHU',  # West Ham United
        '20': 'WOL',  # Wolverhampton Wanderers
    }
    
    return team_mapping

def fix_opponent_column():
    print('\n🔧 Converting team IDs to team names...')
    
    team_mapping = get_fpl_team_mapping()
    
    # Find entries with numeric opponents
    numeric_opponents = PlayerMatch.objects.filter(opponent__regex=r'^\d+$')
    
    if numeric_opponents.count() == 0:
        print('✅ No numeric opponent IDs found')
        return 0
    
    print(f'Found {numeric_opponents.count()} entries with numeric opponent IDs')
    
    updated_count = 0
    examples_shown = 0
    
    for entry in numeric_opponents:
        old_opponent = entry.opponent
        
        # Convert to team name
        if old_opponent in team_mapping:
            new_opponent = team_mapping[old_opponent]
            entry.opponent = new_opponent
            entry.save()
            updated_count += 1
            
            # Show first 10 examples
            if examples_shown < 10:
                print(f'  Updated: "{old_opponent}" → "{new_opponent}" (Player: {entry.player_name})')
                examples_shown += 1
            elif examples_shown == 10:
                print('  ... (showing first 10 examples)')
                examples_shown += 1
        else:
            print(f'  ⚠️  Unknown team ID: {old_opponent} (Player: {entry.player_name})')
    
    print(f'\n✅ Updated {updated_count} opponent entries')
    return updated_count

def verify_opponent_fix():
    print('\n🔍 Verifying opponent column fix...')
    
    # Check for remaining numeric opponents
    remaining_numeric = PlayerMatch.objects.filter(opponent__regex=r'^\d+$').count()
    
    if remaining_numeric == 0:
        print('✅ All numeric opponent IDs successfully converted')
    else:
        print(f'⚠️  {remaining_numeric} numeric opponent IDs still remain')
        
        # Show examples of remaining numeric IDs
        remaining_examples = PlayerMatch.objects.filter(
            opponent__regex=r'^\d+$'
        ).values('opponent').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        print('Remaining numeric IDs:')
        for item in remaining_examples:
            opponent = item['opponent']
            count = item['count']
            print(f'  - "{opponent}": {count} entries')
    
    return remaining_numeric == 0

def show_opponent_summary():
    print('\n📊 Final opponent column summary:')
    
    from django.db.models import Count
    
    # Get current opponent distribution
    opponents = PlayerMatch.objects.values('opponent').annotate(
        count=Count('id')
    ).order_by('-count')[:15]
    
    print('\nTop opponents after fix:')
    for i, item in enumerate(opponents, 1):
        opponent = item['opponent']
        count = item['count']
        is_numeric = opponent and opponent.isdigit()
        status = "🔢" if is_numeric else "✅"
        print(f'  {i:2d}. {status} "{opponent}": {count:,} entries')

if __name__ == '__main__':
    print('🚀 Starting Opponent Column Fix...')
    
    # Analyze current data
    has_numeric = analyze_opponent_data()
    
    if has_numeric:
        # Ask for confirmation
        response = input('\nConvert numeric team IDs to team names? (y/N): ')
        
        if response.lower() == 'y':
            # Fix the opponent column
            fixed_count = fix_opponent_column()
            
            # Verify the fix
            if verify_opponent_fix():
                print('\n🎉 Opponent column fix completed successfully!')
            else:
                print('\n⚠️  Some opponent IDs may not have been converted.')
        else:
            print('Fix cancelled.')
    else:
        print('\n✅ No numeric opponent IDs found to fix.')
    
    # Show final summary
    show_opponent_summary()