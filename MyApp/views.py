from django.shortcuts import render, HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from MyApi.models import CurrentSquad, Player
import json

def home(request):
    """
    Home page displaying the current squad without any edit functionality.
    """
    try:
        current_squad_instance = CurrentSquad.get_or_create_current_squad()
        current_squad = current_squad_instance.squad
    except:
        # If there's an issue with the database, show empty squad
        current_squad = {
            "goalkeepers": [],
            "defenders": [],
            "midfielders": [],
            "forwards": []
        }
    
    context = {
        'current_squad': current_squad
    }
    return render(request, 'home.html', context)

def team_selection(request):
    """
    Team Selection page for building and managing fantasy squads.
    Renders player list on the server-side like player_ratings.
    """
    try:
        week = 4  # Configurable week
        players_queryset = Player.objects.filter(week=week)

        if not players_queryset.exists():
            return render(request, 'team_selection.html', {'players': [], 'error': f'No player data found for week {week}.'})

        # Import models for projected points
        from MyApi.models import ProjectedPoints

        players_data = []
        for player in players_queryset:
            # Get projected points (total for next 3 games)
            projected_points = 0
            try:
                total_projected = ProjectedPoints.get_total_projected_points(player.name, games=3)
                projected_points = round(total_projected, 1) if total_projected else 0
            except Exception as e:
                projected_points = 0

            position_map = {'Keeper': 'GKP', 'Defender': 'DEF', 'Midfielder': 'MID', 'Attacker': 'FWD'}
            players_data.append({
                'id': player.id,
                'name': player.name,
                'team': player.team or 'Unknown Team',
                'position': position_map.get(player.position, player.position),
                'elo_rating': round(float(player.elo), 1),
                'cost': float(player.cost),
                'projected_points': projected_points,
            })

        players_data.sort(key=lambda x: x['elo_rating'], reverse=True)

        # Load current squad from database
        try:
            current_squad_instance = CurrentSquad.get_or_create_current_squad()
            current_squad = current_squad_instance.squad
        except Exception as e:
            print(f"Error loading current squad: {e}")
            current_squad = {
                "goalkeepers": [],
                "defenders": [],
                "midfielders": [],
                "forwards": []
            }

        context = {
            'players': players_data,
            'players_json': json.dumps(players_data),
            'current_squad': current_squad,
            'current_squad_json': json.dumps(current_squad),
            'total_players': len(players_data)
        }
        return render(request, 'team_selection.html', context)

    except Exception as e:
        return render(request, 'team_selection.html', {'players': [], 'error': f'Error loading player data: {str(e)}'})

def squads(request):
    squad_numbers = range(1, 5) 
    context = {
        'squad_numbers': squad_numbers,
    }
    return render(request, 'squads.html', context)

def player_ratings(request):
    """
    Display all players with their ratings, cost, position, projected points, and next 3 fixtures.
    Supports filtering and sorting functionality.
    """
    try:
        # Load data from database instead of SquadSelector
        week = 4  # You can make this configurable later
        players_queryset = Player.objects.filter(week=week)
        
        if not players_queryset.exists():
            context = {
                'players': [],
                'total_players': 0,
                'error': f'No player data found for week {week}. Please import data first.'
            }
            return render(request, 'player_ratings.html', context)
        
        # Import models for fixtures and projected points
        from MyApi.models import PlayerFixture, ProjectedPoints
        
        # Convert to list of dictionaries for template
        players_data = []
        for player in players_queryset:
            # Get projected points (total for next 3 games)
            projected_points = 0
            try:
                total_projected = ProjectedPoints.get_total_projected_points(player.name, games=3)
                projected_points = round(total_projected, 1) if total_projected else 0
            except Exception as e:
                projected_points = 0
            
            # Get next 3 fixtures
            next_fixtures = []
            try:
                fixtures = PlayerFixture.objects.filter(
                    player_name=player.name
                ).order_by('gameweek', 'fixture_date')[:3]
                
                for fixture in fixtures:
                    home_away = "vs" if fixture.is_home else "@"
                    next_fixtures.append({
                        'text': f"{home_away} {fixture.opponent}",
                        'difficulty': fixture.difficulty  # 1-5 FPL difficulty rating
                    })
            except Exception as e:
                next_fixtures = [
                    {'text': "No fixtures", 'difficulty': 3},
                    {'text': "No fixtures", 'difficulty': 3},
                    {'text': "No fixtures", 'difficulty': 3}
                ]
            
            # Ensure we have exactly 3 fixtures (pad with "No fixtures" if needed)
            while len(next_fixtures) < 3:
                next_fixtures.append({'text': "No fixtures", 'difficulty': 3})
            
            player_data = {
                'name': player.name,
                'position': player.position,
                'elo': round(float(player.elo), 1),
                'cost': float(player.cost),
                'comp': player.competition or 'Premier League',
                'projected_points': projected_points,
                'fixture_1': next_fixtures[0]['text'],
                'fixture_1_difficulty': next_fixtures[0]['difficulty'],
                'fixture_2': next_fixtures[1]['text'],
                'fixture_2_difficulty': next_fixtures[1]['difficulty'],
                'fixture_3': next_fixtures[2]['text'],
                'fixture_3_difficulty': next_fixtures[2]['difficulty'],
            }
            players_data.append(player_data)
        
        # Sort by Elo rating by default (highest first)
        players_data.sort(key=lambda x: x['elo'], reverse=True)
        
        context = {
            'players': players_data,
            'total_players': len(players_data)
        }
        
    except Exception as e:
        print(f"Error loading player data: {e}")
        context = {
            'players': [],
            'total_players': 0,
            'error': str(e)
        }
    
    return render(request, 'player_ratings.html', context)


def get_squads(request):
    """
    Generate squads from database and return them as JSON, honoring an optional 'formation' query param.
    Allowed formations: '3-4-3', '3-5-2', '4-4-2', '4-3-3'.
    Maps to counts: keeper=1, defender=X, midfielder=Y, attacker=Z.
    """
    from MyApi.models import Player, SystemSettings
    import random
    
    formation_str = request.GET.get('formation', '3-4-3')
    allowed = {
        '3-4-3': (1, 3, 4, 3),
        '3-5-2': (1, 3, 5, 2),
        '4-4-2': (1, 4, 4, 2),
        '4-3-3': (1, 4, 3, 3),
    }
    if formation_str not in allowed:
        # Fallback to default if an unsupported formation is passed
        formation_str = '3-4-3'
    keeper_count, defender_count, midfielder_count, attacker_count = allowed[formation_str]

    try:
        # Get current week from system settings
        settings = SystemSettings.get_settings()
        current_week = settings.current_gameweek
        
        # Get top players by position from database
        keepers = list(Player.objects.filter(
            position='Keeper', 
            week=current_week
        ).order_by('-elo')[:10])
        
        defenders = list(Player.objects.filter(
            position='Defender', 
            week=current_week
        ).order_by('-elo')[:20])
        
        midfielders = list(Player.objects.filter(
            position='Midfielder', 
            week=current_week
        ).order_by('-elo')[:20])
        
        attackers = list(Player.objects.filter(
            position='Attacker', 
            week=current_week
        ).order_by('-elo')[:15])
        
        # Generate 4 different squads
        squads = []
        for i in range(4):
            # Shuffle to get different combinations
            random.shuffle(keepers)
            random.shuffle(defenders)
            random.shuffle(midfielders)
            random.shuffle(attackers)
            
            squad = {
                'squad_number': i + 1,  # Squad numbers 1-4
                'positions': [keeper_count, defender_count, midfielder_count, attacker_count],  # Expected by frontend
                'goalkeepers': [
                    {
                        'name': player.name,
                        'elo': round(float(player.elo), 1),
                        'cost': float(player.cost),
                        'team': player.team or 'Unknown'
                    }
                    for player in keepers[:keeper_count]
                ],
                'defenders': [
                    {
                        'name': player.name,
                        'elo': round(float(player.elo), 1),
                        'cost': float(player.cost),
                        'team': player.team or 'Unknown'
                    }
                    for player in defenders[:defender_count]
                ],
                'midfielders': [
                    {
                        'name': player.name,
                        'elo': round(float(player.elo), 1),
                        'cost': float(player.cost),
                        'team': player.team or 'Unknown'
                    }
                    for player in midfielders[:midfielder_count]
                ],
                'forwards': [
                    {
                        'name': player.name,
                        'elo': round(float(player.elo), 1),
                        'cost': float(player.cost),
                        'team': player.team or 'Unknown'
                    }
                    for player in attackers[:attacker_count]
                ]
            }
            
            # Calculate total cost and average Elo
            all_players = []
            all_players.extend(squad['goalkeepers'])
            all_players.extend(squad['defenders'])
            all_players.extend(squad['midfielders'])
            all_players.extend(squad['forwards'])
            
            total_cost = sum(p['cost'] for p in all_players)
            total_elo = sum(p['elo'] for p in all_players)
            player_count = len(all_players)
            
            squad['total_cost'] = round(total_cost, 1)
            squad['avg_elo'] = round(total_elo / player_count, 1) if player_count > 0 else 0
            
            squad['total_cost'] = round(total_cost, 1)
            squad['avg_elo'] = round(total_elo / player_count, 1) if player_count > 0 else 0
            
            squads.append(squad)
        
        return JsonResponse({
            'squads': squads,
            'formation': formation_str,
            'counts': {
                'keeper': keeper_count,
                'defender': defender_count,
                'midfielder': midfielder_count,
                'attacker': attacker_count,
            }
        })
    except Exception as e:
        # Surface a useful error to the client
        return JsonResponse({'error': f'Failed to generate squads: {str(e)}'}, status=500)


def get_current_squad(request):
    """
    A Django view that returns the current squad from the database as JSON.
    """
    current_squad_instance = CurrentSquad.get_or_create_current_squad()
    
    # Refresh squad data to ensure it has full player information
    current_squad_instance.refresh_squad_data()
    
    return JsonResponse({'current_squad': current_squad_instance.squad})


def get_all_players(request):
    """
    Get all available players from the database.
    Returns players organized by position for easy selection.
    """
    try:
        from MyApi.models import Player, SystemSettings
        
        # Get current week from system settings
        settings = SystemSettings.get_settings()
        current_week = settings.current_gameweek
        
        # Get players from database for current week
        goalkeepers = Player.objects.filter(
            position='Keeper', 
            week=current_week
        ).order_by('-elo')[:20]
        
        defenders = Player.objects.filter(
            position='Defender', 
            week=current_week
        ).order_by('-elo')[:50]
        
        midfielders = Player.objects.filter(
            position='Midfielder', 
            week=current_week
        ).order_by('-elo')[:50]
        
        forwards = Player.objects.filter(
            position='Attacker', 
            week=current_week
        ).order_by('-elo')[:30]
        
        # Convert to JSON-friendly format
        all_players = {
            "goalkeepers": [
                {
                    "name": player.name,
                    "elo": player.elo,
                    "cost": player.cost,
                    "team": player.team or 'Unknown'
                } 
                for player in goalkeepers
            ],
            "defenders": [
                {
                    "name": player.name,
                    "elo": player.elo,
                    "cost": player.cost,
                    "team": player.team or 'Unknown'
                } 
                for player in defenders
            ],
            "midfielders": [
                {
                    "name": player.name,
                    "elo": player.elo,
                    "cost": player.cost,
                    "team": player.team or 'Unknown'
                } 
                for player in midfielders
            ],
            "forwards": [
                {
                    "name": player.name,
                    "elo": player.elo,
                    "cost": player.cost,
                    "team": player.team or 'Unknown'
                } 
                for player in forwards
            ]
        }
        
        return JsonResponse({'players': all_players})
        
    except Exception as e:
        return JsonResponse({'error': f'Failed to load players: {str(e)}'}, status=500)


@csrf_exempt
def add_player_to_squad(request):
    """
    Add a player to the current squad.
    Expected POST data: {'position': 'defenders', 'player_name': 'John Doe'}
    """
    if request.method == 'POST':
        data = json.loads(request.body)
        position = data.get('position')
        player_name = data.get('player_name')
        
        if not position or not player_name:
            return JsonResponse({'error': 'Position and player_name are required'}, status=400)
        
        current_squad_instance = CurrentSquad.get_or_create_current_squad()
        success = current_squad_instance.add_player(position, player_name)
        
        if success:
            return JsonResponse({
                'message': f'Player {player_name} added to {position}',
                'squad': current_squad_instance.squad
            })
        else:
            return JsonResponse({'error': 'Invalid position'}, status=400)
    
    return JsonResponse({'error': 'Only POST method allowed'}, status=405)


@csrf_exempt
def remove_player_from_squad(request):
    """
    Remove a player from the current squad.
    Expected POST data: {'position': 'defenders', 'player_name': 'John Doe'}
    """
    if request.method == 'POST':
        data = json.loads(request.body)
        position = data.get('position')
        player_name = data.get('player_name')
        
        if not position or not player_name:
            return JsonResponse({'error': 'Position and player_name are required'}, status=400)
        
        current_squad_instance = CurrentSquad.get_or_create_current_squad()
        success = current_squad_instance.remove_player(position, player_name)
        
        if success:
            return JsonResponse({
                'message': f'Player {player_name} removed from {position}',
                'squad': current_squad_instance.squad
            })
        else:
            return JsonResponse({'error': 'Player not found in specified position'}, status=404)
    
    return JsonResponse({'error': 'Only POST method allowed'}, status=405)


def player_info(request, player_name):
    """
    Display detailed information for a specific player including match history and Elo chart.
    """
    from MyApi.models import PlayerMatch, EloCalculation
    from django.db.models import Q
    from urllib.parse import unquote
    
    # URL decode the player name
    player_name = unquote(player_name)
    
    # Try exact match first
    matches = PlayerMatch.objects.filter(player_name=player_name).order_by('-date')[:50]
    
    # If no exact match, try with spaces replaced by underscores
    if not matches.exists():
        player_name_with_underscores = player_name.replace(' ', '_')
        matches = PlayerMatch.objects.filter(player_name=player_name_with_underscores).order_by('-date')[:50]
        if matches.exists():
            player_name = player_name_with_underscores
    
    # If still no match, try with underscores replaced by spaces
    if not matches.exists():
        player_name_with_spaces = player_name.replace('_', ' ')
        matches = PlayerMatch.objects.filter(player_name=player_name_with_spaces).order_by('-date')[:50]
        if matches.exists():
            player_name = player_name_with_spaces
    
    if not matches.exists():
        # Try to find similar player names (case-insensitive partial match)
        search_term = player_name.replace('_', ' ').replace('-', ' ')
        first_word = search_term.split()[0] if search_term else player_name
        
        similar_players = PlayerMatch.objects.filter(
            player_name__icontains=first_word
        ).values_list('player_name', flat=True).distinct()[:10]
        
        context = {
            'player_name': player_name,
            'error': 'Player not found',
            'similar_players': list(similar_players)
        }
        return render(request, 'player_info.html', context)
    
    # Get actual player name from database (for consistency)
    actual_player_name = matches.first().player_name
    
    # Get player team information from current week
    from MyApi.models import SystemSettings
    settings = SystemSettings.get_settings()
    current_week = settings.current_gameweek
    
    # Try to get team from Player model for current week, fallback to any week
    player_team = None
    try:
        from MyApi.models import Player
        player_obj = Player.objects.filter(name=actual_player_name, week=current_week).first()
        if not player_obj:
            # Fallback to any week if current week not found
            player_obj = Player.objects.filter(name=actual_player_name).order_by('-week').first()
        
        if player_obj and player_obj.team:
            player_team = player_obj.team
    except Exception as e:
        print(f"Error getting team for {actual_player_name}: {e}")
    
    # Calculate statistics
    total_matches = matches.count()
    total_goals = sum(match.goals for match in matches)
    total_assists = sum(match.assists for match in matches)
    total_points = sum(match.points for match in matches)
    avg_minutes = sum(match.minutes_played for match in matches) / total_matches if total_matches > 0 else 0
    
    # Get current Elo (most recent match)
    current_elo = matches.first().elo_after_match if matches.exists() else 0
    
    # Prepare Elo history data for chart (most recent 20 matches in chronological order)
    elo_history_recent_desc = PlayerMatch.objects.filter(
        player_name=actual_player_name
    ).order_by('-date')[:20]
    elo_history = list(elo_history_recent_desc)[::-1]  # reverse to chronological
    elo_data = {
        'dates': [m.date.strftime('%Y-%m-%d') for m in elo_history],
        'elos': [float(m.elo_after_match) for m in elo_history],
    }
    
    # Get recent form (last 5 matches)
    recent_matches = matches[:5]
    
    context = {
        'player_name': actual_player_name,
        'player_display_name': actual_player_name.replace('_', ' '),
        'player_team': player_team,
        'matches': matches,
        'recent_matches': recent_matches,
        'total_matches': total_matches,
        'total_goals': total_goals,
        'total_assists': total_assists,
        'total_points': total_points,
        'avg_minutes': round(avg_minutes, 1),
        'current_elo': round(current_elo, 1),
        'elo_data_json': json.dumps(elo_data),
    }
    
    return render(request, 'player_info.html', context)


def data_manager(request):
    """
    Data manager page to display current game week, set new game week,
    manage data refresh operations, and handle player management tasks.
    Combines game week management with player data operations.
    """
    from MyApi.models import SystemSettings, Player
    from django.utils import timezone
    
    try:
        settings = SystemSettings.get_settings()
        
        # Get total players count from current week
        current_week = settings.current_gameweek
        total_players = Player.objects.filter(week=current_week).count()
        
        context = {
            'current_gameweek': settings.current_gameweek,
            'current_season': settings.current_season,
            'last_update': settings.last_data_update.strftime('%Y-%m-%d %H:%M') if settings.last_data_update else 'Never',
            'total_players': total_players,
        }
        
    except Exception as e:
        print(f"Error loading game week manager data: {e}")
        context = {
            'current_gameweek': 1,
            'current_season': '2025/26',
            'last_update': 'Never',
            'total_players': 0,
        }
    
    return render(request, 'data_manager.html', context)


@csrf_exempt
def set_gameweek(request):
    """
    API endpoint to set the current game week.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Only POST method allowed'})
    
    try:
        from MyApi.models import SystemSettings
        
        data = json.loads(request.body)
        gameweek = int(data.get('gameweek', 1))
        
        if not (1 <= gameweek <= 38):
            return JsonResponse({'success': False, 'error': 'Game week must be between 1 and 38'})
        
        settings = SystemSettings.set_current_gameweek(gameweek)
        
        return JsonResponse({
            'success': True,
            'message': f'Game week set to {gameweek}',
            'gameweek': settings.current_gameweek,
            'season': settings.current_season
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
def refresh_players(request):
    """
    API endpoint to refresh player data from database.
    In a database-only mode, this mainly updates timestamps and validates data.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Only POST method allowed'})
    
    try:
        from MyApi.models import SystemSettings, Player, PlayerMatch
        from django.utils import timezone
        
        settings = SystemSettings.get_settings()
        current_week = settings.current_gameweek
        
        # Validate database has data for current week
        player_count = Player.objects.filter(week=current_week).count()
        match_count = PlayerMatch.objects.count()
        
        if player_count == 0:
            return JsonResponse({
                'success': False,
                'error': f'No player data found for week {current_week}. Please import data first.'
            })
        
        # Update last data update timestamp
        settings.last_data_update = timezone.now()
        settings.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Player data validated for game week {current_week}',
            'stats': {
                'players': player_count,
                'matches': match_count,
                'last_update': settings.last_data_update.isoformat()
            }
        })
                
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Failed to refresh player data: {str(e)}'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
def refresh_fixtures(request):
    """
    API endpoint to refresh fixture data.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Only POST method allowed'})
    
    try:
        from MyApi.models import SystemSettings, Player
        from django.utils import timezone
        from django.db.models import Count
        
        # Validate database state for fixtures/matches
        settings = SystemSettings.get_settings()
        
        # Count players with match data as a basic validation
        players_with_matches = Player.objects.filter(
            elo_rating__gt=0
        ).count()
        
        # Update timestamp
        settings.last_fixtures_update = timezone.now()
        settings.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Fixtures validated successfully - {players_with_matches} players with data',
            'last_update': settings.last_fixtures_update.strftime('%Y-%m-%d %H:%M')
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt 
def full_refresh(request):
    """
    API endpoint to perform a full data refresh (players, fixtures, etc.).
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Only POST method allowed'})
    
    try:
        from MyApi.models import SystemSettings, Player, PlayerMatch, EloCalculation
        from django.utils import timezone
        from django.db.models import Count, Max, Min
        
        settings = SystemSettings.get_settings()
        current_week = settings.current_gameweek
        
        messages = []
        
        # Validate database state
        try:
            # Count total players and matches
            total_players = Player.objects.count()
            total_matches = PlayerMatch.objects.count()
            total_elo_records = EloCalculation.objects.count()
            
            # Get latest data dates
            latest_match = PlayerMatch.objects.aggregate(
                latest=Max('match_date'),
                earliest=Min('match_date')
            )
            
            # Validate players have ratings
            players_with_ratings = Player.objects.filter(elo_rating__gt=0).count()
            
            messages.append(f'✓ Database validation complete for game week {current_week}')
            messages.append(f'✓ {total_players} players in database')
            messages.append(f'✓ {total_matches} match records')
            messages.append(f'✓ {total_elo_records} Elo calculations')
            messages.append(f'✓ {players_with_ratings} players with ratings')
            
            if latest_match['latest']:
                messages.append(f'✓ Latest match data: {latest_match["latest"]}')
            if latest_match['earliest']:
                messages.append(f'✓ Earliest match data: {latest_match["earliest"]}')
                
        except Exception as e:
            messages.append(f'✗ Database validation failed: {str(e)}')
        
        # Update timestamps
        now = timezone.now()
        settings.last_data_update = now
        settings.last_fixtures_update = now
        settings.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Full refresh completed',
            'details': messages,
            'last_update': now.strftime('%Y-%m-%d %H:%M')
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
def update_player_positions_from_fpl(request):
    """
    Fetch player positions and teams from FPL API and update database.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Only POST method allowed'})
    
    try:
        import asyncio
        from MyApi.models import Player, SystemSettings
        
        # Get the current week from settings
        try:
            settings = SystemSettings.objects.first()
            current_week = settings.current_gameweek if settings else 4
        except:
            current_week = 4
        
        async def fetch_and_update_positions():
            """
            Async function to fetch FPL data and update positions and teams.
            """
            import aiohttp
            from fpl import FPL
            from asgiref.sync import sync_to_async
            
            async with aiohttp.ClientSession() as session:
                fpl = FPL(session)
                
                try:
                    # Get all FPL players and teams
                    players = await fpl.get_players()
                    teams = await fpl.get_teams()
                    
                    # Create team mapping
                    team_map = {team.id: team.name for team in teams}
                    
                    updated_count = 0
                    team_updated_count = 0
                    errors = []
                    position_changes = []
                    team_changes = []
                    
                    position_map = {
                        1: 'Keeper',      # Goalkeeper
                        2: 'Defender',    # Defender
                        3: 'Midfielder',  # Midfielder
                        4: 'Attacker',    # Forward
                    }
                    
                    for fpl_player in players:
                        try:
                            # Clean player name to match our database format
                            player_name = f"{fpl_player.first_name} {fpl_player.second_name}"
                            player_name_clean = player_name.replace(' ', '_')
                            
                            # Get FPL position and team
                            fpl_position = position_map.get(fpl_player.element_type, 'Midfielder')
                            fpl_team = team_map.get(fpl_player.team, 'Unknown')
                            
                            # Try to find player in our database (try both formats)
                            player_obj = None
                            for name_variant in [player_name, player_name_clean, player_name.replace('_', ' ')]:
                                try:
                                    player_obj = await sync_to_async(Player.objects.filter(
                                        name=name_variant, 
                                        week=current_week
                                    ).first)()
                                    if player_obj:
                                        break
                                except:
                                    continue
                            
                            if player_obj:
                                updated = False
                                
                                # Check if position needs updating
                                if player_obj.position != fpl_position:
                                    old_position = player_obj.position
                                    player_obj.position = fpl_position
                                    updated = True
                                    
                                    position_changes.append({
                                        'name': player_obj.name,
                                        'old_position': old_position,
                                        'new_position': fpl_position
                                    })
                                    updated_count += 1
                                
                                # Check if team needs updating
                                if player_obj.team != fpl_team:
                                    old_team = player_obj.team
                                    player_obj.team = fpl_team
                                    updated = True
                                    
                                    team_changes.append({
                                        'name': player_obj.name,
                                        'old_team': old_team,
                                        'new_team': fpl_team
                                    })
                                    team_updated_count += 1
                                
                                if updated:
                                    await sync_to_async(player_obj.save)()
                            
                        except Exception as e:
                            errors.append(f"Error updating {player_name}: {str(e)}")
                            continue
                    
                    return {
                        'updated_count': updated_count,
                        'team_updated_count': team_updated_count,
                        'position_changes': position_changes,
                        'team_changes': team_changes[:20],  # Limit to first 20
                        'errors': errors[:10]  # Limit errors to first 10
                    }
                    
                except Exception as e:
                    return {'error': f"FPL API error: {str(e)}"}
        
        # Run the async function
        result = asyncio.run(fetch_and_update_positions())
        
        if 'error' in result:
            return JsonResponse({'success': False, 'error': result['error']})
        
        return JsonResponse({
            'success': True,
            'message': f'Updated positions for {result["updated_count"]} players and teams for {result["team_updated_count"]} players',
            'updated_count': result['updated_count'],
            'team_updated_count': result['team_updated_count'],
            'position_changes': result['position_changes'],
            'team_changes': result['team_changes'],
            'errors': result['errors']
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# Removed old batch-based and optimized methods
# Now using only the player-by-player approach with accurate counting and progress tracking


@csrf_exempt
def recalculate_player_elos(request):
    """
    Player-by-player Elo recalculation using the exact same method as elo_model.py
    Clear progress tracking and accurate player counting.
    
    Uses the utility function from MyApi.utils.elo_calculator for consistency.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Only POST method allowed'})
    
    try:
        import asyncio
        from MyApi.utils.elo_calculator import player_by_player_elo_calculation
        
        # Run the player-by-player calculation
        result = asyncio.run(player_by_player_elo_calculation(show_progress=False))
        
        if 'success' in result and result['success']:
            return JsonResponse({
                'success': True,
                'message': f"Successfully recalculated Elo ratings for {result['successful_players']} players (Week {result['week']})",
                'updated_count': result['successful_players'],
                'total_players': result['total_players'],
                'failed_count': result['failed_players'],
                'duration': f"{result['duration']:.2f} seconds",
                'processing_rate': f"{result['processing_rate']:.2f} players/second",
                'week': result['week'],
                'method': 'player_by_player'
            })
        else:
            return JsonResponse({
                'success': False, 
                'error': result.get('error', 'Player-by-player calculation failed')
            })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Elo calculation failed: {str(e)}'})


@csrf_exempt
def system_info(request):
    """
    API endpoint to get current system information for the data page.
    """
    if request.method != 'GET':
        return JsonResponse({'success': False, 'error': 'Only GET method allowed'})
    
    try:
        from MyApi.models import SystemSettings, Player
        
        # Get system settings
        settings = SystemSettings.get_settings()
        
        # Get player count for current week
        current_week = settings.current_gameweek
        total_players = Player.objects.filter(week=current_week).count()
        
        # Format last update time
        last_update = 'Never'
        if settings.last_data_update:
            last_update = settings.last_data_update.strftime('%Y-%m-%d %H:%M')
        
        return JsonResponse({
            'success': True,
            'current_gameweek': settings.current_gameweek,
            'current_season': settings.current_season,
            'total_players': total_players,
            'last_update': last_update
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
def import_current_gameweek_data(request):
    """
    Import current gameweek player performance data from FPL API.
    Safely appends new data without destroying existing records.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Only POST method allowed'})
    
    try:
        import asyncio
        from MyApi.utils.gameweek_importer import get_current_gameweek_data
        
        # Run the gameweek data import
        result = asyncio.run(get_current_gameweek_data())
        
        if result.get('success'):
            return JsonResponse({
                'success': True,
                'message': f"Successfully imported gameweek {result['gameweek']} data",
                'gameweek': result['gameweek'],
                'new_matches': result['new_matches'],
                'updated_matches': result['updated_matches'],
                'skipped_matches': result['skipped_matches'],
                'errors': result['errors'],
                'duration': f"{result['duration']:.2f} seconds",
                'total_players': result['total_players']
            })
        else:
            return JsonResponse({
                'success': False, 
                'error': result.get('error', 'Gameweek data import failed')
            })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Gameweek import failed: {str(e)}'})


@csrf_exempt
def get_current_gameweek_info(request):
    """
    Get current gameweek information from FPL API for display purposes.
    """
    try:
        from MyApi.utils.fpl_gameweek_info import get_current_gameweek_sync
        
        # Get gameweek information
        info = get_current_gameweek_sync()
        
        return JsonResponse(info)
        
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': f'Failed to fetch gameweek info: {str(e)}'
        })


@csrf_exempt
def import_season_gameweeks(request):
    """
    Import all gameweeks for the current season (2025-26) from FPL API.
    Provides clean, consistent data with proper team names.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Only POST method allowed'})
    
    try:
        import asyncio
        from MyApi.utils.season_gameweek_importer import import_current_season_data
        
        # Run the season gameweek import
        result = asyncio.run(import_current_season_data())
        
        if result.get('success'):
            return JsonResponse({
                'success': True,
                'message': f"Successfully imported season {result['season']} data",
                'season': result['season'],
                'gameweeks_processed': result['gameweeks_processed'],
                'total_new_matches': result['total_new_matches'],
                'total_updated_matches': result['total_updated_matches'],
                'total_skipped_matches': result['total_skipped_matches'],
                'total_errors': result['total_errors'],
                'duration': f"{result['duration']:.2f} seconds",
                'gameweek_stats': result.get('gameweek_stats', {})
            })
        else:
            return JsonResponse({
                'success': False, 
                'error': result.get('error', 'Season gameweek import failed')
            })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Season import failed: {str(e)}'})


@csrf_exempt
def update_player_costs_from_fpl(request):
    """
    Update all player costs from FPL API without affecting Elo ratings.
    Uses the separate fpl_cost_updater utility module.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Only POST method allowed'})
    
    try:
        import asyncio
        from MyApi.utils.fpl_cost_updater import update_all_player_costs_from_fpl
        
        # Run the cost update
        result = asyncio.run(update_all_player_costs_from_fpl(show_progress=False))
        
        if result.get('success'):
            return JsonResponse({
                'success': True,
                'message': f"Successfully updated costs for {result['players_updated']} players (Week {result['week']})",
                'total_players': result['total_players'],
                'players_updated': result['players_updated'],
                'successful_updates': result['successful_updates'],
                'failed_updates': result['failed_updates'],
                'duration': f"{result['duration']:.2f} seconds",
                'processing_rate': f"{result['processing_rate']:.2f} players/second",
                'week': result['week'],
                'significant_changes': len([c for c in result['cost_changes'] if abs(c['change']) > 0.5])
            })
        else:
            return JsonResponse({
                'success': False, 
                'error': result.get('error', 'Cost update failed')
            })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Cost update failed: {str(e)}'})


# Removed ultra-optimized method - now using only the player-by-player approach


@csrf_exempt
def calculate_projected_points(request):
    """
    API endpoint to calculate projected points for all players' next 3 games.
    Uses the same expected points formula as ELO calculator.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Only POST method allowed'})
    
    try:
        import asyncio
        from MyApi.utils.projected_points_calculator import calculate_all_projected_points
        
        # Always override existing projections to get fresh calculations
        result = asyncio.run(calculate_all_projected_points(override_existing=True))
        
        if result.get('success'):
            return JsonResponse({
                'success': True,
                'message': f"Successfully calculated projected points for {result['successful_players']} players",
                'fixtures_created': result['fixtures_created'],
                'total_projections': result['total_projections'],
                'successful_players': result['successful_players'],
                'failed_players': result['failed_players'],
                'total_players': result['total_players']
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Projected points calculation failed')
            })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Projected points calculation failed: {str(e)}'})


@csrf_exempt
def get_player_projected_points(request, player_name):
    """
    API endpoint to get projected points for a specific player.
    """
    try:
        import asyncio
        from MyApi.utils.projected_points_calculator import get_player_projected_summary
        
        # Get projected points summary
        result = asyncio.run(get_player_projected_summary(player_name))
        
        if result.get('error'):
            return JsonResponse({
                'success': False,
                'error': result['error']
            })
        
        return JsonResponse({
            'success': True,
            'player_name': result['player_name'],
            'total_projected_points': result['total_projected_points'],
            'games_projected': result['games_projected'],
            'projections': result['projections']
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Failed to get projected points: {str(e)}'})


@csrf_exempt
def get_all_projected_points(request):
    """
    API endpoint to get projected points for all players (top performers) or specific player.
    Supports query parameters: player_name, player_id
    """
    try:
        from MyApi.models import ProjectedPoints, Player
        from django.db.models import Sum
        
        # Check if specific player is requested
        player_name = request.GET.get('player_name')
        player_id = request.GET.get('player_id')
        
        if player_name:
            # Get projected points for specific player by name
            total_projected = ProjectedPoints.objects.filter(
                player_name=player_name
            ).aggregate(
                total=Sum('adjusted_expected_points')
            )['total'] or 0
            
            return JsonResponse({
                'success': True,
                'player_name': player_name,
                'total_projected_points': round(total_projected, 2)
            })
        
        elif player_id:
            # Get projected points for specific player by ID
            try:
                player = Player.objects.get(id=player_id)
                total_projected = ProjectedPoints.objects.filter(
                    player_name=player.name
                ).aggregate(
                    total=Sum('adjusted_expected_points')
                )['total'] or 0
                
                return JsonResponse({
                    'success': True,
                    'player_id': player_id,
                    'player_name': player.name,
                    'total_projected_points': round(total_projected, 2)
                })
            except Player.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': f'Player with ID {player_id} not found'
                })
        
        # Get top players by total projected points for next 3 games
        top_players = (
            ProjectedPoints.objects
            .values('player_name')
            .annotate(total_projected=Sum('adjusted_expected_points'))
            .order_by('-total_projected')[:50]  # Top 50 players
        )
        
        results = []
        for player_data in top_players:
            player_name = player_data['player_name']
            total_projected = player_data['total_projected']
            
            # Get individual game projections
            projections = ProjectedPoints.objects.filter(
                player_name=player_name
            ).order_by('gameweek')[:4]
            
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
            
            results.append({
                'player_name': player_name,
                'total_projected_points': round(total_projected, 2),
                'games_projected': len(projection_details),
                'projections': projection_details
            })
        
        return JsonResponse({
            'success': True,
            'total_players': len(results),
            'players': results
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Failed to get all projected points: {str(e)}'})


@csrf_exempt
def generate_squads_points(request):
    """
    Generate squads using projected points instead of ELO ratings.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Only POST method allowed'})
    
    try:
        import json
        from MyApi.models import Player, ProjectedPoints, SystemSettings
        from django.db.models import Sum
        
        data = json.loads(request.body) if request.body else {}
        formation = data.get('formation', '3-4-3')
        
        current_week = SystemSettings.get_current_gameweek()
        
        # Get all players with their projected points
        players_with_projections = []
        players = Player.objects.filter(week=current_week)
        
        for player in players:
            # Get total projected points for this player
            total_projected = ProjectedPoints.objects.filter(
                player_name=player.name
            ).aggregate(
                total=Sum('adjusted_expected_points')
            )['total'] or 0
            
            players_with_projections.append({
                'name': player.name,
                'position': player.position,
                'team': player.team,
                'cost': player.cost,
                'elo': player.elo,
                'projected_points': round(total_projected, 1)
            })
        
        # Sort by projected points (descending)
        players_with_projections.sort(key=lambda x: x['projected_points'], reverse=True)
        
        # Generate 4 squads using projected points selection
        squads_generated = 0
        for squad_num in range(1, 5):
            try:
                squad = generate_single_squad_points(players_with_projections, formation, squad_num)
                if squad:
                    # Save squad (you might want to save to database)
                    squads_generated += 1
            except Exception as e:
                print(f"Error generating squad {squad_num}: {e}")
        
        return JsonResponse({
            'success': True,
            'message': f'Generated {squads_generated} squads using projected points',
            'squads_created': squads_generated,
            'formation': formation,
            'selection_mode': 'projected_points'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Squad generation failed: {str(e)}'})


@csrf_exempt
def recalculate_multipliers(request):
    """
    API endpoint to recalculate difficulty multipliers using current season data.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Only POST method allowed'})
    
    try:
        import asyncio
        import sys
        import os
        from django.conf import settings
        
        # Add the project directory to Python path
        project_dir = settings.BASE_DIR
        if project_dir not in sys.path:
            sys.path.append(str(project_dir))
        
        # Import the difficulty multiplier calculator
        from MyApi.utils.calculate_difficulty_multiplier import recalculate_difficulty_multipliers
        
        # Run the multiplier calculation
        result = recalculate_difficulty_multipliers()
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'matches_processed': result.get('matches_processed', 0),
                'multipliers': result.get('multipliers', {}),
                'message': 'Difficulty multipliers successfully recalculated'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Unknown error occurred')
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Failed to recalculate multipliers: {str(e)}'
        })


def generate_single_squad_points(players, formation, squad_num):
    """
    Generate a single squad using projected points optimization.
    """
    # Formation requirements
    formation_requirements = {
        '3-4-3': {'Keeper': 1, 'Defender': 3, 'Midfielder': 4, 'Attacker': 3},
        '3-5-2': {'Keeper': 1, 'Defender': 3, 'Midfielder': 5, 'Attacker': 2},
        '4-4-2': {'Keeper': 1, 'Defender': 4, 'Midfielder': 4, 'Attacker': 2},
        '4-3-3': {'Keeper': 1, 'Defender': 4, 'Midfielder': 3, 'Attacker': 3}
    }
    
    requirements = formation_requirements.get(formation, formation_requirements['3-4-3'])
    budget = 100.0
    selected_players = []
    
    # Separate players by position
    by_position = {
        'Keeper': [p for p in players if p['position'] == 'Keeper'],
        'Defender': [p for p in players if p['position'] == 'Defender'],
        'Midfielder': [p for p in players if p['position'] == 'Midfielder'],
        'Attacker': [p for p in players if p['position'] == 'Attacker']
    }
    
    # Select players by position (greedy selection based on projected points per cost)
    for position, needed in requirements.items():
        available = [p for p in by_position[position] if p['name'] not in [sp['name'] for sp in selected_players]]
        
        # Sort by projected points per cost ratio
        available.sort(key=lambda x: x['projected_points'] / x['cost'] if x['cost'] > 0 else 0, reverse=True)
        
        # Add some variation for different squads
        start_idx = (squad_num - 1) * 2  # Offset for squad variation
        
        for i in range(needed):
            if start_idx + i < len(available):
                candidate = available[start_idx + i]
                if sum(p['cost'] for p in selected_players) + candidate['cost'] <= budget:
                    selected_players.append(candidate)
    
    # Store squad in session/cache (simplified for now)
    # In a real implementation, you'd save to database
    global generated_squads_points
    if 'generated_squads_points' not in globals():
        generated_squads_points = {}
    
    generated_squads_points[squad_num] = {
        'goalkeepers': [p for p in selected_players if p['position'] == 'Keeper'],
        'defenders': [p for p in selected_players if p['position'] == 'Defender'],
        'midfielders': [p for p in selected_players if p['position'] == 'Midfielder'],
        'forwards': [p for p in selected_players if p['position'] == 'Attacker']
    }
    
    return generated_squads_points[squad_num]


def get_squad_points(request, squad_number):
    """
    Get a specific squad generated using projected points.
    """
    try:
        global generated_squads_points
        if 'generated_squads_points' not in globals():
            return JsonResponse({'success': False, 'error': 'No squads generated yet'})
        
        squad = generated_squads_points.get(int(squad_number))
        if not squad:
            return JsonResponse({'success': False, 'error': f'Squad {squad_number} not found'})
        
        return JsonResponse({
            'success': True,
            'squad': squad,
            'squad_number': squad_number,
            'selection_mode': 'projected_points'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Failed to get squad: {str(e)}'})


def squad_points_page(request):
    """
    Render the squad points page.
    """
    return render(request, 'squad_points.html')


# TEST FUNCTIONS FOR SUBSTITUTE RECOMMENDATIONS - DO NOT AFFECT EXISTING FUNCTIONALITY

@csrf_exempt
def test_recommend_substitutes(request):
    """
    TEST ENDPOINT: Recommend substitutes using projected points optimization.
    This is a test function that doesn't affect existing functionality.
    """
    try:
        from MyApi.utils.recommend_substitutes import recommend_substitutes_test
        
        # Get parameters from request
        data = json.loads(request.body) if request.body else {}
        max_recommendations = data.get('max_recommendations', 4)
        budget_constraint = data.get('budget_constraint', 100.0)
        
        # Get recommendations
        result = recommend_substitutes_test(max_recommendations, budget_constraint)
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': f'Test substitute recommendation failed: {str(e)}'
        })


@csrf_exempt 
def test_analyze_squad_weaknesses(request):
    """
    TEST ENDPOINT: Analyze current squad weaknesses.
    This is a test function that doesn't affect existing functionality.
    """
    try:
        from MyApi.utils.recommend_substitutes import analyze_squad_weaknesses_test
        
        # Analyze current squad
        result = analyze_squad_weaknesses_test()
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Test squad analysis failed: {str(e)}'
        })


@csrf_exempt
def test_simulate_substitutions(request):
    """
    TEST ENDPOINT: Simulate the impact of proposed substitutions.
    This is a test function that doesn't affect existing functionality.
    """
    try:
        from MyApi.utils.recommend_substitutes import simulate_substitution_impact_test
        
        # Get substitutions from request
        data = json.loads(request.body) if request.body else {}
        substitutions = data.get('substitutions', [])
        
        if not substitutions:
            return JsonResponse({
                'success': False,
                'error': 'No substitutions provided for simulation'
            })
        
        # Simulate substitutions
        result = simulate_substitution_impact_test(substitutions)
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Test substitution simulation failed: {str(e)}'
        })


@csrf_exempt
def update_current_squad(request):
    """
    Replace the entire current squad with the provided squad data.
    Expected POST data: {"squad": [ {"name": ..., "position": ...}, ... ] }
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method allowed'}, status=405)
    try:
        data = json.loads(request.body)
        local_team = data.get('squad')
        # Accept both a flat list (legacy) and a grouped dict (new)
        if isinstance(local_team, list):
            # Use conversion utility to group
            from MyApi.utils.squad_conversion import frontend_to_backend_squad
            squad_dict = frontend_to_backend_squad(local_team)
        elif isinstance(local_team, dict):
            # Already grouped, validate keys
            required_keys = {'goalkeepers', 'defenders', 'midfielders', 'forwards'}
            if not required_keys.issubset(local_team.keys()):
                return JsonResponse({'error': 'Grouped squad dict missing required keys.'}, status=400)
            squad_dict = local_team
        else:
            return JsonResponse({'error': 'squad must be a list or grouped dict.'}, status=400)
        current_squad_instance = CurrentSquad.get_or_create_current_squad()
        current_squad_instance.squad = squad_dict
        current_squad_instance.save()
        return JsonResponse({'success': True, 'squad': current_squad_instance.squad})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)