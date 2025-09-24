from MyApi.models import ProjectedPoints, PlayerFixture, Player

# Example ELO-based expected points calculation (replace with your actual formula)
def calculate_expected_points(current_elo, competition, k=20):
    # Example: k / (1 + 10**(league_rating / current_elo))
    league_rating = get_league_rating(competition)
    return k / (1 + 10 ** (league_rating / current_elo)) if current_elo > 0 else 0.0

# Example: get league rating (replace with your actual logic)
def get_league_rating(competition):
    # Example: Premier League = 1500, Champions League = 1600, etc.
    if competition == 'Champions League':
        return 1600
    return 1500

# Example: apply opposition multiplier (replace with your actual logic)
def apply_opposition_multiplier(expected_points, difficulty_rating, opposition_strength=1.0):
    # Example: harder fixtures reduce points
    return expected_points * (1.0 - 0.1 * (difficulty_rating - 3)) * opposition_strength

async def calculate_and_store_projected_points(override_existing=True):
    from asgiref.sync import sync_to_async
    projections_created = 0
    skipped_fixtures = 0
    # Delete all ProjectedPoints records (full refresh)
    await sync_to_async(ProjectedPoints.objects.all().delete)()
    # Get all future PlayerFixtures
    fixtures = await sync_to_async(list)(PlayerFixture.objects.all())
    for fixture in fixtures:
        try:
            # Try to get the player, skip if not found
            player = await sync_to_async(Player.objects.filter(name=fixture.player_name).first)()
            if not player:
                print(f"[WARN] No Player found for fixture: {fixture.player_name} GW{fixture.gameweek}")
                skipped_fixtures += 1
                continue
            expected_points = calculate_expected_points(
                current_elo=player.elo,
                competition=getattr(fixture, 'competition', 'Premier League')
            )
            adjusted_points = apply_opposition_multiplier(
                expected_points=expected_points,
                difficulty_rating=fixture.difficulty,
                opposition_strength=1.0
            )
            if override_existing:
                await sync_to_async(ProjectedPoints.objects.filter(
                    player_name=fixture.player_name,
                    gameweek=fixture.gameweek,
                    opponent=fixture.opponent
                ).delete)()
                await sync_to_async(ProjectedPoints.objects.create)(
                    player_name=fixture.player_name,
                    gameweek=fixture.gameweek,
                    opponent=fixture.opponent,
                    is_home=fixture.is_home,
                    current_elo=player.elo,
                    current_cost=player.cost,
                    competition=getattr(fixture, 'competition', 'Premier League'),
                    league_rating=get_league_rating(getattr(fixture, 'competition', 'Premier League')),
                    expected_points=expected_points,
                    opposition_strength=1.0,
                    difficulty_rating=fixture.difficulty,
                    adjusted_expected_points=adjusted_points,
                    k_factor=20
                )
                projections_created += 1
            else:
                _, created = await sync_to_async(ProjectedPoints.objects.get_or_create)(
                    player_name=fixture.player_name,
                    gameweek=fixture.gameweek,
                    opponent=fixture.opponent,
                    defaults={
                        'is_home': fixture.is_home,
                        'current_elo': player.elo,
                        'current_cost': player.cost,
                        'competition': getattr(fixture, 'competition', 'Premier League'),
                        'league_rating': get_league_rating(getattr(fixture, 'competition', 'Premier League')),
                        'expected_points': expected_points,
                        'opposition_strength': 1.0,
                        'difficulty_rating': fixture.difficulty,
                        'adjusted_expected_points': adjusted_points,
                        'k_factor': 20
                    }
                )
                if created:
                    projections_created += 1
        except Exception as e:
            print(f"[ERROR] Projected points for {fixture.player_name} GW{fixture.gameweek}: {e}")
            skipped_fixtures += 1
    print(f"[DEBUG] Created/updated {projections_created} ProjectedPoints records. Skipped {skipped_fixtures} fixtures.")
import asyncio
import aiohttp
from datetime import datetime

async def refresh_fixtures_util(next_gameweeks=3) -> dict:
    """
    Update all player fixtures and return a summary dict.
    """
    from MyApi.models import Player, SystemSettings
    try:
        # Update fixtures for all players
        await update_player_fixtures(next_gameweeks=next_gameweeks)
        # Get all current players
        current_week = await sync_to_async(SystemSettings.get_current_gameweek)()
        players = await sync_to_async(list)(
            Player.objects.filter(week=current_week).values_list('name', flat=True)
        )
        result = {
            'success': True,
            'total_players': len(players),
            'successful_players': len(players),
            'failed_players': 0,
            'total_projections': 0,
            'fixtures_created': len(players)*next_gameweeks
        }
        print(f"Projected points calculation complete: {result}")
        return result
    except Exception as e:
        print(f"Error in calculate_all_projected_points: {e}")
        return {
            'success': False,
            'error': str(e),
            'total_players': 0,
            'successful_players': 0,
            'failed_players': 0,
            'total_projections': 0
        }

from asgiref.sync import sync_to_async

async def fetch_fpl_fixtures():
    async with aiohttp.ClientSession() as session:
        async with session.get('https://fantasy.premierleague.com/api/fixtures/') as response:
            if response.status == 200:
                return await response.json()
            return []


async def update_player_fixtures(next_gameweeks=3):
    from MyApi.models import Player, PlayerFixture, SystemSettings, Team

    # Delete all existing PlayerFixture records
    await sync_to_async(PlayerFixture.objects.all().delete)()

    # Get current gameweek
    current_gw = await sync_to_async(SystemSettings.get_current_gameweek)()
    # Fetch FPL data
    fixtures = await fetch_fpl_fixtures()
    team_id_to_name = {t.fpl_team_id: t.name for t in await sync_to_async(list)(Team.objects.all())}
    # Get all player names and their teams in our DB for the current week
    db_players = await sync_to_async(list)(Player.objects.filter(week=current_gw).values('name', 'team'))
    print(f"[DEBUG] Found {len(db_players)} players for week {current_gw}")
    team_name_to_id = {t.name.lower(): t.fpl_team_id for t in await sync_to_async(list)(Team.objects.all())}
    fixtures_to_create = []
    skipped_players = []
    for player in db_players:
        db_name = player['name']
        db_team = player['team']
        # Map friendly name to FPL team_id using Teams table
        team_id = team_name_to_id.get((db_team or '').lower())
        if not team_id:
            print(f"[DEBUG] No FPL team id for player {db_name} (team: {db_team})")
            skipped_players.append(db_name)
            continue
        # Find next N fixtures for this team (future fixtures only)
        player_fixtures = [
            f for f in fixtures
            if (f['team_h'] == team_id or f['team_a'] == team_id)
            and f.get('event', 0) > current_gw
        ]
        player_fixtures = sorted(player_fixtures, key=lambda x: x['event'])[:next_gameweeks]
        for fixture in player_fixtures:
            is_home = fixture['team_h'] == team_id
            opponent_id = fixture['team_a'] if is_home else fixture['team_h']
            difficulty = fixture['team_h_difficulty'] if is_home else fixture['team_a_difficulty']
            fixtures_to_create.append(PlayerFixture(
                player_name=db_name,
                team=team_id,  # Store FPL team_id for player's team
                gameweek=fixture['event'],
                opponent=opponent_id,  # Store FPL team_id for opponent
                is_home=is_home,
                fixture_date=datetime.fromisoformat(fixture['kickoff_time'].replace('Z', '+00:00')) if fixture.get('kickoff_time') else None,
                difficulty=difficulty
            ))
    print(f"[DEBUG] Prepared {len(fixtures_to_create)} PlayerFixture records to create.")
    if skipped_players:
        print(f"[DEBUG] Skipped {len(skipped_players)} players due to missing/mismatched team: {skipped_players}")
    await sync_to_async(PlayerFixture.objects.bulk_create)(fixtures_to_create)
    print(f"Created {len(fixtures_to_create)} player fixtures.")


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
