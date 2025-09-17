"""
Database-backed version of FootballerEloModel that replaces CSV file usage.
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django environment for standalone use
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    # Add the project root to the Python path
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.append(project_root)
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')
    django.setup()

from MyApi.models import PlayerMatch, EloCalculation


class FootballerEloModelDB:
    """
    Database-backed Elo model that replaces the CSV-based FootballerEloModel.
    """
    
    def __init__(self, player_name):
        self.player_name = player_name
        self.match_history = None
        self.load_player_data()
    
    def load_player_data(self):
        """
        Load player match data from the database.
        """
        self.match_history = PlayerMatch.objects.filter(
            player_name=self.player_name
        ).order_by('date')
        
        if not self.match_history.exists():
            raise ValueError(f"No match data found for player: {self.player_name}")
        
        print(f"Loaded {self.match_history.count()} matches for {self.player_name}")
    
    def get_recent_form(self, num_matches=10):
        """
        Get recent form based on the last N matches.
        Returns average Elo change over recent matches.
        """
        recent_matches = self.match_history.order_by('-date')[:num_matches]
        
        if len(recent_matches) < 2:
            return 0.0
        
        recent_matches = list(recent_matches)
        recent_matches.reverse()  # Chronological order
        
        elo_changes = []
        for i in range(1, len(recent_matches)):
            change = recent_matches[i].elo_after_match - recent_matches[i-1].elo_after_match
            elo_changes.append(change)
        
        return sum(elo_changes) / len(elo_changes) if elo_changes else 0.0
    
    def calculate_elo_after_match(self, match_data):
        """
        Calculate Elo rating change after a match.
        This is the core Elo calculation logic.
        """
        # Extract performance metrics
        minutes = match_data.get('minutes_played', 0)
        goals = match_data.get('goals', 0)
        assists = match_data.get('assists', 0)
        result = match_data.get('result', '')
        position = match_data.get('position', '')
        
        # Base performance score
        performance_score = 0
        
        # Goals and assists
        performance_score += goals * 5  # Goals worth more
        performance_score += assists * 3
        
        # Minutes played factor
        if minutes >= 90:
            performance_score += 2  # Full match bonus
        elif minutes >= 60:
            performance_score += 1  # Substantial play time
        
        # Result factor
        if 'W' in result:
            performance_score += 3  # Win bonus
        elif 'D' in result:
            performance_score += 1  # Draw bonus
        # Loss gives no bonus
        
        # Position-specific adjustments
        if 'GK' in position or 'Keeper' in position:
            # Goalkeeper specific metrics
            saves = match_data.get('saves', 0)
            clean_sheet = match_data.get('clean_sheet', False)
            
            performance_score += saves * 0.5  # Save points
            if clean_sheet:
                performance_score += 4  # Clean sheet bonus
        
        # Convert performance to Elo change
        # This is a simplified Elo calculation
        base_elo_change = performance_score * 2  # Scale factor
        
        # Cap the change to prevent extreme swings
        max_change = 50
        elo_change = max(-max_change, min(max_change, base_elo_change))
        
        return elo_change
    
    def get_current_elo(self):
        """
        Get the most recent Elo rating for the player.
        """
        latest_match = self.match_history.order_by('-date').first()
        return latest_match.elo_after_match if latest_match else 1200.0  # Default starting Elo
    
    def get_elo_history(self):
        """
        Get Elo rating history as a list of (date, elo) tuples.
        """
        return [(match.date, match.elo_after_match) for match in self.match_history.order_by('date')]
    
    def get_season_performance(self, season):
        """
        Get performance metrics for a specific season.
        """
        season_matches = self.match_history.filter(season=season)
        
        if not season_matches.exists():
            return None
        
        total_goals = sum(match.goals for match in season_matches)
        total_assists = sum(match.assists for match in season_matches)
        total_minutes = sum(match.minutes_played for match in season_matches)
        matches_played = season_matches.count()
        
        start_elo = season_matches.order_by('date').first().elo_after_match
        end_elo = season_matches.order_by('-date').first().elo_after_match
        elo_change = end_elo - start_elo
        
        return {
            'season': season,
            'matches_played': matches_played,
            'total_goals': total_goals,
            'total_assists': total_assists,
            'total_minutes': total_minutes,
            'average_minutes': total_minutes / matches_played if matches_played > 0 else 0,
            'start_elo': start_elo,
            'end_elo': end_elo,
            'elo_change': elo_change,
            'goals_per_match': total_goals / matches_played if matches_played > 0 else 0,
            'assists_per_match': total_assists / matches_played if matches_played > 0 else 0,
        }
    
    def update_weekly_elo(self, week, season="2024-2025"):
        """
        Calculate and store weekly Elo rating for this player.
        """
        current_elo = self.get_current_elo()
        form_rating = self.get_recent_form()
        
        # Get matches in the calculation period (last week)
        week_start = datetime.now() - timedelta(days=7)
        recent_matches = self.match_history.filter(date__gte=week_start).count()
        
        # Check if already calculated
        existing_calc = EloCalculation.objects.filter(
            player_name=self.player_name,
            week=week,
            season=season
        ).first()
        
        previous_elo = None
        if existing_calc:
            previous_elo = existing_calc.elo_rating
        else:
            # Get previous week's Elo if available
            prev_calc = EloCalculation.objects.filter(
                player_name=self.player_name,
                week=week-1,
                season=season
            ).first()
            if prev_calc:
                previous_elo = prev_calc.elo_rating
        
        elo_change = current_elo - (previous_elo or current_elo)
        
        # Create or update the calculation
        calc, created = EloCalculation.objects.update_or_create(
            player_name=self.player_name,
            week=week,
            season=season,
            defaults={
                'elo_rating': current_elo,
                'previous_elo': previous_elo,
                'elo_change': elo_change,
                'matches_played': recent_matches,
                'last_match_date': self.match_history.order_by('-date').first().date,
                'form_rating': form_rating,
            }
        )
        
        return calc
    
    @classmethod
    def get_all_players(cls):
        """
        Get list of all players with match data.
        """
        return PlayerMatch.objects.values('player_name').distinct().order_by('player_name')
    
    @classmethod
    def calculate_weekly_elos_for_all_players(cls, week, season="2024-2025"):
        """
        Calculate weekly Elo ratings for all players.
        """
        players = cls.get_all_players()
        
        print(f"Calculating weekly Elos for week {week}, season {season}")
        print(f"Processing {players.count()} players...")
        
        success_count = 0
        error_count = 0
        
        for player_data in players:
            player_name = player_data['player_name']
            try:
                player_model = cls(player_name)
                player_model.update_weekly_elo(week, season)
                success_count += 1
                
                if success_count % 50 == 0:
                    print(f"Processed {success_count} players...")
                    
            except Exception as e:
                error_count += 1
                print(f"Error processing {player_name}: {str(e)}")
        
        print(f"Weekly Elo calculation complete: {success_count} successful, {error_count} errors")
        
        return success_count, error_count