"""
Season Gameweek Data Importer

This module handles importing all gameweek data for the current season (2025-26) from FPL API.
Provides clean, consistent data to replace manually imported/incorrect data.

Key features:
- Fetches all gameweek data for the current season from FPL API
- Converts to our PlayerMatch model format with proper team names
- Safe deduplication to prevent duplicate entries
- Comprehensive season data import
- Clean opponent names (team abbreviations)
"""

import asyncio
import aiohttp
from datetime import datetime, date
from typing import Dict, List, Any, Optional
from asgiref.sync import sync_to_async


async def import_season_gameweeks(season_year: str = "2025-26", start_gw: int = 1, end_gw: Optional[int] = None) -> Dict[str, Any]:
    """
    Import all gameweek data for the specified season
    
    Args:
        season_year: Season identifier (e.g., "2025-26")
        start_gw: Starting gameweek (default: 1)
        end_gw: Ending gameweek (default: current gameweek or 38)
    
    Returns:
        Dict[str, Any]: Import summary with detailed statistics
    """
    try:
        from fpl import FPL
        from MyApi.models import PlayerMatch, SystemSettings, Player
        
        print(f"🚀 Starting Season {season_year} Gameweek Data Import")
        print(f"📅 Importing gameweeks {start_gw} to {end_gw or 'current'}")
        start_time = datetime.now()
        
        async with aiohttp.ClientSession() as session:
            fpl = FPL(session)
            
            # Get all gameweeks
            gameweeks = await fpl.get_gameweeks()
            
            # Determine end gameweek if not specified
            if end_gw is None:
                # Find current or latest finished gameweek
                current_gw = next((gw for gw in gameweeks if gw.is_current), None)
                if current_gw:
                    end_gw = current_gw.id
                else:
                    # Find latest finished gameweek
                    finished_gws = [gw for gw in gameweeks if gw.finished]
                    end_gw = max(finished_gws, key=lambda x: x.id).id if finished_gws else 1
            
            print(f"📊 Target range: Gameweeks {start_gw} to {end_gw}")
            
            # Get teams for opponent mapping
            teams = await fpl.get_teams()
            team_map = {team.id: team.short_name for team in teams}
            
            print(f"🏟️  Found {len(team_map)} teams:")
            for team_id, team_name in sorted(team_map.items()):
                print(f"   {team_id:2d}: {team_name}")
            
            # Get all players
            players = await fpl.get_players()
            print(f"👥 Processing {len(players)} players...")
            
            # Statistics tracking
            total_new_matches = 0
            total_updated_matches = 0
            total_skipped_matches = 0
            total_errors = 0
            gameweek_stats = {}
            
            # Process each gameweek
            for gw_num in range(start_gw, end_gw + 1):
                print(f"\\n🔄 Processing Gameweek {gw_num}...")
                
                gw_new = 0
                gw_updated = 0
                gw_skipped = 0
                gw_errors = 0
                
                # Get gameweek info
                gw_info = next((gw for gw in gameweeks if gw.id == gw_num), None)
                if not gw_info:
                    print(f"⚠️  Gameweek {gw_num} not found, skipping...")
                    continue
                
                # Skip if gameweek hasn't started yet
                if not gw_info.finished and not gw_info.is_current:
                    print(f"⏭️  Gameweek {gw_num} not started yet, skipping...")
                    continue
                
                # Process each player for this gameweek
                for i, player in enumerate(players):
                    try:
                        player_name = f"{player.first_name} {player.second_name}".strip()
                        
                        # Get player's gameweek history
                        history = await fpl.get_player_summary(player.id)
                        
                        # Find specific gameweek entry
                        gw_entry = None
                        for h in history.history:
                            if h.get('event') == gw_num or h.get('round') == gw_num:
                                gw_entry = h
                                break
                        
                        if not gw_entry:
                            continue  # No data for this gameweek
                        
                        # Extract match data - improved date handling
                        match_date = None
                        
                        # Try to get date from gw_entry first (more accurate)
                        if gw_entry.get('kickoff_time'):
                            try:
                                match_date = datetime.fromisoformat(
                                    str(gw_entry['kickoff_time']).replace("Z", "")
                                ).date()
                            except:
                                pass
                        
                        # Fallback to gameweek deadline
                        if not match_date and gw_info.deadline_time:
                            try:
                                if hasattr(gw_info.deadline_time, 'date'):
                                    match_date = gw_info.deadline_time.date()
                                else:
                                    parsed_date = datetime.fromisoformat(str(gw_info.deadline_time).replace('Z', ''))
                                    match_date = parsed_date.date()
                            except:
                                pass
                        
                        # Final fallback
                        if not match_date:
                            match_date = date.today()
                        
                        # Get opponent team
                        opponent_team_id = gw_entry.get('opponent_team')
                        opponent = team_map.get(opponent_team_id, f"Team_{opponent_team_id}") if opponent_team_id else "Unknown"
                        
                        # Calculate result
                        was_home = gw_entry.get('was_home', False)
                        team_h_score = gw_entry.get('team_h_score', 0)
                        team_a_score = gw_entry.get('team_a_score', 0)
                        
                        if was_home:
                            result = f"{'W' if team_h_score > team_a_score else 'L' if team_h_score < team_a_score else 'D'} {team_h_score}-{team_a_score}"
                        else:
                            result = f"{'W' if team_a_score > team_h_score else 'L' if team_a_score < team_h_score else 'D'} {team_a_score}-{team_h_score}"
                        
                        # Calculate fantasy points (FPL scoring)
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
                                round_info__in=[f"Gameweek {gw_num}", f"Matchweek {gw_num}", str(gw_num)]
                            ).first
                        )()
                        
                        match_data = {
                            'player_name': player_name,
                            'date': match_date,
                            'round_info': f"Gameweek {gw_num}",
                            'opponent': opponent,
                            'result': result,
                            'minutes_played': minutes,
                            'goals': goals,
                            'assists': assists,
                            'points': points,
                            'saves': saves,
                            'goals_conceded': goals_conceded,
                            'clean_sheet': clean_sheets > 0,
                            'season': season_year,
                            'competition': 'Premier League',
                            'position': player.element_type,  # Position type from FPL
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
                                gw_updated += 1
                            else:
                                gw_skipped += 1
                        else:
                            # Create new match record
                            await sync_to_async(PlayerMatch.objects.create)(**match_data)
                            gw_new += 1
                            
                    except Exception as e:
                        gw_errors += 1
                        if gw_errors <= 3:  # Show first 3 errors per gameweek
                            print(f"   ❌ Error processing {player_name}: {e}")
                
                # Store gameweek statistics
                gameweek_stats[gw_num] = {
                    'new_matches': gw_new,
                    'updated_matches': gw_updated,
                    'skipped_matches': gw_skipped,
                    'errors': gw_errors
                }
                
                total_new_matches += gw_new
                total_updated_matches += gw_updated
                total_skipped_matches += gw_skipped
                total_errors += gw_errors
                
                print(f"   ✅ GW{gw_num}: {gw_new} new, {gw_updated} updated, {gw_skipped} skipped, {gw_errors} errors")
        
        # Calculate duration
        duration = (datetime.now() - start_time).total_seconds()
        
        print(f"\\n🎉 Season Import Complete!")
        print(f"   📊 Total: {total_new_matches} new, {total_updated_matches} updated, {total_skipped_matches} skipped")
        print(f"   ⚠️  Errors: {total_errors}")
        print(f"   ⏱️  Duration: {duration:.2f} seconds")
        
        return {
            'success': True,
            'season': season_year,
            'gameweeks_processed': list(range(start_gw, end_gw + 1)),
            'total_new_matches': total_new_matches,
            'total_updated_matches': total_updated_matches,
            'total_skipped_matches': total_skipped_matches,
            'total_errors': total_errors,
            'duration': duration,
            'gameweek_stats': gameweek_stats
        }
        
    except Exception as e:
        print(f"❌ Season import failed: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            'success': False,
            'error': str(e),
            'season': season_year
        }


async def import_current_season_data() -> Dict[str, Any]:
    """
    Import all available gameweeks for the current season (2025-26)
    
    Returns:
        Dict[str, Any]: Import summary
    """
    return await import_season_gameweeks("2025-26", start_gw=1)


async def import_specific_gameweeks(gameweek_list: List[int], season_year: str = "2025-26") -> Dict[str, Any]:
    """
    Import specific gameweeks for the season
    
    Args:
        gameweek_list: List of gameweek numbers to import
        season_year: Season identifier
    
    Returns:
        Dict[str, Any]: Import summary
    """
    print(f"🎯 Importing specific gameweeks: {gameweek_list}")
    
    results = []
    for gw in gameweek_list:
        result = await import_season_gameweeks(season_year, start_gw=gw, end_gw=gw)
        results.append(result)
    
    # Combine results
    total_new = sum(r.get('total_new_matches', 0) for r in results if r.get('success'))
    total_updated = sum(r.get('total_updated_matches', 0) for r in results if r.get('success'))
    total_skipped = sum(r.get('total_skipped_matches', 0) for r in results if r.get('success'))
    total_errors = sum(r.get('total_errors', 0) for r in results if r.get('success'))
    
    return {
        'success': all(r.get('success', False) for r in results),
        'season': season_year,
        'gameweeks_processed': gameweek_list,
        'total_new_matches': total_new,
        'total_updated_matches': total_updated,
        'total_skipped_matches': total_skipped,
        'total_errors': total_errors,
        'individual_results': results
    }