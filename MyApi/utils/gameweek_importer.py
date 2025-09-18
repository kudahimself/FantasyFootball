"""
Current Gameweek Data Importer

This module handles importing current gameweek data from FPL API into our database.
Safely appends new data without destroying existing records.

Key features:
- Fetches current gameweek player performance data from FPL API
- Converts to our PlayerMatch model format
- Prevents duplicate data with safe deduplication
- Calculates fantasy points from FPL statistics
- Updates only missing gameweek data
"""

import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, List, Any, Optional
from asgiref.sync import sync_to_async


async def get_current_gameweek_data() -> Dict[str, Any]:
    """
    Fetch current gameweek data from FPL API and import into database
    
    Returns:
        Dict[str, Any]: Import summary with success status and details
    """
    try:
        from fpl import FPL
        from MyApi.models import PlayerMatch, SystemSettings, Player
        
        print("🚀 Starting Current Gameweek Data Import")
        start_time = datetime.now()
        
        async with aiohttp.ClientSession() as session:
            fpl = FPL(session)
            
            # Get current gameweek
            gameweeks = await fpl.get_gameweeks()
            current_gw = next(gw for gw in gameweeks if gw.is_current)
            gw_id = current_gw.id
            
            print(f"📅 Current Gameweek: {gw_id}")
            
            # Update system settings with current gameweek if needed
            settings = await sync_to_async(SystemSettings.get_settings)()
            if settings.current_gameweek != gw_id:
                settings.current_gameweek = gw_id
                await sync_to_async(settings.save)()
                print(f"✅ Updated system gameweek to {gw_id}")
            
            # Get teams for opponent mapping
            teams = await fpl.get_teams()
            team_map = {team.id: team.short_name for team in teams}
            
            # Get all players
            players = await fpl.get_players()
            
            new_matches = 0
            updated_matches = 0
            skipped_matches = 0
            errors = 0
            
            print(f"👥 Processing {len(players)} players...")
            
            for i, player in enumerate(players, 1):
                try:
                    player_name = f"{player.first_name} {player.second_name}"
                    
                    # Get player's gameweek history
                    history = await fpl.get_player_summary(player.id)
                    
                    # Find current gameweek entry
                    gw_entry = None
                    for g in history.history:
                        if g.get('event') == gw_id or g.get('round') == gw_id:
                            gw_entry = g
                            break
                    
                    if not gw_entry:
                        continue  # No data for this gameweek
                    
                    # Extract match data
                    match_date = None
                    if gw_entry.get('kickoff_time'):
                        match_date = datetime.fromisoformat(
                            gw_entry['kickoff_time'].replace("Z", "")
                        ).date()
                    
                    # Get opponent team
                    opponent_team_id = gw_entry.get('opponent_team')
                    opponent = team_map.get(opponent_team_id, f"Team {opponent_team_id}") if opponent_team_id else "Unknown"
                    
                    # Calculate result
                    was_home = gw_entry.get('was_home', False)
                    team_h_score = gw_entry.get('team_h_score', 0)
                    team_a_score = gw_entry.get('team_a_score', 0)
                    
                    if was_home:
                        result = f"{'W' if team_h_score > team_a_score else 'L' if team_h_score < team_a_score else 'D'} {team_h_score}-{team_a_score}"
                    else:
                        result = f"{'W' if team_a_score > team_h_score else 'L' if team_a_score < team_h_score else 'D'} {team_a_score}-{team_h_score}"
                    
                    # Calculate fantasy points (simplified FPL scoring)
                    minutes = gw_entry.get('minutes', 0)
                    goals = gw_entry.get('goals_scored', 0)
                    assists = gw_entry.get('assists', 0)
                    clean_sheets = gw_entry.get('clean_sheets', 0)
                    goals_conceded = gw_entry.get('goals_conceded', 0)
                    saves = gw_entry.get('saves', 0)
                    yellow_cards = gw_entry.get('yellow_cards', 0)
                    red_cards = gw_entry.get('red_cards', 0)
                    bonus = gw_entry.get('bonus', 0)
                    
                    # Basic FPL points calculation
                    points = 0
                    if minutes > 0:
                        points += 1  # Playing
                    if minutes >= 60:
                        points += 1  # 60+ minutes
                    
                    points += goals * 4  # Goals (simplified - varies by position)
                    points += assists * 3  # Assists
                    points += clean_sheets * 4  # Clean sheets (simplified)
                    points += saves // 3  # Every 3 saves = 1 point
                    points -= yellow_cards  # Yellow card
                    points -= red_cards * 3  # Red card
                    points += bonus  # Bonus points
                    
                    # Check if match already exists (improved deduplication)
                    existing_match = await sync_to_async(
                        PlayerMatch.objects.filter(
                            player_name=player_name,
                            date=match_date,
                            round_info__in=[f"Gameweek {gw_id}", f"Matchweek {gw_id}", str(gw_id)]
                        ).first
                    )()
                    
                    match_data = {
                        'player_name': player_name,
                        'season': f"{datetime.now().year}-{datetime.now().year + 1}",
                        'date': match_date,
                        'competition': 'Premier League',
                        'round_info': f"Gameweek {gw_id}",
                        'opponent': opponent,
                        'result': result,
                        'position': player.position if hasattr(player, 'position') else '',
                        'minutes_played': minutes,
                        'goals': goals,
                        'assists': assists,
                        'points': points,
                        'saves': saves,
                        'goals_conceded': goals_conceded,
                        'clean_sheet': clean_sheets > 0,
                        'elo_before_match': 1200.0,  # Will be calculated later
                        'elo_after_match': 1200.0,   # Will be calculated later
                    }
                    
                    if existing_match:
                        # Update existing match if data has changed
                        updated = False
                        for field, value in match_data.items():
                            if hasattr(existing_match, field) and getattr(existing_match, field) != value:
                                setattr(existing_match, field, value)
                                updated = True
                        
                        if updated:
                            await sync_to_async(existing_match.save)()
                            updated_matches += 1
                        else:
                            skipped_matches += 1
                    else:
                        # Create new match record
                        await sync_to_async(PlayerMatch.objects.create)(**match_data)
                        new_matches += 1
                    
                    # Show progress every 100 players
                    if i % 100 == 0:
                        print(f"🔄 Processed {i}/{len(players)} players...")
                        
                except Exception as e:
                    errors += 1
                    if errors <= 5:  # Show first few errors
                        print(f"❌ Error processing {player.first_name} {player.second_name}: {e}")
            
            # Summary
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            print(f"✅ Gameweek {gw_id} data import complete!")
            print(f"   New matches: {new_matches}")
            print(f"   Updated matches: {updated_matches}")
            print(f"   Skipped matches: {skipped_matches}")
            print(f"   Errors: {errors}")
            print(f"   Duration: {duration:.2f} seconds")
            
            return {
                'success': True,
                'gameweek': gw_id,
                'new_matches': new_matches,
                'updated_matches': updated_matches,
                'skipped_matches': skipped_matches,
                'errors': errors,
                'duration': duration,
                'total_players': len(players)
            }
            
    except Exception as e:
        print(f"❌ Fatal error during gameweek data import: {e}")
        return {
            'success': False,
            'error': str(e)
        }


async def refresh_current_gameweek_players() -> Dict[str, Any]:
    """
    Convenience function to refresh current gameweek player data
    
    Returns:
        Dict[str, Any]: Import result summary
    """
    return await get_current_gameweek_data()


# Standalone execution
if __name__ == "__main__":
    import os
    import django
    
    # Setup Django if running standalone
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')
    django.setup()
    
    # Run the import
    result = asyncio.run(get_current_gameweek_data())
    
    if result['success']:
        print(f"\n🎉 Success: Imported gameweek {result['gameweek']} data")
        print(f"   {result['new_matches']} new matches added")
        print(f"   {result['updated_matches']} matches updated")
    else:
        print(f"\n💥 Failed: {result['error']}")