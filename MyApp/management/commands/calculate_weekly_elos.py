"""
Django management command to calculate weekly Elo ratings for all players.
This replaces the CSV-based weekly Elo generation process.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Avg
from fantasy_models.elo_model_db import FootballerEloModelDB
from MyApi.models import Player, EloCalculation


class Command(BaseCommand):
    help = 'Calculate weekly Elo ratings for all players and update the Player model'

    def add_arguments(self, parser):
        parser.add_argument(
            '--week',
            type=int,
            required=True,
            help='Week number to calculate (e.g., --week 4)',
        )
        parser.add_argument(
            '--season',
            type=str,
            default='2024-2025',
            help='Season to calculate for (e.g., --season 2024-2025)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recalculation (overwrite existing calculations)',
        )

    def handle(self, *args, **options):
        week = options['week']
        season = options['season']
        force = options['force']
        
        self.stdout.write(f'Calculating weekly Elos for Week {week}, Season {season}')
        
        # Check if calculations already exist
        if not force:
            existing_count = EloCalculation.objects.filter(week=week, season=season).count()
            if existing_count > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f'Calculations for Week {week} already exist ({existing_count} players). '
                        f'Use --force to recalculate.'
                    )
                )
                return
        
        try:
            # Calculate weekly Elos for all players
            success_count, error_count = FootballerEloModelDB.calculate_weekly_elos_for_all_players(
                week, season
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Elo calculations complete: {success_count} successful, {error_count} errors'
                )
            )
            
            # Update the Player model with the calculated Elos
            self.update_player_model(week, season)
            
        except Exception as e:
            raise CommandError(f'Error calculating weekly Elos: {str(e)}')
    
    def update_player_model(self, week, season):
        """
        Update the Player model with the calculated weekly Elos.
        """
        self.stdout.write('Updating Player model with calculated Elos...')
        
        # Get all Elo calculations for this week
        elo_calculations = EloCalculation.objects.filter(week=week, season=season)
        
        created_count = 0
        updated_count = 0
        
        # Map player names to positions (this could be improved with a proper mapping)
        position_mapping = self.get_position_mapping()
        
        with transaction.atomic():
            for calc in elo_calculations:
                # Try to determine position from historical data
                position = self.determine_player_position(calc.player_name, position_mapping)
                
                # Determine cost based on Elo (simplified logic)
                cost = self.calculate_cost_from_elo(calc.elo_rating, position)
                
                # Create or update Player record
                player, created = Player.objects.update_or_create(
                    name=calc.player_name,
                    week=week,
                    defaults={
                        'position': position,
                        'elo': calc.elo_rating,
                        'cost': cost,
                        'team': self.get_player_team(calc.player_name),
                        'competition': 'Premier League',
                    }
                )
                
                if created:
                    created_count += 1
                else:
                    updated_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Player model updated: {created_count} created, {updated_count} updated'
            )
        )
        
        # Show statistics
        self.show_statistics(week)
    
    def get_position_mapping(self):
        """
        Create a mapping of common position abbreviations to our standard positions.
        """
        return {
            'GK': 'Keeper',
            'Keeper': 'Keeper',
            'CB': 'Defender',
            'LB': 'Defender', 
            'RB': 'Defender',
            'DF': 'Defender',
            'DEF': 'Defender',
            'LWB': 'Defender',
            'RWB': 'Defender',
            'CM': 'Midfielder',
            'CDM': 'Midfielder',
            'CAM': 'Midfielder',
            'LM': 'Midfielder',
            'RM': 'Midfielder',
            'MF': 'Midfielder',
            'MID': 'Midfielder',
            'LW': 'Midfielder',
            'RW': 'Midfielder',
            'FW': 'Attacker',
            'ST': 'Attacker',
            'CF': 'Attacker',
            'LF': 'Attacker',
            'RF': 'Attacker',
            'ATT': 'Attacker',
        }
    
    def determine_player_position(self, player_name, position_mapping):
        """
        Determine player position from their historical match data.
        """
        from MyApp.models import PlayerMatch
        
        # Get the most common position from recent matches
        recent_matches = PlayerMatch.objects.filter(
            player_name=player_name
        ).order_by('-date')[:20]  # Last 20 matches
        
        position_counts = {}
        for match in recent_matches:
            positions = match.position.split(',')  # Handle multiple positions
            for pos in positions:
                pos = pos.strip()
                # Map to standard position
                standard_pos = position_mapping.get(pos, pos)
                if standard_pos in ['Keeper', 'Defender', 'Midfielder', 'Attacker']:
                    position_counts[standard_pos] = position_counts.get(standard_pos, 0) + 1
        
        if position_counts:
            # Return most common position
            return max(position_counts, key=position_counts.get)
        
        # Default fallback
        return 'Midfielder'
    
    def calculate_cost_from_elo(self, elo_rating, position):
        """
        Calculate player cost based on Elo rating and position.
        This is a simplified algorithm - you might want to make it more sophisticated.
        """
        # Base cost calculation
        if elo_rating >= 2000:
            base_cost = 12.0 + (elo_rating - 2000) / 100
        elif elo_rating >= 1800:
            base_cost = 9.0 + (elo_rating - 1800) / 100
        elif elo_rating >= 1600:
            base_cost = 6.0 + (elo_rating - 1600) / 100
        elif elo_rating >= 1400:
            base_cost = 4.5 + (elo_rating - 1400) / 100
        else:
            base_cost = 4.0
        
        # Position adjustments
        if position == 'Attacker':
            base_cost *= 1.1  # Attackers typically cost more
        elif position == 'Keeper':
            base_cost *= 0.9  # Keepers typically cost less
        
        # Cap the cost
        return min(15.0, max(4.0, round(base_cost, 1)))
    
    def get_player_team(self, player_name):
        """
        Try to determine player's current team.
        This is a simplified implementation - you might want to maintain a proper team mapping.
        """
        # You could implement a proper team mapping here
        # For now, return empty string
        return ''
    
    def show_statistics(self, week):
        """
        Show statistics about the weekly Elo calculations.
        """
        self.stdout.write(f'\nWeek {week} Statistics:')
        
        total_players = Player.objects.filter(week=week).count()
        self.stdout.write(f'Total players: {total_players}')
        
        # Position breakdown
        for position in ['Keeper', 'Defender', 'Midfielder', 'Attacker']:
            count = Player.objects.filter(week=week, position=position).count()
            avg_elo = Player.objects.filter(week=week, position=position).aggregate(
                avg_elo=Avg('elo')
            )['avg_elo'] or 0
            avg_cost = Player.objects.filter(week=week, position=position).aggregate(
                avg_cost=Avg('cost')
            )['avg_cost'] or 0
            
            self.stdout.write(
                f'{position}: {count} players, avg Elo: {avg_elo:.1f}, avg cost: £{avg_cost:.1f}m'
            )
        
        # Top 10 players by Elo
        top_players = Player.objects.filter(week=week).order_by('-elo')[:10]
        self.stdout.write(f'\nTop 10 players by Elo:')
        for i, player in enumerate(top_players, 1):
            self.stdout.write(
                f'{i:2d}. {player.name} ({player.position}) - Elo: {player.elo:.1f}, Cost: £{player.cost}m'
            )