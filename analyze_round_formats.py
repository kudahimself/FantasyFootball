#!/usr/bin/env python
"""
Analyze Round Info Formats

This script analyzes all the different round_info formats in the database
to understand what needs to be standardized.
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')
django.setup()

from MyApi.models import PlayerMatch

def analyze_round_info_formats():
    print('🔍 Analyzing all round_info formats...')
    
    from django.db.models import Count
    
    # Get all unique round_info values with counts
    round_formats = PlayerMatch.objects.values('round_info').annotate(
        count=Count('id')
    ).order_by('-count')
    
    print(f'\n📊 Found {round_formats.count()} unique round_info formats')
    print('\nTop formats by frequency:')
    
    gameweek_total = 0
    other_total = 0
    
    for i, item in enumerate(round_formats):
        round_info = item['round_info']
        count = item['count']
        
        if round_info and round_info.startswith('Gameweek'):
            gameweek_total += count
        else:
            other_total += count
        
        # Show top 20 formats
        if i < 20:
            format_type = "✅ Standard" if round_info and round_info.startswith('Gameweek') else "⚠️  Other"
            print(f'  {i+1:2d}. "{round_info}": {count:,} entries ({format_type})')
    
    print(f'\n📈 Summary:')
    print(f'  - "Gameweek X" format: {gameweek_total:,} entries')
    print(f'  - Other formats: {other_total:,} entries')
    
    # Look for specific patterns that could be converted
    print('\n🔍 Analyzing convertible patterns...')
    
    # Check for variations that could be standardized
    patterns_to_check = [
        ('Matchweek', 'Starts with "Matchweek"'),
        ('GW', 'Contains "GW"'),
        ('Week', 'Contains "Week"'),
        ('Round', 'Contains "Round"'),
        ('', 'Empty/null values'),
    ]
    
    for pattern, description in patterns_to_check:
        if pattern == '':
            # Check for empty/null values
            count = PlayerMatch.objects.filter(round_info__isnull=True).count()
            count += PlayerMatch.objects.filter(round_info='').count()
        else:
            count = PlayerMatch.objects.filter(round_info__icontains=pattern).count()
        
        if count > 0:
            print(f'  - {description}: {count:,} entries')
    
    # Show some examples of non-standard formats
    print('\n📋 Examples of non-standard formats:')
    non_standard = PlayerMatch.objects.exclude(
        round_info__startswith='Gameweek'
    ).values('round_info').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    for item in non_standard:
        round_info = item['round_info']
        count = item['count']
        print(f'  - "{round_info}": {count:,} entries')

if __name__ == '__main__':
    analyze_round_info_formats()