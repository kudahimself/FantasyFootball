"""
Django management command to import weekly Elo data from CSV files into the database.
"""

import os
import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from MyApi.models import Player


class Command(BaseCommand):
    help = 'Import weekly Elo data from CSV files into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--week',
            type=int,
            help='Import data for a specific week (e.g., --week 4)',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Import data for all available weeks',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reimport (delete existing data for the week)',
        )

    def handle(self, *args, **options):
        """
        Main command handler.
        """
        if options['all']:
            self.import_all_weeks(options['force'])
        elif options['week']:
            self.import_week(options['week'], options['force'])
        else:
            self.stdout.write(
                self.style.ERROR('Please specify either --week <number> or --all')
            )
            return

    def import_all_weeks(self, force=False):
        """
        Import data for all available weekly CSV files.
        """
        weekly_elo_dir = 'weekly_elo'
        
        if not os.path.exists(weekly_elo_dir):
            raise CommandError(f'Directory {weekly_elo_dir} does not exist')
        
        # Find all weekly_elo_*.csv files
        csv_files = []
        for filename in os.listdir(weekly_elo_dir):
            if filename.startswith('weekly_elo_') and filename.endswith('.csv'):
                try:
                    week_num = int(filename.replace('weekly_elo_', '').replace('.csv', ''))
                    csv_files.append((week_num, filename))
                except ValueError:
                    self.stdout.write(
                        self.style.WARNING(f'Skipping file with invalid format: {filename}')
                    )
        
        if not csv_files:
            self.stdout.write(
                self.style.WARNING(f'No weekly_elo_*.csv files found in {weekly_elo_dir}')
            )
            return
        
        # Sort by week number
        csv_files.sort(key=lambda x: x[0])
        
        self.stdout.write(f'Found {len(csv_files)} weekly files to import')
        
        for week_num, filename in csv_files:
            self.import_week(week_num, force)

    def import_week(self, week, force=False):
        """
        Import data for a specific week.
        """
        csv_path = f'weekly_elo/weekly_elo_{week}.csv'
        
        if not os.path.exists(csv_path):
            raise CommandError(f'CSV file {csv_path} does not exist')
        
        # Check if data already exists
        existing_count = Player.objects.filter(week=week).count()
        if existing_count > 0 and not force:
            self.stdout.write(
                self.style.WARNING(
                    f'Data for week {week} already exists ({existing_count} players). '
                    f'Use --force to reimport.'
                )
            )
            return
        
        # Delete existing data if force is True
        if force and existing_count > 0:
            Player.objects.filter(week=week).delete()
            self.stdout.write(
                self.style.SUCCESS(f'Deleted {existing_count} existing players for week {week}')
            )
        
        try:
            # Read CSV file
            self.stdout.write(f'Reading CSV file: {csv_path}')
            df = pd.read_csv(csv_path)
            
            # Validate required columns
            required_columns = ['Player', 'Position', 'Elo', 'Cost']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise CommandError(f'Missing required columns: {missing_columns}')
            
            # Clean and validate data
            df = df.dropna(subset=required_columns)
            df['Elo'] = pd.to_numeric(df['Elo'], errors='coerce')
            df['Cost'] = pd.to_numeric(df['Cost'], errors='coerce')
            df = df.dropna(subset=['Elo', 'Cost'])
            
            if len(df) == 0:
                raise CommandError(f'No valid data found in {csv_path}')
            
            # Import data in a transaction
            with transaction.atomic():
                players_created = 0
                for _, row in df.iterrows():
                    player, created = Player.objects.get_or_create(
                        name=row['Player'],
                        week=week,
                        defaults={
                            'position': row['Position'],
                            'elo': float(row['Elo']),
                            'cost': float(row['Cost']),
                            'team': row.get('Team', ''),
                            'competition': row.get('Competition', 'Premier League'),
                        }
                    )
                    
                    if created:
                        players_created += 1
                    else:
                        # Update existing player data
                        player.position = row['Position']
                        player.elo = float(row['Elo'])
                        player.cost = float(row['Cost'])
                        player.team = row.get('Team', '')
                        player.competition = row.get('Competition', 'Premier League')
                        player.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully imported {players_created} players for week {week}'
                )
            )
            
            # Show statistics
            total_players = Player.objects.filter(week=week).count()
            position_stats = {}
            for position_choice in Player.POSITION_CHOICES:
                position = position_choice[0]
                count = Player.objects.filter(week=week, position=position).count()
                position_stats[position] = count
            
            self.stdout.write(f'Week {week} statistics:')
            self.stdout.write(f'  Total players: {total_players}')
            for position, count in position_stats.items():
                self.stdout.write(f'  {position}: {count}')
                
        except Exception as e:
            raise CommandError(f'Error importing week {week}: {str(e)}')