"""
Django management command to import existing CSV data from elo_data folder into the database.
This is much faster than calling the FPL API when you already have the data.
"""

import csv
import os
import glob
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from MyApi.models import Player, PlayerMatch, EloCalculation, SystemSettings


class Command(BaseCommand):
    help = 'Import existing CSV data from elo_data folder into database tables'

    def add_arguments(self, parser):
        parser.add_argument(
            '--week',
            type=int,
            default=4,
            help='Week number to import data for (default: 4)',
        )
        parser.add_argument(
            '--season',
            type=str,
            default='2024-25',
            help='Season to import data for (default: 2024-25)',
        )

    def handle(self, *args, **options):
        week = options['week']
        season = options['season']
        
        self.stdout.write(f'Importing player data from elo_data folder for Week {week}, Season {season}')
        
        try:
            # Import player data from individual CSV files
            self.import_player_data_from_elo_folder(week, season)
            
            # Import current Elo ratings
            self.import_current_elos(week, season)
            
            # Update system settings
            self.update_system_settings(week, season)
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully imported player data for week {week}')
            )
                
        except Exception as e:
            raise CommandError(f'Error importing CSV data: {str(e)}')
    
    def import_player_data_from_elo_folder(self, week, season):
        """Import player match data from individual CSV files in elo_data folder"""
        elo_data_folder = 'elo_data'
        
        if not os.path.exists(elo_data_folder):
            self.stdout.write(self.style.WARNING(f'Folder {elo_data_folder} not found'))
            return
        
        # Get all CSV files in the elo_data folder
        csv_files = glob.glob(os.path.join(elo_data_folder, '*.csv'))
        
        self.stdout.write(f'Found {len(csv_files)} player files in {elo_data_folder}')
        
        total_matches = 0
        players_processed = 0
        
        for csv_file in csv_files:
            player_name = os.path.basename(csv_file).replace('.csv', '').replace('_', ' ')
            
            try:
                with open(csv_file, 'r', encoding='utf-8') as file:
                    reader = csv.DictReader(file)
                    
                    matches_imported = 0
                    latest_elo = 1500  # Default
                    
                    for row in reader:
                        try:
                            # Parse match data
                            season_year = row['Season']
                            date_str = row['Date']
                            competition = row['Comp']
                            round_info = row['Round']
                            opponent = row['Opponent']
                            result = row['Result']
                            position = row['Pos']
                            minutes = int(float(row['Min'])) if row['Min'] else 0
                            goals = int(float(row['Gls'])) if row['Gls'] else 0
                            assists = int(float(row['Ast'])) if row['Ast'] else 0
                            points = int(float(row['Points'])) if row['Points'] else 0
                            elo_after = float(row['Elo']) if row['Elo'] else 1500
                            
                            # Parse date
                            match_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                            
                            # Create PlayerMatch record
                            PlayerMatch.objects.update_or_create(
                                player_name=player_name,
                                date=match_date,
                                opponent=opponent,
                                defaults={
                                    'season': season_year,
                                    'competition': competition,
                                    'round_info': round_info,
                                    'result': result,
                                    'position': position,
                                    'minutes_played': minutes,
                                    'goals': goals,
                                    'assists': assists,
                                    'points': points,
                                    'elo_after_match': elo_after,
                                    'saves': 0,
                                    'goals_conceded': 0,
                                    'clean_sheet': 'W' in result and goals == 0,
                                    'created_at': datetime.now(),
                                    'updated_at': datetime.now(),
                                }
                            )
                            
                            matches_imported += 1
                            latest_elo = elo_after
                            
                        except Exception as e:
                            self.stdout.write(f'Error importing match for {player_name}: {str(e)}')
                            continue
                    
                    # Determine position from the most recent match
                    position_mapping = {
                        'GK': 'Keeper',
                        'RB': 'Defender', 'LB': 'Defender', 'CB': 'Defender', 'WB': 'Defender',
                        'DM': 'Midfielder', 'CM': 'Midfielder', 'AM': 'Midfielder', 'RM': 'Midfielder', 'LM': 'Midfielder',
                        'RW': 'Attacker', 'LW': 'Attacker', 'CF': 'Attacker', 'ST': 'Attacker'
                    }
                    
                    # Get the most common position or default to Midfielder
                    main_position = 'Midfielder'
                    if position:
                        for key, value in position_mapping.items():
                            if key in position:
                                main_position = value
                                break
                    
                    # Calculate cost based on Elo (simple formula)
                    cost = max(4.0, min(15.0, (latest_elo - 1000) / 200 + 4.5))
                    
                    # Create Player record for current week
                    Player.objects.update_or_create(
                        name=player_name,
                        week=week,
                        defaults={
                            'position': main_position,
                            'elo': latest_elo,
                            'cost': round(cost, 1),
                            'team': '',
                            'competition': 'Premier League',
                            'created_at': datetime.now(),
                            'updated_at': datetime.now(),
                        }
                    )
                    
                    # Create EloCalculation record
                    EloCalculation.objects.update_or_create(
                        player_name=player_name,
                        week=week,
                        season=season,
                        defaults={
                            'elo': latest_elo,
                            'previous_elo': latest_elo,
                            'elo_change': 0.0,
                            'matches_played': 1 if matches_imported > 0 else 0,
                            'last_match_date': datetime.now().date(),
                            'created_at': datetime.now(),
                            'updated_at': datetime.now(),
                        }
                    )
                    
                    total_matches += matches_imported
                    players_processed += 1
                    
                    if players_processed % 50 == 0:
                        self.stdout.write(f'Processed {players_processed} players...')
                        
            except Exception as e:
                self.stdout.write(f'Error processing file {csv_file}: {str(e)}')
                continue
        
        self.stdout.write(f'Imported {total_matches} matches for {players_processed} players')
    
    def import_current_elos(self, week, season):
        """Import current Elo ratings from elos.csv if available"""
        csv_file = 'elos.csv'
        
        if not os.path.exists(csv_file):
            self.stdout.write(f'File {csv_file} not found, using Elo from individual files')
            return
        
        self.stdout.write(f'Updating Elo ratings from {csv_file}...')
        
        updated_count = 0
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                try:
                    player_name = row['Player'].replace('_', ' ')
                    position = row['Position']
                    elo = float(row['Elo'])
                    cost = float(row['Cost'])
                    
                    # Update Player record if it exists
                    try:
                        player = Player.objects.get(name=player_name, week=week)
                        player.elo = elo
                        player.cost = cost
                        player.position = position
                        player.save()
                        updated_count += 1
                    except Player.DoesNotExist:
                        # Create new player if not found
                        Player.objects.create(
                            name=player_name,
                            week=week,
                            position=position,
                            elo=elo,
                            cost=cost,
                            team='',
                            competition='Premier League',
                        )
                        updated_count += 1
                        
                except Exception as e:
                    self.stdout.write(f'Error updating {player_name}: {str(e)}')
                    continue
        
        self.stdout.write(f'Updated {updated_count} player ratings from elos.csv')
    
    def update_system_settings(self, week, season):
        """Update system settings with current week and season"""
        settings = SystemSettings.get_settings()
        settings.current_gameweek = week
        settings.current_season = season
        settings.last_data_update = datetime.now()
        settings.save()
        
        self.stdout.write(f'Updated system settings: Week {week}, Season {season}')