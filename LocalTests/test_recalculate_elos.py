#!/usr/bin/env python3
"""
Test script for the recalculate_player_elos functionality.
This script tests the Elo recalculation function and verifies data integrity.
"""

import os
import django
import requests
import json
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')
django.setup()

from MyApi.models import Player, PlayerMatch, EloCalculation
from collections import Counter

def test_recalculate_elos():
    """Test the recalculate Elo functionality comprehensively."""
    
    print("="*60)
    print("TESTING RECALCULATE ELO FUNCTIONALITY")
    print("="*60)
    
    # 1. Check initial database state
    print("\n1. INITIAL DATABASE STATE:")
    print("-" * 30)
    
    player_count = Player.objects.count()
    player_match_count = PlayerMatch.objects.count()
    elo_calc_count = EloCalculation.objects.count()
    
    print(f"Players in database: {player_count}")
    print(f"PlayerMatch records: {player_match_count}")
    print(f"EloCalculation records: {elo_calc_count}")
    
    # Sample some players with their current Elo
    sample_players = Player.objects.all()[:5]
    print(f"\nSample players before recalculation:")
    for player in sample_players:
        print(f"  {player.name}: Elo={player.elo}, Position={player.position}, Team={player.team}")
    
    # Check position and team distribution before
    positions_before = Counter(Player.objects.values_list('position', flat=True))
    teams_before = Counter(Player.objects.values_list('team', flat=True))
    print(f"\nPosition distribution before: {dict(positions_before)}")
    print(f"Unknown teams before: {teams_before.get('Unknown', 0)}")
    
    # 2. Test PlayerMatch data availability
    print("\n2. CHECKING PLAYERMATCH DATA:")
    print("-" * 30)
    
    # Get unique player names from PlayerMatch
    player_names_with_matches = set(PlayerMatch.objects.values_list('player_name', flat=True))
    player_names_in_db = set(Player.objects.values_list('name', flat=True))
    
    print(f"Unique players with match data: {len(player_names_with_matches)}")
    print(f"Players in Player table: {len(player_names_in_db)}")
    
    # Find overlap
    overlap = player_names_with_matches.intersection(player_names_in_db)
    print(f"Players with both Player record and match data: {len(overlap)}")
    
    # Sample some match data
    if PlayerMatch.objects.exists():
        sample_match = PlayerMatch.objects.first()
        print(f"\nSample PlayerMatch record:")
        print(f"  Player: {sample_match.player_name}")
        print(f"  Date: {sample_match.date}")
        print(f"  Points: {sample_match.points}")
        print(f"  Goals: {sample_match.goals}")
        print(f"  Assists: {sample_match.assists}")
        print(f"  Minutes: {sample_match.minutes_played}")
        print(f"  Elo after match: {sample_match.elo_after_match}")
        
        # Check if the model has elo_before_match field
        if hasattr(sample_match, 'elo_before_match'):
            print(f"  Elo before match: {sample_match.elo_before_match}")
        else:
            print("  ⚠️  PlayerMatch model missing 'elo_before_match' field")
    else:
        print("WARNING: No PlayerMatch records found!")
        return False
    
    # 3. Test the recalculate function via API
    print("\n3. TESTING RECALCULATE ELO API:")
    print("-" * 30)
    
    try:
        response = requests.post('http://127.0.0.1:8000/api/recalculate_elos/')
        print(f"API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"API Response: {json.dumps(result, indent=2)}")
            
            if result.get('success'):
                print(f"✅ SUCCESS: Updated {result.get('updated_count', 0)} players")
            else:
                print(f"❌ API Error: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure Django server is running on http://127.0.0.1:8000")
        return False
    except Exception as e:
        print(f"❌ Request Error: {str(e)}")
        return False
    
    # 4. Verify data integrity after recalculation
    print("\n4. VERIFYING DATA INTEGRITY:")
    print("-" * 30)
    
    # Check that positions and teams are preserved
    positions_after = Counter(Player.objects.values_list('position', flat=True))
    teams_after = Counter(Player.objects.values_list('team', flat=True))
    
    print(f"Position distribution after: {dict(positions_after)}")
    print(f"Unknown teams after: {teams_after.get('Unknown', 0)}")
    
    # Compare before and after
    if positions_before == positions_after:
        print("✅ Positions preserved correctly")
    else:
        print("❌ Positions were corrupted!")
        print(f"  Before: {dict(positions_before)}")
        print(f"  After: {dict(positions_after)}")
    
    if teams_before == teams_after:
        print("✅ Teams preserved correctly")
    else:
        print("❌ Teams were corrupted!")
        print(f"  Unknown teams before: {teams_before.get('Unknown', 0)}")
        print(f"  Unknown teams after: {teams_after.get('Unknown', 0)}")
    
    # 5. Check Elo changes
    print("\n5. CHECKING ELO CHANGES:")
    print("-" * 30)
    
    # Sample the same players after recalculation
    print(f"Sample players after recalculation:")
    for player in sample_players:
        player.refresh_from_db()  # Reload from database
        print(f"  {player.name}: Elo={player.elo}, Position={player.position}, Team={player.team}")
    
    # Check EloCalculation records
    elo_calc_count_after = EloCalculation.objects.count()
    print(f"\nEloCalculation records after: {elo_calc_count_after}")
    
    if elo_calc_count_after > elo_calc_count:
        print(f"✅ Added {elo_calc_count_after - elo_calc_count} new EloCalculation records")
    
    # Sample some EloCalculation records
    recent_elos = EloCalculation.objects.order_by('-id')[:3]
    print(f"\nRecent EloCalculation records:")
    for elo_calc in recent_elos:
        print(f"  {elo_calc.player_name}: Elo={elo_calc.elo}, Change={elo_calc.elo_change}, Matches={elo_calc.matches_played}")
    
    # 6. Test error cases
    print("\n6. TESTING ERROR HANDLING:")
    print("-" * 30)
    
    # Test GET request (should fail)
    try:
        get_response = requests.get('http://127.0.0.1:8000/api/recalculate_elos/')
        if get_response.status_code != 200:
            print("✅ GET request properly rejected")
        else:
            print("❌ GET request should have been rejected")
    except:
        print("✅ GET request properly handled")
    
    print("\n" + "="*60)
    print("TEST COMPLETED")
    print("="*60)
    
    return True

def test_specific_player_elo(player_name):
    """Test Elo calculation for a specific player."""
    print(f"\nDETAILED ELO TEST FOR: {player_name}")
    print("-" * 40)
    
    try:
        # Get player record
        player = Player.objects.get(name=player_name)
        print(f"Current Player record:")
        print(f"  Elo: {player.elo}")
        print(f"  Position: {player.position}")
        print(f"  Team: {player.team}")
        print(f"  Cost: {player.cost}")
        
        # Get match history
        matches = PlayerMatch.objects.filter(player_name=player_name).order_by('date')
        print(f"\nMatch history ({matches.count()} matches):")
        
        for i, match in enumerate(matches[:5]):  # Show first 5 matches
            print(f"  Match {i+1}: {match.date}")
            print(f"    Points: {match.points}, Goals: {match.goals}, Assists: {match.assists}")
            print(f"    Minutes: {match.minutes_played}")
            print(f"    Elo after match: {match.elo_after_match}")
            if hasattr(match, 'elo_before_match'):
                print(f"    Elo before match: {match.elo_before_match}")
            else:
                print(f"    ⚠️  Missing elo_before_match field")
        
        if matches.count() > 5:
            print(f"  ... and {matches.count() - 5} more matches")
        
        # Get EloCalculation record
        try:
            elo_calc = EloCalculation.objects.get(player_name=player_name)
            print(f"\nEloCalculation record:")
            print(f"  Current Elo: {elo_calc.elo}")
            print(f"  Previous Elo: {elo_calc.previous_elo}")
            print(f"  Elo Change: {elo_calc.elo_change}")
            print(f"  Matches Played: {elo_calc.matches_played}")
            print(f"  Last Match: {elo_calc.last_match_date}")
        except EloCalculation.DoesNotExist:
            print(f"\n❌ No EloCalculation record found for {player_name}")
        
    except Player.DoesNotExist:
        print(f"❌ Player '{player_name}' not found in database")

if __name__ == "__main__":
    # Run the main test
    success = test_recalculate_elos()
    
    if success:
        # Test specific players
        test_players = ["Erling Haaland", "Mohamed Salah", "Bruno Borges Fernandes"]
        for player_name in test_players:
            if Player.objects.filter(name=player_name).exists():
                test_specific_player_elo(player_name)
                break  # Just test one player in detail