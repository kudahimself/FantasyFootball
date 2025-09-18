#!/usr/bin/env python3
"""
Optimized Elo calculation using NumPy and optimization libraries.
This module provides vectorized calculations for better performance.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple
import time

class OptimizedEloCalculator:
    """
    Optimized Elo calculator using vectorized operations.
    """
    
    def __init__(self, starting_elo: float = 1200.0, 
                 points_weight: float = 2.0,
                 goals_weight: float = 5.0,
                 assists_weight: float = 3.0,
                 min_elo_change: float = -30.0,
                 max_elo_change: float = 30.0):
        """
        Initialize the optimized Elo calculator.
        
        Args:
            starting_elo: Initial Elo rating for new players
            points_weight: Weight for fantasy points in Elo calculation
            goals_weight: Weight for goals in Elo calculation
            assists_weight: Weight for assists in Elo calculation
            min_elo_change: Minimum Elo change per match
            max_elo_change: Maximum Elo change per match
        """
        self.starting_elo = starting_elo
        self.points_weight = points_weight
        self.goals_weight = goals_weight
        self.assists_weight = assists_weight
        self.min_elo_change = min_elo_change
        self.max_elo_change = max_elo_change
    
    def calculate_minutes_bonus(self, minutes_array: np.ndarray) -> np.ndarray:
        """
        Vectorized calculation of minutes bonus.
        
        Args:
            minutes_array: Array of minutes played values
            
        Returns:
            Array of minute bonuses
        """
        return np.where(
            minutes_array >= 90, 2,
            np.where(
                minutes_array >= 60, 1,
                np.where(minutes_array == 0, -2, 0)
            )
        )
    
    def calculate_performance_points(self, match_data: pd.DataFrame) -> np.ndarray:
        """
        Vectorized calculation of performance points.
        
        Args:
            match_data: DataFrame with columns: points, goals, assists, minutes_played
            
        Returns:
            Array of performance points
        """
        minutes_bonus = self.calculate_minutes_bonus(match_data['minutes_played'].values)
        
        performance_points = (
            match_data['points'].values * self.points_weight +
            match_data['goals'].values * self.goals_weight +
            match_data['assists'].values * self.assists_weight +
            minutes_bonus
        )
        
        return performance_points
    
    def calculate_elo_changes(self, performance_points: np.ndarray) -> np.ndarray:
        """
        Vectorized calculation of Elo changes with capping.
        
        Args:
            performance_points: Array of performance points
            
        Returns:
            Array of capped Elo changes
        """
        return np.clip(performance_points, self.min_elo_change, self.max_elo_change)
    
    def calculate_player_elo_history(self, match_data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate Elo progression for a single player using vectorized operations.
        
        Args:
            match_data: DataFrame with player's match data, sorted by date
            
        Returns:
            Tuple of (elo_before_array, elo_after_array)
        """
        if len(match_data) == 0:
            return np.array([]), np.array([])
        
        # Calculate performance points vectorized
        performance_points = self.calculate_performance_points(match_data)
        
        # Calculate Elo changes vectorized
        elo_changes = self.calculate_elo_changes(performance_points)
        
        # Calculate cumulative Elo progression
        elo_before = np.zeros(len(match_data))
        elo_after = np.zeros(len(match_data))
        
        elo_before[0] = self.starting_elo
        elo_after[0] = elo_before[0] + elo_changes[0]
        
        for i in range(1, len(match_data)):
            elo_before[i] = elo_after[i-1]
            elo_after[i] = elo_before[i] + elo_changes[i]
        
        return elo_before, elo_after
    
    def calculate_batch_elos(self, all_match_data: Dict[str, pd.DataFrame]) -> Dict[str, Dict]:
        """
        Calculate Elos for multiple players in batch.
        
        Args:
            all_match_data: Dict mapping player_name -> DataFrame of matches
            
        Returns:
            Dict mapping player_name -> {'elo_before': array, 'elo_after': array, 'final_elo': float}
        """
        results = {}
        
        for player_name, match_data in all_match_data.items():
            if len(match_data) == 0:
                continue
                
            elo_before, elo_after = self.calculate_player_elo_history(match_data)
            
            results[player_name] = {
                'elo_before': elo_before,
                'elo_after': elo_after,
                'final_elo': elo_after[-1] if len(elo_after) > 0 else self.starting_elo,
                'matches_count': len(match_data)
            }
        
        return results


def test_optimized_calculator():
    """
    Test the optimized Elo calculator against the original method.
    """
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')
    import django
    django.setup()
    
    from MyApi.models import PlayerMatch
    
    print("="*60)
    print("TESTING OPTIMIZED ELO CALCULATOR")
    print("="*60)
    
    # Get sample data
    print("Loading sample data...")
    sample_players = list(PlayerMatch.objects.values_list('player_name', flat=True).distinct()[:10])
    
    # Prepare data for optimized calculator
    all_match_data = {}
    for player_name in sample_players:
        matches = PlayerMatch.objects.filter(player_name=player_name).order_by('date')
        match_data = pd.DataFrame(list(matches.values('points', 'goals', 'assists', 'minutes_played', 'date')))
        if not match_data.empty:
            all_match_data[player_name] = match_data
    
    print(f"Testing with {len(all_match_data)} players...")
    
    # Initialize optimized calculator
    calculator = OptimizedEloCalculator()
    
    # Test original method timing
    print("\n1. Testing ORIGINAL method:")
    start_time = time.time()
    
    original_results = {}
    for player_name, match_data in all_match_data.items():
        current_elo = 1200.0
        elo_progression = []
        
        for _, match in match_data.iterrows():
            # Original calculation logic
            performance_points = (
                match['points'] * 2 +
                match['goals'] * 5 +
                match['assists'] * 3 +
                (2 if match['minutes_played'] >= 90 else 1 if match['minutes_played'] >= 60 else -2 if match['minutes_played'] == 0 else 0)
            )
            
            elo_change = max(-30, min(30, performance_points))
            new_elo = current_elo + elo_change
            elo_progression.append((current_elo, new_elo))
            current_elo = new_elo
        
        original_results[player_name] = {
            'final_elo': current_elo,
            'progression': elo_progression
        }
    
    original_time = time.time() - start_time
    print(f"   Original method completed in: {original_time:.4f} seconds")
    
    # Test optimized method timing
    print("\n2. Testing OPTIMIZED method:")
    start_time = time.time()
    
    optimized_results = calculator.calculate_batch_elos(all_match_data)
    
    optimized_time = time.time() - start_time
    print(f"   Optimized method completed in: {optimized_time:.4f} seconds")
    
    # Calculate speedup
    speedup = original_time / optimized_time if optimized_time > 0 else float('inf')
    print(f"   Speedup: {speedup:.2f}x faster")
    
    # Verify accuracy
    print("\n3. Verifying accuracy:")
    accuracy_ok = True
    
    for player_name in sample_players[:5]:  # Check first 5 players
        if player_name in original_results and player_name in optimized_results:
            original_final = original_results[player_name]['final_elo']
            optimized_final = optimized_results[player_name]['final_elo']
            
            diff = abs(original_final - optimized_final)
            print(f"   {player_name[:20]:20}: Original={original_final:.2f}, Optimized={optimized_final:.2f}, Diff={diff:.6f}")
            
            if diff > 0.001:  # Allow for tiny floating point differences
                accuracy_ok = False
    
    if accuracy_ok:
        print("   ✅ Accuracy verification PASSED")
    else:
        print("   ❌ Accuracy verification FAILED")
    
    # Performance summary
    print("\n" + "="*60)
    print("PERFORMANCE SUMMARY")
    print("="*60)
    print(f"Original time:   {original_time:.4f} seconds")
    print(f"Optimized time:  {optimized_time:.4f} seconds")
    print(f"Speedup:         {speedup:.2f}x")
    print(f"Accuracy:        {'✅ PASS' if accuracy_ok else '❌ FAIL'}")
    
    return calculator, optimized_results, speedup, accuracy_ok


if __name__ == "__main__":
    calculator, results, speedup, accuracy = test_optimized_calculator()
    
    if accuracy and speedup > 1.0:
        print(f"\n🎉 Optimization successful! {speedup:.2f}x speedup with perfect accuracy!")
    else:
        print(f"\n⚠️  Need to investigate: Speedup={speedup:.2f}x, Accuracy={'OK' if accuracy else 'FAILED'}")