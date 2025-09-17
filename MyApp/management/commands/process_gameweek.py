"""
Django management command to process current gameweek data and update database.
This replaces the CSV-based weekly data processing.
"""

from django.core.management.base import BaseCommand, CommandError
from asgiref.sync import async_to_sync
from fantasy_models.weekly_data_db import WeeklyDataProcessorDB


class Command(BaseCommand):
    help = 'Process current gameweek data from FPL API and update player Elo ratings'

    def add_arguments(self, parser):
        parser.add_argument(
            '--week',
            type=int,
            required=True,
            help='Week number to process (e.g., --week 4)',
        )
        parser.add_argument(
            '--season',
            type=str,
            default='2024-2025',
            help='Season to process for (e.g., --season 2024-2025)',
        )

    def handle(self, *args, **options):
        week = options['week']
        season = options['season']
        
        self.stdout.write(f'Processing gameweek data for Week {week}, Season {season}')
        
        try:
            # Run the async processing using async_to_sync to handle Django ORM properly
            processor = WeeklyDataProcessorDB()
            success = async_to_sync(processor.process_weekly_data)(week, season)
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully processed gameweek {week} data')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'Failed to process gameweek {week} data')
                )
                
        except Exception as e:
            raise CommandError(f'Error processing gameweek data: {str(e)}')