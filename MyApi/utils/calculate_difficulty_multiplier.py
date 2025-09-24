"""
Difficulty Multiplier Calculator for 2025-2026 Season

This module calculates fixture difficulty multipliers by analyzing actual player performance
against different FPL difficulty rated opponents in the 2025-2026 season. It uses the 
existing FPL difficulty ratings from PlayerFixture model and the Elo calculator formula 
to determine expected points and compares them with actual points to derive accurate 
difficulty multipliers.

The analysis only considers players who started games (minutes_played > 0) to ensure
accurate performance metrics.
"""

import os
import django
from typing import Dict, List, Tuple, Any
from collections import defaultdict
import statistics

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')
django.setup()

from MyApi.models import PlayerMatch, PlayerFixture


def get_opponent_difficulty_mapping() -> Dict[str, int]:
    """
    Build a mapping from opponent team short name to FPL difficulty rating
    using PlayerFixture data and TEAM_ALIASES mapping.
    Returns:
        Dict[str, int]: e.g. {'LIV': 2, 'MCI': 5, ...}
    """
    TEAM_ALIASES = {
        'LIV': '12',
        'MCI': '13',
        'MUN': '14',
        'ARS': '1',
        'CHE': '7',
        'TOT': '18',
        'NEW': '15',
        'AVL': '2',
        'BHA': '6',
        'WHU': '19',
        'FUL': '10',
        'CRY': '8',
        'BRE': '5',
        'BOU': '4',
        'WOL': '20',
        'EVE': '9',
        'NFO': '16',
        'BUR': '3',
        'SUN': '17',
        'LEE': '11',
        # Add more aliases as needed
    }
    # Reverse mapping: team_id -> short_name
    ID_TO_SHORT = {v: k for k, v in TEAM_ALIASES.items()}
    print(ID_TO_SHORT, 'ID_TO_SHORT')

    mapping = {}
    # Get all unique (opponent_team_id, difficulty) pairs from PlayerFixture
    fixtures = PlayerFixture.objects.values_list('opponent', 'difficulty').distinct()
    print(fixtures)
    for team_id, difficulty in fixtures:
        print('\n')
        print('team_id',team_id,
              'difficulty',difficulty)
        short_name = ID_TO_SHORT[team_id]
        print(short_name)
        if short_name and difficulty:
            mapping[short_name] = difficulty
    
    print(mapping)
    return mapping
    



def calculate_expected_points(elo: float, opponent_difficulty: int, competition: str = 'Premier League') -> float:
    """
    Calculate expected points using the Elo calculator formula.
    
    This uses the exact same formula from elo_calculator.py:
    E_a = k/(1 + 10**(League_Rating/Ra))
    
    Args:
        elo: Player's Elo rating before the match
        opponent_difficulty: FPL difficulty level (1-5)
        competition: Competition name (default: Premier League)
    
    Returns:
        Expected points for the player
    """
    # League ratings from elo_calculator.py
    if competition == 'Champions League' or competition == 'Champions Lg':
        League_Rating = 1600
    elif competition in ['Premier League', 'FA Cup', 'Europa League']:
        League_Rating = 1500
    elif competition in ['Bundesliga', 'La Liga', 'Serie A']:
        League_Rating = 1300
    elif competition in ['Ligue 1', 'Eredivisie']:
        League_Rating = 1250
    elif competition in ['Championship', 'Primeira Liga']:
        League_Rating = 1000
    else:
        League_Rating = 900
    
    # K-factor from elo_calculator.py
    k = 20
    
    # Expected score formula from elo_calculator.py (no adjustment needed here)
    E_a = round(k / (1 + 10**(League_Rating / elo)), 2)
    
    return E_a


def analyze_difficulty_multipliers() -> Dict[int, float]:
    """
    Analyze actual vs expected performance to calculate difficulty multipliers.
    
    Returns:
        Dictionary mapping FPL difficulty levels (1-5) to multipliers
    """
    print("Analyzing 2025-2026 season data to calculate difficulty multipliers...")
    
    # Get opponent difficulty mapping from FPL data
    print("Getting FPL difficulty ratings...")
    opponent_difficulties = get_opponent_difficulty_mapping()
    print(opponent_difficulties)
    
    if not opponent_difficulties:
        print("No FPL difficulty data found")
        return {}
    
    print(f"Found FPL difficulty ratings for {len(opponent_difficulties)} opponents")
    
    # Display the difficulty mapping
    print("\nFPL Difficulty Ratings by Opponent:")
    difficulty_groups = defaultdict(list)
    for opponent, difficulty in opponent_difficulties.items():
        difficulty_groups[difficulty].append(opponent)
    
    difficulty_names = {
        1: "Very Easy",
        2: "Easy", 
        3: "Average",
        4: "Hard",
        5: "Very Hard"
    }
    
    for difficulty in range(1, 6):
        teams = difficulty_groups[difficulty]
        if teams:
            print(f"  Difficulty {difficulty} ({difficulty_names[difficulty]}): {', '.join(teams)}")
    
    # Analyze performance by difficulty level
    difficulty_analysis = defaultdict(list)
    
    # Get all matches from 2025-2026 season where players started
    matches = PlayerMatch.objects.filter(
        season='2025-2026',
        minutes_played__gt=0,
        elo_before_match__isnull=False,
        points__isnull=False
    )
    
    print(f"\nAnalyzing {matches.count()} matches where players started...")
    
    processed = 0
    for match in matches:
        if match.opponent in opponent_difficulties:
            difficulty = opponent_difficulties[match.opponent]
            
            # Calculate expected points using Elo formula (without difficulty adjustment)
            expected_points = calculate_expected_points(
                match.elo_before_match, 
                difficulty, 
                match.competition
            )
            
            actual_points = match.points
            
            # Only include meaningful data points
            if expected_points > 0:
                performance_ratio = actual_points / expected_points
                difficulty_analysis[difficulty].append(performance_ratio)
                processed += 1
    
    print(f"Processed {processed} valid match performances")
    
    # Calculate multipliers for each difficulty level
    multipliers = {}
    
    print(f"\nDifficulty Analysis Results:")
    for difficulty in range(1, 6):
        if difficulty in difficulty_analysis and len(difficulty_analysis[difficulty]) > 0:
            # Use median to avoid outlier effects
            ratios = difficulty_analysis[difficulty]
            median_ratio = statistics.median(ratios)
            mean_ratio = statistics.mean(ratios)
            multipliers[difficulty] = round(median_ratio, 1)
            
            print(f"  Difficulty {difficulty} ({difficulty_names[difficulty]}): {len(ratios)} samples")
            print(f"    Median ratio: {median_ratio:.2f}, Mean ratio: {mean_ratio:.2f}")
            print(f"    Suggested multiplier: {multipliers[difficulty]}")
        else:
            # Fallback to default values if no data
            default_multipliers = {1: 1.8, 2: 1.6, 3: 1.0, 4: 0.7, 5: 0.4}
            multipliers[difficulty] = default_multipliers[difficulty]
            print(f"  Difficulty {difficulty} ({difficulty_names[difficulty]}): No data, using default {default_multipliers[difficulty]}")
    
    return multipliers


def main():
    """
    Main function to calculate and display difficulty multipliers.
    """
    print("Starting Difficulty Multiplier Calculation for 2025-2026 Season")
    print("Using existing FPL difficulty ratings from PlayerFixture data")
    print("="*70)
    
    try:
        # Calculate multipliers
        multipliers = analyze_difficulty_multipliers()
        
        if multipliers:
            print("\n" + "="*50)
            print("CALCULATED DIFFICULTY MULTIPLIERS")
            print("="*50)
            
            difficulty_names = {
                1: "Very Easy Fixtures",
                2: "Easy Fixtures", 
                3: "Average Fixtures",
                4: "Hard Fixtures",
                5: "Very Hard Fixtures"
            }
            
            for difficulty in range(1, 6):
                multiplier = multipliers.get(difficulty, 1.0)
                name = difficulty_names[difficulty]
                print(f"{difficulty}: {multiplier:4.1f}  # {name}")
            
            print("\n" + "="*50)
            print("PYTHON DICTIONARY FORMAT")
            print("="*50)
            print("difficulty_multipliers = {")
            for difficulty in range(1, 6):
                multiplier = multipliers.get(difficulty, 1.0)
                name = difficulty_names[difficulty]
                print(f"    {difficulty}: {multiplier},  # {name}")
            print("}")
            
        else:
            print("Failed to calculate multipliers - no valid data found")
            
    except Exception as e:
        print(f"Error calculating difficulty multipliers: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()


def get_team_strength_ratings() -> Dict[str, float]:
    """
    Calculate team strength ratings based on average Elo of opponents faced.
    Returns a dictionary mapping team names to their strength ratings.
    """
    from django.db.models import Avg
    
    # Get average Elo ratings for each team based on their players' performance
    team_strengths = {}
    
    # Get all matches from 2025-2026 season where players started
    matches = PlayerMatch.objects.filter(
        season='2025-2026',
        minutes_played__gt=0
    )
    
    # Calculate average points scored against each team
    team_points_against = defaultdict(list)
    
    for match in matches:
        if match.points is not None and match.opponent:
            team_points_against[match.opponent].append(match.points)
    
    # Calculate team strength based on average points conceded (lower = stronger)
    for team, points_list in team_points_against.items():
        avg_points_conceded = statistics.mean(points_list)
        # Invert so higher rating = stronger team (concedes fewer points)
        team_strengths[team] = 1.0 / (avg_points_conceded + 1.0) if avg_points_conceded > 0 else 0.5
    
    return team_strengths


def categorize_fixtures_by_difficulty(team_strengths: Dict[str, float]) -> Dict[str, int]:
    """
    Categorize each team into difficulty levels 1-5 based on their strength ratings.
    
    Returns:
        Dict mapping team names to difficulty levels (1=Very Easy, 5=Very Hard)
    """
    if not team_strengths:
        return {}
    
    # Sort teams by strength (weakest to strongest)
    sorted_teams = sorted(team_strengths.items(), key=lambda x: x[1])
    total_teams = len(sorted_teams)
    
    team_difficulties = {}
    
    for i, (team, strength) in enumerate(sorted_teams):
        # Divide into 5 roughly equal groups
        percentile = i / total_teams
        
        if percentile < 0.2:
            difficulty = 1  # Very Easy (bottom 20% - weakest teams)
        elif percentile < 0.4:
            difficulty = 2  # Easy (next 20%)
        elif percentile < 0.6:
            difficulty = 3  # Average (middle 20%)
        elif percentile < 0.8:
            difficulty = 4  # Hard (next 20%)
        else:
            difficulty = 5  # Very Hard (top 20% - strongest teams)
        
        team_difficulties[team] = difficulty
    
    return team_difficulties


def calculate_expected_points(elo: float, opponent_difficulty: int, competition: str = 'Premier League') -> float:
    """
    Calculate expected points using the Elo calculator formula.
    
    This uses the exact same formula from elo_calculator.py:
    E_a = k/(1 + 10**(League_Rating/Ra))
    
    Args:
        elo: Player's Elo rating before the match
        opponent_difficulty: Difficulty level (1-5)
        competition: Competition name (default: Premier League)
    
    Returns:
        Expected points for the player
    """
    # League ratings from elo_calculator.py
    if competition == 'Champions League' or competition == 'Champions Lg':
        League_Rating = 1600
    elif competition in ['Premier League', 'FA Cup', 'Europa League']:
        League_Rating = 1500
    elif competition in ['Bundesliga', 'La Liga', 'Serie A']:
        League_Rating = 1300
    elif competition in ['Ligue 1', 'Eredivisie']:
        League_Rating = 1250
    elif competition in ['Championship', 'Primeira Liga']:
        League_Rating = 1000
    else:
        League_Rating = 900
    
    # Adjust league rating based on opponent difficulty
    # Stronger opponents (higher difficulty) increase the effective league rating
    difficulty_adjustments = {
        1: -200,  # Very easy fixtures - reduce league rating
        2: -100,  # Easy fixtures
        3: 0,     # Average fixtures - no adjustment
        4: 100,   # Hard fixtures - increase league rating
        5: 200    # Very hard fixtures
    }
    
    adjusted_league_rating = League_Rating + difficulty_adjustments.get(opponent_difficulty, 0)
    
    # K-factor from elo_calculator.py
    k = 20
    
    # Expected score formula from elo_calculator.py
    E_a = round(k / (1 + 10**(adjusted_league_rating / elo)), 2)
    
    return E_a


def analyze_difficulty_multipliers() -> Dict[int, float]:
    """
    Analyze actual vs expected performance to calculate difficulty multipliers.
    
    Returns:
        Dictionary mapping difficulty levels (1-5) to multipliers
    """
    print("🔍 Analyzing 2025-2026 season data to calculate difficulty multipliers...")
    
    # Get team strength ratings
    print("📊 Calculating team strength ratings...")
    team_strengths = get_team_strength_ratings()
    
    if not team_strengths:
        print("❌ No team strength data found")
        return {}
    
    print(f"✅ Calculated strength ratings for {len(team_strengths)} teams")
    
    # Categorize fixtures by difficulty
    team_difficulties = categorize_fixtures_by_difficulty(team_strengths)
    
    # Analyze performance by difficulty level
    difficulty_analysis = defaultdict(list)
    
    # Get all matches from 2025-2026 season where players started
    matches = PlayerMatch.objects.filter(
        season='2025-2026',
        minutes_played__gt=0,
        elo_before_match__isnull=False,
        points__isnull=False
    )
    
    print(f"📈 Analyzing {matches.count()} matches where players started...")
    
    processed = 0
    for match in matches:
        if match.opponent in team_difficulties:
            difficulty = team_difficulties[match.opponent]
            
            # Calculate expected points using Elo formula
            expected_points = calculate_expected_points(
                match.elo_before_match, 
                difficulty, 
                match.competition
            )
            
            actual_points = match.points
            
            # Only include meaningful data points
            if expected_points > 0:
                performance_ratio = actual_points / expected_points
                difficulty_analysis[difficulty].append(performance_ratio)
                processed += 1
    
    print(f"✅ Processed {processed} valid match performances")
    
    # Calculate multipliers for each difficulty level
    multipliers = {}
    
    for difficulty in range(1, 6):
        if difficulty in difficulty_analysis and len(difficulty_analysis[difficulty]) > 0:
            # Use median to avoid outlier effects
            ratios = difficulty_analysis[difficulty]
            median_ratio = statistics.median(ratios)
            multipliers[difficulty] = round(median_ratio, 1)
            
            print(f"Difficulty {difficulty}: {len(ratios)} samples, median ratio: {median_ratio:.2f}")
        else:
            # Fallback to default values if no data
            default_multipliers = {1: 1.8, 2: 1.6, 3: 1.0, 4: 0.7, 5: 0.4}
            multipliers[difficulty] = default_multipliers[difficulty]
            print(f"Difficulty {difficulty}: No data, using default {default_multipliers[difficulty]}")
    
    return multipliers


def display_team_analysis(team_strengths: Dict[str, float], team_difficulties: Dict[str, int]):
    """
    Display analysis of team strengths and difficulty categorizations.
    """
    print("\n" + "="*60)
    print("TEAM STRENGTH ANALYSIS")
    print("="*60)
    
    # Group teams by difficulty level
    difficulty_groups = defaultdict(list)
    for team, difficulty in team_difficulties.items():
        strength = team_strengths.get(team, 0.0)
        difficulty_groups[difficulty].append((team, strength))
    
    difficulty_names = {
        1: "Very Easy Fixtures",
        2: "Easy Fixtures", 
        3: "Average Fixtures",
        4: "Hard Fixtures",
        5: "Very Hard Fixtures"
    }
    
    for difficulty in range(1, 6):
        teams = difficulty_groups[difficulty]
        if teams:
            print(f"\n{difficulty_names[difficulty]} (Level {difficulty}):")
            # Sort by strength within each group
            teams.sort(key=lambda x: x[1])
            for team, strength in teams:
                print(f"  {team:<20} (Strength: {strength:.3f})")


def main():
    """
    Main function to calculate and display difficulty multipliers.
    """
    print("🚀 Starting Difficulty Multiplier Calculation for 2025-2026 Season")
    print("="*70)
    
    try:
        # Calculate multipliers
        multipliers = analyze_difficulty_multipliers()
        
        if multipliers:
            print("\n" + "="*40)
            print("CALCULATED DIFFICULTY MULTIPLIERS")
            print("="*40)
            
            difficulty_names = {
                1: "Very Easy Fixtures",
                2: "Easy Fixtures", 
                3: "Average Fixtures",
                4: "Hard Fixtures",
                5: "Very Hard Fixtures"
            }
            
            for difficulty in range(1, 6):
                multiplier = multipliers.get(difficulty, 1.0)
                name = difficulty_names[difficulty]
                print(f"{difficulty}: {multiplier:4.1f}  # {name}")
            
            print("\n" + "="*40)
            print("PYTHON DICTIONARY FORMAT")
            print("="*40)
            print("difficulty_multipliers = {")
            for difficulty in range(1, 6):
                multiplier = multipliers.get(difficulty, 1.0)
                name = difficulty_names[difficulty]
                print(f"    {difficulty}: {multiplier},  # {name}")
            print("}")
            
            # Also display team analysis
            team_strengths = get_team_strength_ratings()
            team_difficulties = categorize_fixtures_by_difficulty(team_strengths)
            display_team_analysis(team_strengths, team_difficulties)
            
        else:
            print("❌ Failed to calculate multipliers - no valid data found")
            
    except Exception as e:
        print(f"❌ Error calculating difficulty multipliers: {e}")
        import traceback
        traceback.print_exc()


def recalculate_difficulty_multipliers() -> Dict[str, Any]:
    """
    Recalculate difficulty multipliers using current season data.
    Returns a dictionary with success status, matches processed, and calculated multipliers.
    """
    try:
        print("🔄 Starting difficulty multiplier recalculation...")
        
        # Get opponent difficulty mapping
        opponent_difficulties = get_opponent_difficulty_mapping()
        print(f"📊 Found difficulty ratings for {len(opponent_difficulties)} opponents")
        
        # Get 2025-2026 season match data for players who started
        # We'll get the last 4 games for each player
        from django.db.models import Q
        
        # Get all players who have matches in 2025-2026 season
        # Handle possible season string variations like '2025-26' or '2025-2026'
        players_with_matches = PlayerMatch.objects.filter(
            Q(season='2025-2026') | Q(season='2025-26'),
            minutes_played__gt=0
        ).values_list('player_name', flat=True).distinct()
        
        print(f"🎯 Found {len(players_with_matches)} players with matches in 2025-2026 season")
        print("📊 Analyzing last 4 games for each player to calculate difficulty multipliers...")
        
        if len(players_with_matches) == 0:
            return {
                'success': False,
                'error': 'No players found with match data for 2025-2026 season'
            }
        
        # Group matches by difficulty rating
        difficulty_data = defaultdict(list)
        processed_matches = 0
        
        for player_name in players_with_matches:
            # Get last 4 games for this player (most recent first)
            last_4_games = PlayerMatch.objects.filter(
                player_name=player_name,
                season='2025-26',
                minutes_played__gt=0,
                elo_before_match__isnull=False,
                points__isnull=False
            ).order_by('-date')[:4]
            
            
            for match in last_4_games:
                # Try to match opponent with difficulty rating
                opponent_difficulty = None
                
                # Direct match attempt
                if match.opponent in opponent_difficulties:
                    opponent_difficulty = opponent_difficulties[match.opponent]
                else:
                    # Try partial matching for different formats
                    for opp_name, difficulty in opponent_difficulties.items():
                        if match.opponent.lower() in opp_name.lower() or opp_name.lower() in match.opponent.lower():
                            opponent_difficulty = difficulty
                            break
                
                if opponent_difficulty is not None and match.elo_before_match:
                    # Calculate expected points using Elo formula
                    expected_points = calculate_expected_points(match.elo_before_match, 'Premier League')
                    
                    if expected_points > 0:
                        # Calculate performance ratio
                        performance_ratio = match.points / expected_points
                        difficulty_data[opponent_difficulty].append(performance_ratio)
                        processed_matches += 1
        
        print(f"✅ Processed {processed_matches} valid matches from last 4 games of each player")
        
        if processed_matches == 0:
            return {
                'success': False,
                'error': 'No valid matches could be processed'
            }
        
        # Calculate multipliers for each difficulty level
        difficulty_multipliers = {}
        sample_sizes = {}
        
        for difficulty, ratios in difficulty_data.items():
            if len(ratios) >= 10:  # Minimum sample size
                median_ratio = statistics.median(ratios)
                difficulty_multipliers[difficulty] = round(median_ratio, 1)
                sample_sizes[difficulty] = len(ratios)
                print(f"📈 Difficulty {difficulty}: {len(ratios)} samples, median ratio: {median_ratio:.2f}")
        
        # Fill in missing difficulties with logical defaults based on trend
        if difficulty_multipliers:
            # Fill in missing values
            all_difficulties = {1: 3.2, 2: 2.8, 3: 2.1, 4: 1.9, 5: 1.5}  # Logical defaults
            
            for diff in range(1, 6):
                if diff not in difficulty_multipliers:
                    difficulty_multipliers[diff] = all_difficulties[diff]
                    sample_sizes[diff] = 0
                    print(f"🔧 Using default for Difficulty {diff}: {all_difficulties[diff]}")
        
        # Save multipliers to database
        try:
            from MyApi.models import DifficultyMultiplier
            DifficultyMultiplier.update_multipliers(difficulty_multipliers, sample_sizes)
            print("💾 Multipliers saved to database successfully!")
        except Exception as e:
            print(f"⚠️ Warning: Could not save multipliers to database: {e}")
        
        print("✅ Difficulty multipliers recalculated successfully!")
        print("📊 Final multipliers:")
        for diff in sorted(difficulty_multipliers.keys()):
            print(f"   Difficulty {diff}: {difficulty_multipliers[diff]}x")
        
        return {
            'success': True,
            'matches_processed': processed_matches,
            'multipliers': difficulty_multipliers,
            'sample_sizes': sample_sizes,
            'message': 'Difficulty multipliers successfully recalculated and saved'
        }
        
    except Exception as e:
        print(f"❌ Error recalculating difficulty multipliers: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }


if __name__ == "__main__":
    main()
