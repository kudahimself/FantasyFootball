from django.db import models
import json

class Team(models.Model):
    """
    Canonical mapping of FPL team ID to team name for consistent use across the app.
    """
    fpl_team_id = models.IntegerField(unique=True, db_index=True)
    name = models.CharField(max_length=100, unique=True, db_index=True)

    class Meta:
        db_table = 'teams'
        ordering = ['fpl_team_id']

    def __str__(self):
        return f"{self.name} (FPL ID: {self.fpl_team_id})"

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
    elo_before_match = models.FloatField(default=1200.0, help_text="Elo rating before this match")
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
    elo = models.FloatField()
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
            models.Index(fields=['elo']),
        ]
    ordering = ['-week', '-elo']
    
    def __str__(self):
        return f"{self.player_name} - Week {self.week} - Elo: {self.elo}"
    
    @classmethod
    def get_weekly_elos(cls, week, season):
        """
        Get all Elo ratings for a specific week and season.
        """
        return cls.objects.filter(week=week, season=season).order_by('-elo')
    
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
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, related_name='current_squad')
    name = models.CharField(max_length=100, default="Current Squad")
    squad_data = models.TextField(default='{}')  # Store JSON data as text
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'current_squad'
        unique_together = ('user',)
    
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
        Add a player to a specific position with full data (name, elo, cost, team).
        
        Args:
            position (str): One of 'goalkeepers', 'defenders', 'midfielders', 'forwards'
            player_name (str): Name of the player to add
        
        Returns:
            bool: True if successful, False if position is invalid
        """
        valid_positions = ['goalkeepers', 'defenders', 'midfielders', 'forwards']
        
        if position not in valid_positions:
            return False
        
        # Get player data from the Player model (current week)
        from MyApi.models import SystemSettings
        settings = SystemSettings.get_settings()
        current_week = settings.current_gameweek
        
        player_data = {"name": player_name}
        
        try:
            player = Player.objects.filter(name=player_name, week=current_week).first()
            if not player:
                # Fallback to any week if current week not found
                player = Player.objects.filter(name=player_name).order_by('-week').first()
            
            if player:
                player_data.update({
                    "elo": float(player.elo),
                    "cost": float(player.cost),
                    "team": player.team or "",
                    "position": player.position
                })
        except Exception as e:
            print(f"Error fetching player data for {player_name}: {e}")
        
        current_squad = self.squad
        current_squad[position].append(player_data)
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
    
    def refresh_squad_data(self):
        """
        Refresh existing squad data to include full player information (elo, cost, team).
        This is useful for updating squads that only have player names.
        """
        from MyApi.models import SystemSettings
        settings = SystemSettings.get_settings()
        current_week = settings.current_gameweek
        
        current_squad = self.squad
        
        for position in ['goalkeepers', 'defenders', 'midfielders', 'forwards']:
            if position in current_squad:
                for i, player_data in enumerate(current_squad[position]):
                    if isinstance(player_data, dict) and 'name' in player_data:
                        player_name = player_data['name']
                        
                        # Skip if already has elo and cost data
                        if 'elo' in player_data and 'cost' in player_data:
                            continue
                        
                        # Fetch full player data
                        try:
                            player = Player.objects.filter(name=player_name, week=current_week).first()
                            if not player:
                                player = Player.objects.filter(name=player_name).order_by('-week').first()
                            
                            if player:
                                current_squad[position][i] = {
                                    "name": player_name,
                                    "elo": float(player.elo),
                                    "cost": float(player.cost),
                                    "team": player.team or "",
                                    "position": player.position
                                }
                        except Exception as e:
                            print(f"Error refreshing data for {player_name}: {e}")
        
        self.squad = current_squad
        self.save()
    
    @classmethod
    def get_or_create_current_squad(cls, user):
        """
        Get the current squad for a user or create one if it doesn't exist.
        
        Args:
            user: The Django user instance
        
        Returns:
            CurrentSquad: The current squad instance for the user
        """
        squad, created = cls.objects.get_or_create(
            user=user,
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
    current_season = models.CharField(max_length=20, default="2025/26", help_text="Current season (e.g., 2025/26)")
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
                'current_season': '2025/26'
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


class PlayerFixture(models.Model):
    """
    Model to store upcoming fixtures for players.
    Used for projecting points for next 3 games.
    """
    player_name = models.CharField(max_length=200, db_index=True)
    team = models.CharField(max_length=100)  # Player's team
    gameweek = models.IntegerField(db_index=True)  # FPL gameweek number
    opponent = models.CharField(max_length=100)  # Opposition team
    is_home = models.BooleanField(default=True)  # True if playing at home
    fixture_date = models.DateTimeField(null=True, blank=True)
    competition = models.CharField(max_length=100, default='Premier League')
    difficulty = models.IntegerField(default=3, help_text="FPL difficulty rating (1-5)")
    projected_points = models.FloatField(default=0.0, help_text="Projected points for this fixture")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'player_fixtures'
        unique_together = ['player_name', 'gameweek', 'opponent']
        indexes = [
            models.Index(fields=['player_name', 'gameweek']),
            models.Index(fields=['gameweek', 'team']),
            models.Index(fields=['fixture_date']),
        ]
        ordering = ['gameweek', 'fixture_date']
    
    def __str__(self):
        home_away = "vs" if self.is_home else "@"
        return f"{self.player_name} ({self.team}) {home_away} {self.opponent} - GW{self.gameweek}"


class ProjectedPoints(models.Model):
    """
    Model to store projected points for players for the next 3 games.
    Uses the same expected points formula as ELO calculator.
    """
    player_name = models.CharField(max_length=200, db_index=True)
    gameweek = models.IntegerField(db_index=True)
    opponent = models.CharField(max_length=100)
    is_home = models.BooleanField(default=True)
    
    # Current player stats
    current_elo = models.FloatField(help_text="Player's current ELO rating")
    current_cost = models.FloatField(help_text="Player's current cost")
    
    # Expected points calculation (same as ELO calculator)
    competition = models.CharField(max_length=100, default='Premier League')
    league_rating = models.IntegerField(help_text="Competition difficulty rating")
    expected_points = models.FloatField(help_text="Expected points using ELO formula: k/(1 + 10**(League_Rating/current_elo))")
    
    # Opposition multiplier (for future enhancement)
    opposition_strength = models.FloatField(default=1.0, help_text="Opposition strength multiplier (from FPL)")
    difficulty_rating = models.IntegerField(default=3, help_text="FPL difficulty rating (1-5)")
    adjusted_expected_points = models.FloatField(help_text="Expected points adjusted for opposition strength")
    
    # Calculation metadata
    calculated_at = models.DateTimeField(auto_now_add=True)
    k_factor = models.IntegerField(default=20, help_text="K-factor used in calculation")
    
    class Meta:
        db_table = 'projected_points'
        unique_together = ['player_name', 'gameweek', 'opponent']
        indexes = [
            models.Index(fields=['player_name', 'gameweek']),
            models.Index(fields=['gameweek']),
            models.Index(fields=['expected_points']),
            models.Index(fields=['adjusted_expected_points']),
        ]
        ordering = ['gameweek', '-expected_points']
    
    def __str__(self):
        return f"{self.player_name} vs {self.opponent} GW{self.gameweek}: {self.expected_points:.2f} pts"
    
    @classmethod
    def get_next_3_games(cls, player_name):
        """Get projected points for next 3 games for a specific player."""
        return cls.objects.filter(player_name=player_name).order_by('gameweek')[:3]
    
    @classmethod
    def get_total_projected_points(cls, player_name, games=3):
        """Get total projected points for next N games."""
        projections = cls.get_next_3_games(player_name)[:games]
        return sum(proj.adjusted_expected_points for proj in projections)


class DifficultyMultiplier(models.Model):
    """
    Model to store calculated difficulty multipliers for FPL difficulty ratings.
    These are dynamically calculated based on actual player performance data.
    """
    difficulty_rating = models.IntegerField(unique=True, help_text="FPL difficulty rating (1-5)")
    multiplier = models.FloatField(help_text="Calculated multiplier for this difficulty level")
    sample_size = models.IntegerField(default=0, help_text="Number of matches used in calculation")
    last_calculated = models.DateTimeField(auto_now=True, help_text="When this multiplier was last updated")
    
    class Meta:
        db_table = 'difficulty_multipliers'
        ordering = ['difficulty_rating']
    
    def __str__(self):
        difficulty_names = {1: "Very Easy", 2: "Easy", 3: "Average", 4: "Hard", 5: "Very Hard"}
        name = difficulty_names.get(self.difficulty_rating, f"Difficulty {self.difficulty_rating}")
        return f"{name}: {self.multiplier}x (n={self.sample_size})"
    
    @classmethod
    def get_multiplier(cls, difficulty_rating: int) -> float:
        """Get multiplier for a specific difficulty rating, with fallback to defaults."""
        try:
            multiplier_obj = cls.objects.get(difficulty_rating=difficulty_rating)
            return multiplier_obj.multiplier
        except cls.DoesNotExist:
            # Fallback to logical defaults if not found
            defaults = {1: 3.2, 2: 2.8, 3: 2.1, 4: 1.9, 5: 1.5}
            return defaults.get(difficulty_rating, 1.0)
    
    @classmethod
    def update_multipliers(cls, multipliers_dict: dict, sample_sizes: dict = None):
        """Update all multipliers from a dictionary."""
        for difficulty, multiplier in multipliers_dict.items():
            sample_size = sample_sizes.get(difficulty, 0) if sample_sizes else 0
            cls.objects.update_or_create(
                difficulty_rating=difficulty,
                defaults={
                    'multiplier': multiplier,
                    'sample_size': sample_size
                }
            )


class UserSquad(models.Model):
    """
    Stores a fantasy football squad for a user for a specific week (future or past).
    """
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='user_squads')
    week = models.IntegerField(db_index=True)
    name = models.CharField(max_length=100, default="Squad")
    squad_data = models.TextField(default='{}')  # Store JSON data as text
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_squad'
        unique_together = ('user', 'week')
        ordering = ['user', 'week']

    def __str__(self):
        return f"{self.user.username} - GW{self.week} - {self.name}"

    @property
    def squad(self):
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
        self.squad_data = json.dumps(value)
