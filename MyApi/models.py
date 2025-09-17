from django.db import models
import json

# Create your models here.

class PlayerMatch(models.Model):
    """
    Model to store individual match performance data for Elo calculations.
    This replaces the individual CSV files in elo_data folder.
    """
    player_name = models.CharField(max_length=200, db_index=True)
    season = models.CharField(max_length=20)  # e.g., "2022-2023"
    date = models.DateField()
    competition = models.CharField(max_length=100)  # Premier League, Champions League, etc.
    round_info = models.CharField(max_length=100, blank=True)  # Matchweek 1, Group stage, etc.
    opponent = models.CharField(max_length=100)
    result = models.CharField(max_length=20)  # W 3-1, L 1-2, D 0-0
    position = models.CharField(max_length=50, blank=True)  # FW, RW, etc.
    minutes_played = models.IntegerField(default=0)
    goals = models.IntegerField(default=0)
    assists = models.IntegerField(default=0)
    points = models.IntegerField(default=0)  # Fantasy points
    elo_after_match = models.FloatField(help_text="Elo rating after this match")
    
    # Additional fields that might be useful
    saves = models.IntegerField(default=0, help_text="For goalkeepers")
    goals_conceded = models.IntegerField(default=0, help_text="For goalkeepers/defenders")
    clean_sheet = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'player_matches'
        # Ensure unique combination of player, date, and opponent
        unique_together = ['player_name', 'date', 'opponent']
        # Add indexes for common queries
        indexes = [
            models.Index(fields=['player_name', 'date']),
            models.Index(fields=['player_name', 'season']),
            models.Index(fields=['date', 'competition']),
            models.Index(fields=['player_name', 'elo_after_match']),
        ]
        ordering = ['-date', 'player_name']  # Most recent matches first
    
    def __str__(self):
        return f"{self.player_name} vs {self.opponent} ({self.date}) - Elo: {self.elo_after_match}"
    
    @classmethod
    def get_player_history(cls, player_name, limit=None):
        """
        Get match history for a specific player, ordered by date.
        """
        queryset = cls.objects.filter(player_name=player_name).order_by('-date')
        if limit:
            queryset = queryset[:limit]
        return queryset
    
    @classmethod
    def get_latest_elo(cls, player_name):
        """
        Get the most recent Elo rating for a player.
        """
        latest_match = cls.objects.filter(player_name=player_name).order_by('-date').first()
        return latest_match.elo_after_match if latest_match else None
    
    @classmethod
    def get_players_by_season(cls, season):
        """
        Get all players who played in a specific season.
        """
        return cls.objects.filter(season=season).values('player_name').distinct()


class EloCalculation(models.Model):
    """
    Model to store weekly Elo calculations and track changes over time.
    This replaces the weekly_elo CSV generation process.
    """
    player_name = models.CharField(max_length=200, db_index=True)
    week = models.IntegerField(db_index=True)
    season = models.CharField(max_length=20)  # e.g., "2024-2025"
    elo_rating = models.FloatField()
    previous_elo = models.FloatField(null=True, blank=True)
    elo_change = models.FloatField(default=0.0)
    
    # Context for the calculation
    matches_played = models.IntegerField(default=0, help_text="Matches in this calculation period")
    last_match_date = models.DateField(null=True, blank=True)
    form_rating = models.FloatField(null=True, blank=True, help_text="Recent form factor")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'elo_calculations'
        unique_together = ['player_name', 'week', 'season']
        indexes = [
            models.Index(fields=['week', 'season']),
            models.Index(fields=['player_name', 'week']),
            models.Index(fields=['elo_rating']),
        ]
        ordering = ['-week', '-elo_rating']
    
    def __str__(self):
        return f"{self.player_name} - Week {self.week} - Elo: {self.elo_rating}"
    
    @classmethod
    def get_weekly_elos(cls, week, season):
        """
        Get all Elo ratings for a specific week and season.
        """
        return cls.objects.filter(week=week, season=season).order_by('-elo_rating')
    
    @classmethod
    def get_player_elo_history(cls, player_name, season=None):
        """
        Get Elo history for a specific player.
        """
        queryset = cls.objects.filter(player_name=player_name)
        if season:
            queryset = queryset.filter(season=season)
        return queryset.order_by('week')


class Player(models.Model):
    """
    Model to store player data for each week, including Elo ratings and costs.
    """
    POSITION_CHOICES = [
        ('Keeper', 'Goalkeeper'),
        ('Defender', 'Defender'),
        ('Midfielder', 'Midfielder'),
        ('Attacker', 'Attacker'),
    ]
    
    name = models.CharField(max_length=200, db_index=True)
    position = models.CharField(max_length=20, choices=POSITION_CHOICES, db_index=True)
    elo = models.FloatField(help_text="Player's Elo rating")
    cost = models.FloatField(help_text="Player's cost in millions")
    week = models.IntegerField(db_index=True, help_text="Game week number")
    
    # Optional fields for additional data
    team = models.CharField(max_length=100, blank=True, null=True)
    competition = models.CharField(max_length=100, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'players'
        # Ensure unique combination of player name and week
        unique_together = ['name', 'week']
        # Add index for common queries
        indexes = [
            models.Index(fields=['week', 'position']),
            models.Index(fields=['week', 'elo']),
            models.Index(fields=['position', 'elo']),
        ]
        ordering = ['-elo']  # Default ordering by Elo (highest first)
    
    def __str__(self):
        return f"{self.name} (Week {self.week}) - {self.position} - Elo: {self.elo}"
    
    @classmethod
    def get_players_by_week(cls, week):
        """
        Get all players for a specific week.
        """
        return cls.objects.filter(week=week)
    
    @classmethod
    def get_top_players_by_position(cls, week, position, limit=10):
        """
        Get top players by position for a specific week, ordered by Elo.
        """
        return cls.objects.filter(
            week=week, 
            position=position
        ).order_by('-elo')[:limit]


class CurrentSquad(models.Model):
    """
    Model to store the current fantasy football squad with players in different positions.
    """
    name = models.CharField(max_length=100, default="Current Squad")
    squad_data = models.TextField(default='{}')  # Store JSON data as text
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'current_squad'
    
    def __str__(self):
        return f"{self.name} - Updated: {self.updated_at}"
    
    @property
    def squad(self):
        """
        Get the squad data as a Python dictionary.
        """
        if self.squad_data:
            return json.loads(self.squad_data)
        return {
            "goalkeepers": [],
            "defenders": [],
            "midfielders": [],
            "forwards": []
        }
    
    @squad.setter
    def squad(self, value):
        """
        Set the squad data from a Python dictionary.
        """
        self.squad_data = json.dumps(value)
    
    def initialize_default_squad(self):
        """
        Initialize the squad with default players.
        """
        default_squad = {
            "goalkeepers": [{"name": "Player A"}],
            "defenders": [{"name": "Player B"}, {"name": "Player C"}, {"name": "Player D"}],
            "midfielders": [{"name": "Player E"}, {"name": "Player F"}, {"name": "Player G"}, {"name": "Player H"}],
            "forwards": [{"name": "Player I"}, {"name": "Player J"}, {"name": "Player K"}]
        }
        self.squad = default_squad
        self.save()
        return self.squad
    
    def add_player(self, position, player_name):
        """
        Add a player to a specific position.
        
        Args:
            position (str): One of 'goalkeepers', 'defenders', 'midfielders', 'forwards'
            player_name (str): Name of the player to add
        
        Returns:
            bool: True if successful, False if position is invalid
        """
        valid_positions = ['goalkeepers', 'defenders', 'midfielders', 'forwards']
        
        if position not in valid_positions:
            return False
        
        current_squad = self.squad
        current_squad[position].append({"name": player_name})
        self.squad = current_squad
        self.save()
        return True
    
    def remove_player(self, position, player_name):
        """
        Remove a player from a specific position.
        
        Args:
            position (str): One of 'goalkeepers', 'defenders', 'midfielders', 'forwards'
            player_name (str): Name of the player to remove
        
        Returns:
            bool: True if player was found and removed, False otherwise
        """
        valid_positions = ['goalkeepers', 'defenders', 'midfielders', 'forwards']
        
        if position not in valid_positions:
            return False
        
        current_squad = self.squad
        position_players = current_squad[position]
        
        # Find and remove the player
        for i, player in enumerate(position_players):
            if player.get("name") == player_name:
                position_players.pop(i)
                self.squad = current_squad
                self.save()
                return True
        
        return False
    
    def get_players_by_position(self, position):
        """
        Get all players in a specific position.
        
        Args:
            position (str): One of 'goalkeepers', 'defenders', 'midfielders', 'forwards'
        
        Returns:
            list: List of players in that position
        """
        valid_positions = ['goalkeepers', 'defenders', 'midfielders', 'forwards']
        
        if position not in valid_positions:
            return []
        
        return self.squad.get(position, [])
    
    def get_total_players(self):
        """
        Get the total number of players in the squad.
        
        Returns:
            int: Total number of players
        """
        squad_data = self.squad
        total = 0
        for position in squad_data:
            total += len(squad_data[position])
        return total
    
    def clear_position(self, position):
        """
        Remove all players from a specific position.
        
        Args:
            position (str): One of 'goalkeepers', 'defenders', 'midfielders', 'forwards'
        
        Returns:
            bool: True if successful, False if position is invalid
        """
        valid_positions = ['goalkeepers', 'defenders', 'midfielders', 'forwards']
        
        if position not in valid_positions:
            return False
        
        current_squad = self.squad
        current_squad[position] = []
        self.squad = current_squad
        self.save()
        return True
    
    @classmethod
    def get_or_create_current_squad(cls):
        """
        Get the current squad or create one if it doesn't exist.
        
        Returns:
            CurrentSquad: The current squad instance
        """
        squad, created = cls.objects.get_or_create(
            name="Current Squad",
            defaults={'name': "Current Squad"}
        )
        
        if created or not squad.squad_data:
            squad.initialize_default_squad()
        
        return squad


class SystemSettings(models.Model):
    """
    Model to store system-wide settings like current game week, season, etc.
    """
    current_gameweek = models.IntegerField(default=1, help_text="Current game week number (1-38)")
    current_season = models.CharField(max_length=20, default="2024/25", help_text="Current season (e.g., 2024/25)")
    last_data_update = models.DateTimeField(null=True, blank=True, help_text="Last time data was refreshed from FPL API")
    last_fixtures_update = models.DateTimeField(null=True, blank=True, help_text="Last time fixtures were updated")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'system_settings'
        verbose_name = 'System Settings'
        verbose_name_plural = 'System Settings'
    
    def __str__(self):
        return f"Season {self.current_season} - Game Week {self.current_gameweek}"
    
    @classmethod
    def get_settings(cls):
        """
        Get or create the system settings instance.
        
        Returns:
            SystemSettings: The system settings instance
        """
        settings, created = cls.objects.get_or_create(
            id=1,  # Ensure only one settings instance
            defaults={
                'current_gameweek': 1,
                'current_season': '2024/25'
            }
        )
        return settings
    
    @classmethod
    def get_current_gameweek(cls):
        """Get the current game week number."""
        return cls.get_settings().current_gameweek
    
    @classmethod
    def set_current_gameweek(cls, gameweek):
        """Set the current game week number."""
        settings = cls.get_settings()
        settings.current_gameweek = gameweek
        settings.save()
        return settings
    
    @classmethod
    def get_current_season(cls):
        """Get the current season."""
        return cls.get_settings().current_season
