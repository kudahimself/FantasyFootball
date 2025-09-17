"""
Database-backed version of weekly data processing that replaces CSV file usage.
This replaces the weekly_data.py functionality.
"""

import os
import sys
import django
from datetime import datetime
import asyncio
import aiohttp
from fpl import FPL
from asgiref.sync import sync_to_async

# Setup Django environment for standalone use
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    # Add the project root to the Python path
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.append(project_root)
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')
    django.setup()

from MyApi.models import PlayerMatch, Player, EloCalculation
from fantasy_models.elo_model_db import FootballerEloModelDB


class WeeklyDataProcessorDB:
    """
    Database-backed weekly data processor that handles current gameweek data.
    """
    
    def __init__(self):
        self.current_gw_data = []
        self.players_data = {}
    
    async def get_current_gw_player_details(self):
        """
        Fetch current gameweek player details from FPL API and store in database.
        """
        async with aiohttp.ClientSession() as session:
            fpl = FPL(session)
            
            try:
                gameweeks = await fpl.get_gameweeks()
                current_gw = next(gw for gw in gameweeks if gw.is_current)
                gw_id = current_gw.id
                
                print(f"Processing gameweek {gw_id}")
                
                players = await fpl.get_players()
                
                for player in players:
                    try:
                        history = await fpl.get_player_summary(player.id)
                        
                        # Find the current gameweek entry
                        gw_entry = None
                        for g in history.history:
                            if 'event' in g and g['event'] == gw_id:
                                gw_entry = g
                                break
                            elif 'round' in g and g['round'] == gw_id:
                                gw_entry = g
                                break
                        
                        if gw_entry:
                            # Process player data
                            player_data = {
                                'name': self.clean_player_name(player.web_name),
                                'team': player.team,
                                'position': self.map_fpl_position(player.element_type),
                                'total_points': gw_entry.get('total_points', 0),
                                'minutes': gw_entry.get('minutes', 0),
                                'goals_scored': gw_entry.get('goals_scored', 0),
                                'assists': gw_entry.get('assists', 0),
                                'clean_sheets': gw_entry.get('clean_sheets', 0),
                                'goals_conceded': gw_entry.get('goals_conceded', 0),
                                'saves': gw_entry.get('saves', 0),
                                'bonus': gw_entry.get('bonus', 0),
                                'bps': gw_entry.get('bps', 0),
                                'influence': gw_entry.get('influence', 0),
                                'creativity': gw_entry.get('creativity', 0),
                                'threat': gw_entry.get('threat', 0),
                                'ict_index': gw_entry.get('ict_index', 0),
                                'value': gw_entry.get('value', 0),
                                'transfers_balance': gw_entry.get('transfers_balance', 0),
                                'selected': gw_entry.get('selected', 0),
                                'transfers_in': gw_entry.get('transfers_in', 0),
                                'transfers_out': gw_entry.get('transfers_out', 0),
                            }
                            
                            self.current_gw_data.append(player_data)
                            self.players_data[player_data['name']] = player_data
                    
                    except Exception as e:
                        print(f"Error processing player {player.web_name}: {str(e)}")
                        continue
                
                print(f"Fetched data for {len(self.current_gw_data)} players")
                return self.current_gw_data
                
            except Exception as e:
                print(f"Error fetching gameweek data: {str(e)}")
                return []
    
    def clean_player_name(self, web_name):
        """
        Clean player names to match the format used in our database.
        """
        # You might need to implement name mapping logic here
        # For now, just return the web_name
        return web_name.replace(' ', '_')
    
    def map_fpl_position(self, element_type):
        """
        Map FPL position codes to our standard positions.
        """
        position_map = {
            1: 'Keeper',      # Goalkeeper
            2: 'Defender',    # Defender
            3: 'Midfielder',  # Midfielder
            4: 'Attacker',    # Forward
        }
        return position_map.get(element_type, 'Midfielder')
    
    async def update_player_elos_from_gameweek(self, week, season="2024-2025"):
        """
        Update player Elo ratings based on current gameweek performance.
        """
        print(f"Updating Elo ratings for week {week}")
        
        updated_count = 0
        
        for player_name, player_data in self.players_data.items():
            try:
                # Check if player exists in our historical data
                if not PlayerMatch.objects.filter(player_name=player_name).exists():
                    print(f"No historical data for {player_name}, skipping Elo update")
                    continue
                
                # Get current Elo
                try:
                    elo_model = FootballerEloModelDB(player_name)
                    current_elo = elo_model.get_current_elo()
                except Exception as e:
                    print(f"Error getting Elo for {player_name}: {str(e)}")
                    current_elo = 1200.0  # Default Elo
                
                # Calculate Elo change based on performance
                elo_change = self.calculate_elo_change_from_performance(player_data)
                new_elo = current_elo + elo_change
                
                # Update or create Player record
                player, created = await sync_to_async(Player.objects.update_or_create)(
                    name=player_name,
                    week=week,
                    defaults={
                        'position': player_data['position'],
                        'elo': new_elo,
                        'cost': self.calculate_cost_from_performance(player_data, new_elo),
                        'team': str(player_data.get('team', '')),
                        'competition': 'Premier League',
                    }
                )
                
                # Update EloCalculation record
                await sync_to_async(EloCalculation.objects.update_or_create)(
                    player_name=player_name,
                    week=week,
                    season=season,
                    defaults={
                        'elo_rating': new_elo,
                        'previous_elo': current_elo,
                        'elo_change': elo_change,
                        'matches_played': 1 if player_data['minutes'] > 0 else 0,
                        'last_match_date': datetime.now().date(),
                        'form_rating': self.calculate_form_rating(player_data),
                    }
                )
                
                updated_count += 1
                
            except Exception as e:
                print(f"Error updating {player_name}: {str(e)}")
                continue
        
        print(f"Updated Elo ratings for {updated_count} players")
        return updated_count
    
    def calculate_elo_change_from_performance(self, player_data):
        """
        Calculate Elo rating change based on gameweek performance.
        """
        minutes = player_data.get('minutes', 0)
        goals = player_data.get('goals_scored', 0)
        assists = player_data.get('assists', 0)
        total_points = player_data.get('total_points', 0)
        
        # Base change from total points
        elo_change = total_points * 2
        
        # Bonus for goals and assists
        elo_change += goals * 5
        elo_change += assists * 3
        
        # Minutes played factor
        if minutes >= 90:
            elo_change += 2
        elif minutes >= 60:
            elo_change += 1
        elif minutes == 0:
            elo_change -= 5  # Penalty for not playing
        
        # Position-specific bonuses
        position = player_data.get('position', '')
        if position == 'Keeper':
            clean_sheets = player_data.get('clean_sheets', 0)
            saves = player_data.get('saves', 0)
            elo_change += clean_sheets * 4
            elo_change += saves * 0.5
        
        # Cap the change
        return max(-30, min(30, elo_change))
    
    def calculate_cost_from_performance(self, player_data, elo_rating):
        """
        Calculate player cost based on performance and Elo.
        """
        # Base cost from Elo
        if elo_rating >= 2000:
            base_cost = 12.0
        elif elo_rating >= 1800:
            base_cost = 9.0
        elif elo_rating >= 1600:
            base_cost = 6.5
        elif elo_rating >= 1400:
            base_cost = 5.0
        else:
            base_cost = 4.0
        
        # Adjust based on recent performance
        total_points = player_data.get('total_points', 0)
        if total_points >= 10:
            base_cost += 0.5
        elif total_points >= 6:
            base_cost += 0.2
        elif total_points <= 0:
            base_cost -= 0.3
        
        return min(15.0, max(4.0, round(base_cost, 1)))
    
    def calculate_form_rating(self, player_data):
        """
        Calculate a form rating based on recent performance.
        """
        total_points = player_data.get('total_points', 0)
        minutes = player_data.get('minutes', 0)
        
        if minutes == 0:
            return -1.0  # Didn't play
        
        # Normalize points by minutes played
        points_per_minute = total_points / minutes if minutes > 0 else 0
        
        return points_per_minute * 90  # Scale to full match
    
    async def process_weekly_data(self, week, season="2024-2025"):
        """
        Complete weekly data processing pipeline.
        """
        print(f"Starting weekly data processing for week {week}")
        
        # Fetch current gameweek data
        await self.get_current_gw_player_details()
        
        if not self.current_gw_data:
            print("No gameweek data fetched, aborting")
            return False
        
        # Update Elo ratings
        updated_count = self.update_player_elos_from_gameweek(week, season)
        
        print(f"Weekly data processing complete. Updated {updated_count} players.")
        return True


# Standalone function for command-line usage
async def main():
    """
    Main function for standalone execution.
    """
    processor = WeeklyDataProcessorDB()
    
    # Get current week (you might want to make this configurable)
    current_week = 4  # Example
    
    success = await processor.process_weekly_data(current_week)
    
    if success:
        print("Weekly data processing completed successfully!")
    else:
        print("Weekly data processing failed!")


if __name__ == "__main__":
    asyncio.run(main())