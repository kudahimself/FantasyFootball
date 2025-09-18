#!/usr/bin/env python3
"""
Intelligent Elo calculator that chooses the best method based on data size.
"""

import numpy as np
import pandas as pd
import time
from typing import List, Dict, Tuple, Any

class IntelligentEloCalculator:
    """
    Intelligent Elo calculator that chooses optimization strategy based on data size.
    """
    
    def __init__(self, starting_elo: float = 1200.0, 
                 optimization_threshold: int = 50):
        """
        Initialize the intelligent calculator.
        
        Args:
            starting_elo: Initial Elo rating
            optimization_threshold: Minimum matches per player to use vectorization
        """
        self.starting_elo = starting_elo
        self.optimization_threshold = optimization_threshold
        
        # Elo calculation parameters
        self.points_weight = 2.0
        self.goals_weight = 5.0
        self.assists_weight = 3.0
        self.min_elo_change = -30.0
        self.max_elo_change = 30.0
    
    def calculate_single_match_elo(self, points: int, goals: int, assists: int, 
                                  minutes_played: int, current_elo: float) -> float:
        """
        Calculate Elo change for a single match (fast, simple method).
        
        Args:
            points: Fantasy points
            goals: Goals scored
            assists: Assists
            minutes_played: Minutes played
            current_elo: Current Elo rating
            
        Returns:
            New Elo rating after the match
        """
        # Minutes bonus
        if minutes_played >= 90:
            minutes_bonus = 2
        elif minutes_played >= 60:
            minutes_bonus = 1
        elif minutes_played == 0:
            minutes_bonus = -2
        else:
            minutes_bonus = 0
        
        # Performance points
        performance_points = (
            points * self.points_weight +
            goals * self.goals_weight +
            assists * self.assists_weight +
            minutes_bonus
        )
        
        # Cap the Elo change
        elo_change = max(self.min_elo_change, min(self.max_elo_change, performance_points))
        
        return current_elo + elo_change
    
    def calculate_vectorized_elo(self, match_data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate Elo progression using vectorized operations (for large datasets).
        """
        if len(match_data) == 0:
            return np.array([]), np.array([])
        
        # Vectorized minutes bonus
        minutes_bonus = np.where(
            match_data['minutes_played'] >= 90, 2,
            np.where(
                match_data['minutes_played'] >= 60, 1,
                np.where(match_data['minutes_played'] == 0, -2, 0)
            )
        )
        
        # Vectorized performance points
        performance_points = (
            match_data['points'].values * self.points_weight +
            match_data['goals'].values * self.goals_weight +
            match_data['assists'].values * self.assists_weight +
            minutes_bonus
        )
        
        # Vectorized Elo changes
        elo_changes = np.clip(performance_points, self.min_elo_change, self.max_elo_change)
        
        # Calculate cumulative Elo progression
        elo_before = np.zeros(len(match_data))
        elo_after = np.zeros(len(match_data))
        
        elo_before[0] = self.starting_elo
        elo_after[0] = elo_before[0] + elo_changes[0]
        
        for i in range(1, len(match_data)):
            elo_before[i] = elo_after[i-1]
            elo_after[i] = elo_before[i] + elo_changes[i]
        
        return elo_before, elo_after
    
    def calculate_player_elo_intelligent(self, match_data: List[Dict]) -> Tuple[List[float], List[float], float]:
        """
        Intelligently choose calculation method based on data size.
        
        Args:
            match_data: List of match dictionaries
            
        Returns:
            Tuple of (elo_before_list, elo_after_list, final_elo)
        """
        if len(match_data) == 0:
            return [], [], self.starting_elo
        
        # Choose method based on data size
        if len(match_data) >= self.optimization_threshold:
            # Use vectorized method for large datasets
            df = pd.DataFrame(match_data)
            elo_before, elo_after = self.calculate_vectorized_elo(df)
            return elo_before.tolist(), elo_after.tolist(), float(elo_after[-1])
        else:
            # Use simple iterative method for small datasets
            elo_before = []
            elo_after = []
            current_elo = self.starting_elo
            
            for match in match_data:
                elo_before.append(current_elo)
                new_elo = self.calculate_single_match_elo(
                    match['points'], match['goals'], match['assists'],
                    match['minutes_played'], current_elo
                )
                elo_after.append(new_elo)
                current_elo = new_elo
            
            return elo_before, elo_after, current_elo


def test_intelligent_calculator():
    """
    Test the intelligent calculator against both methods.
    """
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')
    import django
    django.setup()
    
    from MyApi.models import PlayerMatch
    
    print("="*60)
    print("TESTING INTELLIGENT ELO CALCULATOR")
    print("="*60)
    
    # Get test data
    sample_players = list(PlayerMatch.objects.values_list('player_name', flat=True).distinct()[:5])
    
    calculator = IntelligentEloCalculator(optimization_threshold=20)  # Use vectorization for 20+ matches
    
    total_simple_time = 0
    total_vectorized_time = 0
    total_intelligent_time = 0
    
    for player_name in sample_players:
        matches = list(PlayerMatch.objects.filter(player_name=player_name).order_by('date').values(
            'points', 'goals', 'assists', 'minutes_played'
        ))
        
        if not matches:
            continue
        
        print(f"\nTesting {player_name} ({len(matches)} matches):")
        
        # Test simple method
        start = time.time()
        simple_before, simple_after, simple_final = [], [], 1200.0
        current_elo = 1200.0
        for match in matches:
            simple_before.append(current_elo)
            new_elo = calculator.calculate_single_match_elo(
                match['points'], match['goals'], match['assists'],
                match['minutes_played'], current_elo
            )
            simple_after.append(new_elo)
            current_elo = new_elo
        simple_final = current_elo
        simple_time = time.time() - start
        total_simple_time += simple_time
        
        # Test vectorized method
        start = time.time()
        df = pd.DataFrame(matches)
        vec_before, vec_after = calculator.calculate_vectorized_elo(df)
        vec_final = float(vec_after[-1]) if len(vec_after) > 0 else 1200.0
        vectorized_time = time.time() - start
        total_vectorized_time += vectorized_time
        
        # Test intelligent method
        start = time.time()
        int_before, int_after, int_final = calculator.calculate_player_elo_intelligent(matches)
        intelligent_time = time.time() - start
        total_intelligent_time += intelligent_time
        
        # Check accuracy
        accuracy_ok = abs(simple_final - int_final) < 0.001
        
        print(f"  Simple:      {simple_time:.6f}s -> Final Elo: {simple_final:.2f}")
        print(f"  Vectorized:  {vectorized_time:.6f}s -> Final Elo: {vec_final:.2f}")
        print(f"  Intelligent: {intelligent_time:.6f}s -> Final Elo: {int_final:.2f}")
        print(f"  Accuracy:    {'✅' if accuracy_ok else '❌'}")
        print(f"  Method used: {'Vectorized' if len(matches) >= calculator.optimization_threshold else 'Simple'}")
    
    print(f"\n" + "="*60)
    print("OVERALL PERFORMANCE:")
    print(f"Simple total:      {total_simple_time:.6f}s")
    print(f"Vectorized total:  {total_vectorized_time:.6f}s")
    print(f"Intelligent total: {total_intelligent_time:.6f}s")
    
    simple_speedup = total_simple_time / total_intelligent_time if total_intelligent_time > 0 else 1
    vec_speedup = total_vectorized_time / total_intelligent_time if total_intelligent_time > 0 else 1
    
    print(f"Intelligent vs Simple:     {simple_speedup:.2f}x")
    print(f"Intelligent vs Vectorized: {vec_speedup:.2f}x")
    
    if simple_speedup >= 1.0 and vec_speedup >= 1.0:
        print("🎉 Intelligent method is optimal!")
    else:
        print("⚠️  Need to adjust thresholds")
    
    return calculator


if __name__ == "__main__":
    test_intelligent_calculator()