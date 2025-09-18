"""
Projected Points Calculator

This module calculates projected points for players' next 3 games using the EXACT same
expected points formula as the ELO calculator: E_a = k/(1 + 10**(League_Rating/current_elo))

Key features:
- Uses identical formula to ELO calculator for consistency
- Calculates expected points for next 3 fixtures (FPL API limitation)
- Includes opposition strength multiplier from FPL API
- Stores results in ProjectedPoints model for easy access
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from asgiref.sync import sync_to_async
from django.utils import timezone

logger = logging.getLogger(__name__)


def get_league_rating(competition: str) -> int:
    """
    Get league rating for competition - EXACT same as ELO calculator.
    
    Args:
        competition (str): Competition name
        
    Returns:
        int: League rating value
    """
    if competition == 'Champions League' or competition == 'Champions Lg':
        return 1600
    elif competition in ['Premier League', 'FA Cup', 'Europa League']:
        return 1500
    elif competition in ['Bundesliga', 'La Liga', 'Serie A']:
        return 1300
    elif competition in ['Ligue 1', 'Eredivisie']:
        return 1250
    elif competition in ['Championship', 'Primeira Liga']:
        return 1000
    else:
        return 900


def calculate_expected_points(current_elo: float, competition: str, k: int = 20) -> float:
    """
    Calculate expected points using EXACT same formula as ELO calculator.
    
    Args:
        current_elo (float): Player's current ELO rating
        competition (str): Competition name
        k (int): K-factor (default 20)
        
    Returns:
        float: Expected points
    """
    league_rating = get_league_rating(competition)
    
    # EXACT formula from ELO calculator: E_a = k/(1 + 10**(League_Rating/current_elo))
    expected_points = round(k / (1 + 10**(league_rating / current_elo)), 2)
    
    return expected_points


def apply_opposition_multiplier(expected_points: float, difficulty_rating: int, 
                              opposition_strength: float = 1.0) -> float:
    """
    Apply opposition strength multiplier to expected points.
    
    Args:
        expected_points (float): Base expected points
        difficulty_rating (int): FPL difficulty rating (1-5)
        opposition_strength (float): Opposition strength from FPL API
        
    Returns:
        float: Adjusted expected points
    """
    try:
        # Try to get dynamic multipliers from database
        from MyApi.models import DifficultyMultiplier
        difficulty_multiplier = DifficultyMultiplier.get_multiplier(difficulty_rating)
    except Exception:
        # Fallback to hardcoded multipliers if database access fails
        difficulty_multipliers = {
            1: 3.2,  # Very easy fixture
            2: 2.8,  # Easy fixture
            3: 2.1,  # Average fixture
            4: 1.9,  # Hard fixture
            5: 1.5   # Very hard fixture
        }
        difficulty_multiplier = difficulty_multipliers.get(difficulty_rating, 1.0)
    
    # Combine difficulty and opposition strength
    total_multiplier = difficulty_multiplier * opposition_strength
    
    return round(expected_points * total_multiplier, 2)


async def fetch_fpl_fixtures() -> List[Dict[str, Any]]:
    """
    Fetch upcoming fixtures from FPL API.
    
    Returns:
        List[Dict]: List of fixture data
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('https://fantasy.premierleague.com/api/fixtures/') as response:
                if response.status == 200:
                    fixtures = await response.json()
                    # Filter for upcoming fixtures only
                    upcoming_fixtures = [
                        fixture for fixture in fixtures 
                        if not fixture.get('finished') and fixture.get('event') is not None
                    ]
                    return upcoming_fixtures
                else:
                    logger.error(f"Failed to fetch fixtures: HTTP {response.status}")
                    return []
    except Exception as e:
        logger.error(f"Error fetching FPL fixtures: {e}")
        return []


async def fetch_fpl_teams() -> Dict[int, Dict[str, Any]]:
    """
    Fetch team data from FPL API.
    
    Returns:
        Dict: Team data indexed by team ID
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('https://fantasy.premierleague.com/api/bootstrap-static/') as response:
                if response.status == 200:
                    data = await response.json()
                    teams = {team['id']: team for team in data['teams']}
                    return teams
                else:
                    logger.error(f"Failed to fetch teams: HTTP {response.status}")
                    return {}
    except Exception as e:
        logger.error(f"Error fetching FPL teams: {e}")
        return {}


async def get_player_team_mapping() -> Dict[str, str]:
    """
    Get mapping of player names to their teams.
    
    Returns:
        Dict: Player name -> team name mapping
    """
    try:
        from MyApi.models import Player, SystemSettings
        
        current_week = await sync_to_async(SystemSettings.get_current_gameweek)()
        
        players = await sync_to_async(list)(
            Player.objects.filter(week=current_week).values('name', 'team')
        )
        
        return {player['name']: player['team'] for player in players}
    except Exception as e:
        logger.error(f"Error getting player team mapping: {e}")
        return {}


async def create_player_fixtures(next_gameweeks: int = 3) -> int:
    """
    Create PlayerFixture records for the next N gameweeks.
    
    Args:
        next_gameweeks (int): Number of gameweeks to project (default 3)
        
    Returns:
        int: Number of fixtures created
    """
    try:
        from MyApi.models import PlayerFixture, SystemSettings
        
        # Get current gameweek
        current_gw = await sync_to_async(SystemSettings.get_current_gameweek)()
        
        # Fetch data from FPL API
        fixtures, teams, player_teams = await asyncio.gather(
            fetch_fpl_fixtures(),
            fetch_fpl_teams(),
            get_player_team_mapping()
        )
        
        if not all([fixtures, teams, player_teams]):
            logger.error("Failed to fetch required data for fixture creation")
            return 0
        
        # Create reverse team mapping (team name -> team ID)
        team_name_to_id = {}
        for team_id, team_data in teams.items():
            team_name_to_id[team_data['name']] = team_id
        
        fixtures_created = 0
        target_gameweeks = list(range(current_gw, current_gw + next_gameweeks))
        
        # Filter fixtures for target gameweeks
        relevant_fixtures = [
            fixture for fixture in fixtures 
            if fixture.get('event') in target_gameweeks
        ]
        
        # Create PlayerFixture records
        for player_name, team_name in player_teams.items():
            team_id = team_name_to_id.get(team_name)
            if not team_id:
                continue
                
            for fixture in relevant_fixtures:
                if fixture['team_h'] == team_id or fixture['team_a'] == team_id:
                    is_home = fixture['team_h'] == team_id
                    opponent_id = fixture['team_a'] if is_home else fixture['team_h']
                    opponent_name = teams[opponent_id]['name']
                    
                    # Get fixture difficulty
                    difficulty = fixture['team_h_difficulty'] if is_home else fixture['team_a_difficulty']
                    
                    # Create or update fixture
                    fixture_obj, created = await sync_to_async(PlayerFixture.objects.get_or_create)(
                        player_name=player_name,
                        gameweek=fixture['event'],
                        opponent=opponent_name,
                        defaults={
                            'team': team_name,
                            'is_home': is_home,
                            'fixture_date': datetime.fromisoformat(fixture['kickoff_time'].replace('Z', '+00:00')) if fixture.get('kickoff_time') else None,
                            'difficulty': difficulty
                        }
                    )
                    
                    if created:
                        fixtures_created += 1
        
        logger.info(f"Created {fixtures_created} player fixtures")
        return fixtures_created
        
    except Exception as e:
        logger.error(f"Error creating player fixtures: {e}")
        return 0


async def calculate_projected_points_for_player(player_name: str, override_existing: bool = True) -> int:
    """
    Calculate projected points for a specific player's next 3 games.
    
    Args:
        player_name (str): Name of the player
        override_existing (bool): Whether to override existing projections
        
    Returns:
        int: Number of projections created or updated
    """
    try:
        from MyApi.models import Player, PlayerFixture, ProjectedPoints, SystemSettings
        
        # Get current player data
        current_week = await sync_to_async(SystemSettings.get_current_gameweek)()
        
        try:
            player = await sync_to_async(Player.objects.get)(
                name=player_name, week=current_week
            )
        except Player.DoesNotExist:
            logger.warning(f"Player {player_name} not found for week {current_week}")
            return 0
        
        # Get next 3 fixtures for this player
        fixtures = await sync_to_async(list)(
            PlayerFixture.objects.filter(player_name=player_name)
            .order_by('gameweek')[:3]
        )
        
        if not fixtures:
            logger.warning(f"No fixtures found for {player_name}")
            return 0
        
        projections_created = 0
        
        for fixture in fixtures:
            # Calculate expected points using ELO formula
            expected_points = calculate_expected_points(
                current_elo=player.elo,
                competition=fixture.competition
            )
            
            # Apply opposition multiplier
            adjusted_points = apply_opposition_multiplier(
                expected_points=expected_points,
                difficulty_rating=fixture.difficulty,
                opposition_strength=1.0  # Default for now, can be enhanced later
            )
            
            # Create or update projection
            if override_existing:
                # Delete existing projection if it exists
                await sync_to_async(ProjectedPoints.objects.filter(
                    player_name=player_name,
                    gameweek=fixture.gameweek,
                    opponent=fixture.opponent
                ).delete)()
                
                # Create new projection
                projection = await sync_to_async(ProjectedPoints.objects.create)(
                    player_name=player_name,
                    gameweek=fixture.gameweek,
                    opponent=fixture.opponent,
                    is_home=fixture.is_home,
                    current_elo=player.elo,
                    current_cost=player.cost,
                    competition=fixture.competition,
                    league_rating=get_league_rating(fixture.competition),
                    expected_points=expected_points,
                    opposition_strength=1.0,
                    difficulty_rating=fixture.difficulty,
                    adjusted_expected_points=adjusted_points,
                    k_factor=20
                )
                projections_created += 1
                
            else:
                # Use get_or_create to avoid duplicates
                projection, created = await sync_to_async(ProjectedPoints.objects.get_or_create)(
                    player_name=player_name,
                    gameweek=fixture.gameweek,
                    opponent=fixture.opponent,
                    defaults={
                        'is_home': fixture.is_home,
                        'current_elo': player.elo,
                        'current_cost': player.cost,
                        'competition': fixture.competition,
                        'league_rating': get_league_rating(fixture.competition),
                        'expected_points': expected_points,
                        'opposition_strength': 1.0,
                        'difficulty_rating': fixture.difficulty,
                        'adjusted_expected_points': adjusted_points,
                        'k_factor': 20
                    }
                )
                
                if created:
                    projections_created += 1
        
        return projections_created
        
    except Exception as e:
        logger.error(f"Error calculating projected points for {player_name}: {e}")
        return 0


async def calculate_all_projected_points(override_existing: bool = True) -> Dict[str, Any]:
    """
    Calculate projected points for all players.
    
    Args:
        override_existing (bool): Whether to override existing projections
    
    Returns:
        Dict: Summary of calculations
    """
    try:
        from MyApi.models import Player, SystemSettings
        
        # First, create fixtures for next 3 gameweeks
        logger.info("Creating player fixtures...")
        fixtures_created = await create_player_fixtures(next_gameweeks=3)
        
        # Get all current players
        current_week = await sync_to_async(SystemSettings.get_current_gameweek)()
        players = await sync_to_async(list)(
            Player.objects.filter(week=current_week).values_list('name', flat=True)
        )
        
        logger.info(f"Calculating projected points for {len(players)} players...")
        
        total_projections = 0
        successful_players = 0
        failed_players = 0
        
        # Process players in batches to avoid overwhelming the system
        batch_size = 50
        for i in range(0, len(players), batch_size):
            batch = players[i:i + batch_size]
            
            for player_name in batch:
                try:
                    projections = await calculate_projected_points_for_player(player_name, override_existing)
                    total_projections += projections
                    if projections > 0:
                        successful_players += 1
                    else:
                        failed_players += 1
                except Exception as e:
                    logger.error(f"Failed to calculate projections for {player_name}: {e}")
                    failed_players += 1
            
            # Small delay between batches
            await asyncio.sleep(0.1)
        
        result = {
            'success': True,
            'fixtures_created': fixtures_created,
            'total_projections': total_projections,
            'successful_players': successful_players,
            'failed_players': failed_players,
            'total_players': len(players)
        }
        
        logger.info(f"Projected points calculation complete: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error in calculate_all_projected_points: {e}")
        return {
            'success': False,
            'error': str(e),
            'fixtures_created': 0,
            'total_projections': 0,
            'successful_players': 0,
            'failed_players': 0,
            'total_players': 0
        }


async def get_player_projected_summary(player_name: str) -> Dict[str, Any]:
    """
    Get projected points summary for a specific player.
    
    Args:
        player_name (str): Name of the player
        
    Returns:
        Dict: Summary of projected points
    """
    try:
        from MyApi.models import ProjectedPoints
        
        projections = await sync_to_async(list)(
            ProjectedPoints.objects.filter(player_name=player_name)
            .order_by('gameweek')[:3]
        )
        
        if not projections:
            return {
                'player_name': player_name,
                'total_projected_points': 0,
                'games_projected': 0,
                'projections': []
            }
        
        total_points = sum(proj.adjusted_expected_points for proj in projections)
        
        projection_details = []
        for proj in projections:
            projection_details.append({
                'gameweek': proj.gameweek,
                'opponent': proj.opponent,
                'is_home': proj.is_home,
                'expected_points': proj.expected_points,
                'adjusted_points': proj.adjusted_expected_points,
                'difficulty': proj.difficulty_rating
            })
        
        return {
            'player_name': player_name,
            'total_projected_points': round(total_points, 2),
            'games_projected': len(projections),
            'projections': projection_details
        }
        
    except Exception as e:
        logger.error(f"Error getting projected summary for {player_name}: {e}")
        return {
            'player_name': player_name,
            'total_projected_points': 0,
            'games_projected': 0,
            'projections': [],
            'error': str(e)
        }
