"""
Django management command to import historical player match data from elo_data CSV files.
"""

import os
import pandas as pd
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from MyApi.models import PlayerMatch


class Command(BaseCommand):
    help = 'Import historical player match data from elo_data CSV files into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--player',
            type=str,
            help='Import data for a specific player (e.g., --player Mohamed_Salah)',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Import data for all players in elo_data directory',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reimport (delete existing data for the player)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit number of players to process (useful for testing)',
        )

    def handle(self, *args, **options):
        """
        Main command handler.
        """
        if options['all']:
            self.import_all_players(options['force'], options.get('limit'))
        elif options['player']:
            self.import_player(options['player'], options['force'])
        else:
            self.stdout.write(
                self.style.ERROR('Please specify either --player <name> or --all')
            )
            return

    def import_all_players(self, force=False, limit=None):
        """
        Import data for all players in the elo_data directory.
        """
        elo_data_dir = 'elo_data'
        
        if not os.path.exists(elo_data_dir):
            raise CommandError(f'Directory {elo_data_dir} does not exist')
        
        # Find all CSV files
        csv_files = []
        for filename in os.listdir(elo_data_dir):
            if filename.endswith('.csv'):
                player_name = filename.replace('.csv', '')
                csv_files.append(player_name)
        
        if not csv_files:
            self.stdout.write(
                self.style.WARNING(f'No CSV files found in {elo_data_dir}')
            )
            return
        
        # Apply limit if specified
        if limit:
            csv_files = csv_files[:limit]
            self.stdout.write(f'Processing first {limit} players only')
        
        self.stdout.write(f'Found {len(csv_files)} player files to import')
        
        success_count = 0
        error_count = 0
        
        for player_name in csv_files:
            try:
                self.import_player(player_name, force, verbose=False)
                success_count += 1
                if success_count % 50 == 0:  # Progress indicator
                    self.stdout.write(f'Processed {success_count} players...')
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Error importing {player_name}: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Import complete: {success_count} successful, {error_count} errors'
            )
        )

    def import_player(self, player_name, force=False, verbose=True):
        """
        Import data for a specific player.
        """
        csv_path = f'elo_data/{player_name}.csv'
        
        if not os.path.exists(csv_path):
            raise CommandError(f'CSV file {csv_path} does not exist')
        
        # Check if data already exists
        existing_count = PlayerMatch.objects.filter(player_name=player_name).count()
        if existing_count > 0 and not force:
            if verbose:
                self.stdout.write(
                    self.style.WARNING(
                        f'Data for {player_name} already exists ({existing_count} matches). '
                        f'Use --force to reimport.'
                    )
                )
            return
        
        # Delete existing data if force is True
        if force and existing_count > 0:
            PlayerMatch.objects.filter(player_name=player_name).delete()
            if verbose:
                self.stdout.write(
                    self.style.SUCCESS(f'Deleted {existing_count} existing matches for {player_name}')
                )
        
        try:
            # Read CSV file
            if verbose:
                self.stdout.write(f'Reading CSV file: {csv_path}')
            df = pd.read_csv(csv_path)
            
            # Validate required columns
            required_columns = ['Season', 'Date', 'Comp', 'Opponent', 'Result', 'Min', 'Gls', 'Ast', 'Elo']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise CommandError(f'Missing required columns in {csv_path}: {missing_columns}')
            
            # Clean and validate data
            df = df.dropna(subset=['Date', 'Elo'])
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            df = df.dropna(subset=['Date'])  # Remove rows with invalid dates
            
            if len(df) == 0:
                raise CommandError(f'No valid data found in {csv_path}')
            
            # Import data in batches for better performance
            with transaction.atomic():
                matches_created = 0
                batch_size = 100
                matches_to_create = []
                
                for _, row in df.iterrows():
                    # Parse result to extract goals conceded (for goalkeepers)
                    goals_conceded = 0
                    clean_sheet = False
                    try:
                        result_clean = str(row['Result']).replace('W ', '').replace('L ', '').replace('D ', '').strip()
                        if '–' in result_clean or '-' in result_clean:
                            result_clean = result_clean.replace('–', '-')
                            parts = result_clean.split('-')
                            if len(parts) == 2:
                                goals_conceded = int(parts[1])
                                clean_sheet = goals_conceded == 0
                    except:
                        pass  # If parsing fails, keep defaults
                    
                    match = PlayerMatch(
                        player_name=player_name,
                        season=str(row['Season']),
                        date=row['Date'].date(),
                        competition=str(row['Comp']),
                        round_info=str(row.get('Round', '')),
                        opponent=str(row['Opponent']),
                        result=str(row['Result']),
                        position=str(row.get('Pos', '')),
                        minutes_played=int(row.get('Min', 0)),
                        goals=int(row.get('Gls', 0)),
                        assists=int(row.get('Ast', 0)),
                        points=int(row.get('Points', 0)),
                        elo_after_match=float(row['Elo']),
                        saves=int(row.get('Saves', 0)),
                        goals_conceded=goals_conceded,
                        clean_sheet=clean_sheet,
                    )
                    
                    matches_to_create.append(match)
                    
                    # Create in batches
                    if len(matches_to_create) >= batch_size:
                        PlayerMatch.objects.bulk_create(matches_to_create, ignore_conflicts=True)
                        matches_created += len(matches_to_create)
                        matches_to_create = []
                
                # Create remaining matches
                if matches_to_create:
                    PlayerMatch.objects.bulk_create(matches_to_create, ignore_conflicts=True)
                    matches_created += len(matches_to_create)
            
            if verbose:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully imported {matches_created} matches for {player_name}'
                    )
                )
            
            # Show statistics
            if verbose:
                total_matches = PlayerMatch.objects.filter(player_name=player_name).count()
                latest_elo = PlayerMatch.get_latest_elo(player_name)
                
                self.stdout.write(f'{player_name} statistics:')
                self.stdout.write(f'  Total matches: {total_matches}')
                self.stdout.write(f'  Latest Elo: {latest_elo}')
                
                # Season breakdown
                seasons = PlayerMatch.objects.filter(player_name=player_name).values('season').distinct()
                for season_data in seasons:
                    season = season_data['season']
                    count = PlayerMatch.objects.filter(player_name=player_name, season=season).count()
                    self.stdout.write(f'  {season}: {count} matches')
                
        except Exception as e:
            raise CommandError(f'Error importing {player_name}: {str(e)}')