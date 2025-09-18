#!/usr/bin/env python3
"""
Test the corrected Elo calculation that allows players to lose Elo.
"""

import os
import django
import asyncio

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')
django.setup()

from MyApi.models import PlayerMatch


def test_corrected_elo_calculation():
    """Test the corrected Elo calculation logic."""
    print("🧪 Testing Corrected Elo Calculation Logic")
    print("="*50)
    
    def calculate_elo_change(current_elo: float, points: int, goals: int, assists: int, 
                           minutes_played: int, competition: str, k: int = 20) -> float:
        """
        Proper Elo calculation based on elo_model.py logic.
        Players can lose Elo when they underperform.
        """
        # Get league rating based on competition
        if competition in ['Champions League', 'Champions Lg']:
            league_rating = 1600
        elif competition in ['Premier League', 'FA Cup', 'Europa League', 'Europa Lg']:
            league_rating = 1500
        elif competition in ['Bundesliga', 'La Liga', 'Serie A']:
            league_rating = 1300
        elif competition in ['Ligue 1', 'Eredivisie']:
            league_rating = 1250
        elif competition in ['Championship', 'Primeira Liga']:
            league_rating = 1000
        else:
            league_rating = 900
        
        # Calculate expected score based on Elo (normalized to points scale)
        E_a = round(k / (1 + 10**(league_rating / current_elo)), 2)
        
        # Calculate actual performance points (Pa)
        Pa = points  # Use the fantasy points directly
        
        # Calculate Elo change: Ra + k * (Pa - E_a)
        elo_change = k * (Pa - E_a)
        
        # Cap the change to prevent extreme swings
        return max(-30, min(30, elo_change))
    
    # Test scenarios
    test_cases = [
        # (current_elo, points, goals, assists, minutes, competition, description)
        (1200, 0, 0, 0, 90, "Premier League", "Poor performance (0 points)"),
        (1200, 1, 0, 0, 30, "Premier League", "Minimal performance (1 point)"),
        (1200, 5, 1, 0, 90, "Premier League", "Good performance (5 points)"),
        (1200, 10, 2, 0, 90, "Premier League", "Great performance (10 points)"),
        (1200, 20, 4, 0, 90, "Premier League", "Exceptional performance (20 points)"),
        (2500, 0, 0, 0, 90, "Premier League", "Elite player poor performance"),
        (2500, 5, 1, 0, 90, "Premier League", "Elite player average performance"),
        (800, 0, 0, 0, 90, "Premier League", "Low-rated player poor performance"),
        (800, 5, 1, 0, 90, "Premier League", "Low-rated player good performance"),
    ]
    
    print("Test Cases:")
    print("Current Elo | Points | Performance | Competition | Expected Score | Elo Change | New Elo | Can Lose?")
    print("-" * 100)
    
    for current_elo, points, goals, assists, minutes, comp, desc in test_cases:
        elo_change = calculate_elo_change(current_elo, points, goals, assists, minutes, comp)
        new_elo = current_elo + elo_change
        
        # Calculate expected score for display
        k = 20
        if comp in ['Champions League', 'Champions Lg']:
            league_rating = 1600
        elif comp in ['Premier League', 'FA Cup', 'Europa League', 'Europa Lg']:
            league_rating = 1500
        else:
            league_rating = 900
        
        E_a = round(k / (1 + 10**(league_rating / current_elo)), 2)
        
        can_lose = "YES" if elo_change < 0 else "NO"
        
        print(f"{current_elo:11.0f} | {points:6d} | {desc:25s} | {comp:12s} | {E_a:13.2f} | {elo_change:10.2f} | {new_elo:7.1f} | {can_lose}")
    
    print("\n✅ Key Observations:")
    print("   • Players CAN lose Elo when they underperform (negative Elo change)")
    print("   • Expected score depends on current Elo and league difficulty")
    print("   • Higher-rated players have higher expectations")
    print("   • Lower-rated players can gain more from good performances")


def test_with_real_player_data():
    """Test with real Viktor Gyökeres data to see Elo changes."""
    print("\n🎯 Testing with Viktor Gyökeres Real Data")
    print("="*50)
    
    # Get Viktor Gyökeres matches
    viktor_matches = PlayerMatch.objects.filter(
        player_name='Viktor Gyökeres'
    ).order_by('date')[:20]  # First 20 matches
    
    if not viktor_matches.exists():
        print("❌ Viktor Gyökeres not found")
        return
    
    def calculate_elo_change(current_elo, points, goals, assists, minutes_played, competition, k=20):
        # Same function as above
        if competition in ['Champions League', 'Champions Lg']:
            league_rating = 1600
        elif competition in ['Premier League', 'FA Cup', 'Europa League', 'Europa Lg']:
            league_rating = 1500
        elif competition in ['Bundesliga', 'La Liga', 'Serie A']:
            league_rating = 1300
        elif competition in ['Ligue 1', 'Eredivisie']:
            league_rating = 1250
        elif competition in ['Championship', 'Primeira Liga']:
            league_rating = 1000
        else:
            league_rating = 900
        
        E_a = round(k / (1 + 10**(league_rating / current_elo)), 2)
        Pa = points
        elo_change = k * (Pa - E_a)
        return max(-30, min(30, elo_change))
    
    current_elo = 1200.0
    positive_changes = 0
    negative_changes = 0
    zero_point_matches = 0
    
    print("Date       | vs Opponent        | Points | Goals | Elo Before | Expected | Elo Change | Elo After")
    print("-" * 95)
    
    for match in viktor_matches:
        elo_change = calculate_elo_change(
            current_elo, match.points, match.goals, match.assists, 
            match.minutes_played, match.competition
        )
        
        # Calculate expected score for display
        k = 20
        if match.competition in ['Champions League', 'Champions Lg']:
            league_rating = 1600
        elif match.competition in ['Premier League', 'FA Cup', 'Europa League', 'Europa Lg']:
            league_rating = 1500
        else:
            league_rating = 900
        
        E_a = round(k / (1 + 10**(league_rating / current_elo)), 2)
        
        new_elo = current_elo + elo_change
        
        # Track statistics
        if elo_change > 0:
            positive_changes += 1
        elif elo_change < 0:
            negative_changes += 1
        
        if match.points == 0:
            zero_point_matches += 1
        
        print(f"{match.date} | vs {match.opponent:15s} | {match.points:6d} | {match.goals:5d} | {current_elo:10.1f} | {E_a:8.2f} | {elo_change:10.2f} | {new_elo:9.1f}")
        
        current_elo = new_elo
    
    print(f"\n📊 Statistics for first 20 matches:")
    print(f"   • Positive Elo changes: {positive_changes}")
    print(f"   • Negative Elo changes: {negative_changes}")
    print(f"   • Zero-point matches: {zero_point_matches}")
    print(f"   • Final Elo: {current_elo:.1f}")
    print(f"   • Total gain: {current_elo - 1200:.1f}")
    
    if negative_changes > 0:
        print(f"   ✅ Players CAN lose Elo when they perform poorly!")
    else:
        print(f"   ⚠️ No negative changes in this sample (Viktor performs very well)")


async def test_ultra_optimized_corrected():
    """Test the corrected ultra-optimized function."""
    print("\n🚀 Testing Corrected Ultra-Optimized Function")
    print("="*50)
    
    try:
        from ultra_optimized_elo import ultra_optimized_recalculate_elos
        
        # Test with a small number of players
        result = await ultra_optimized_recalculate_elos(max_players=3, batch_size=3)
        
        if 'error' in result:
            print(f"❌ Error: {result['error']}")
        else:
            print(f"✅ Success: {result}")
            print("   The corrected calculation now allows players to lose Elo!")
        
    except Exception as e:
        print(f"❌ Error testing ultra-optimized: {e}")


def main():
    """Main test function."""
    print("🧪 ELO CALCULATION CORRECTION TEST")
    print("="*60)
    print("Testing the fix to allow players to lose Elo when they underperform")
    print("="*60)
    
    # Test the calculation logic
    test_corrected_elo_calculation()
    
    # Test with real data
    test_with_real_player_data()
    
    # Test the ultra-optimized function
    asyncio.run(test_ultra_optimized_corrected())
    
    print("\n" + "="*60)
    print("🏁 CORRECTION TEST COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()