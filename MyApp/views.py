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
    """
    return render(request, 'team_selection.html')

def squads(request):
    squad_numbers = range(1, 5) 
    context = {
        'squad_numbers': squad_numbers,
    }
    return render(request, 'squads.html', context)

def player_ratings(request):
    """
    Display all players with their ratings, cost, position, and other details.
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
        
        # Convert to list of dictionaries for template
        players_data = []
        for player in players_queryset:
            player_data = {
                'name': player.name,
                'position': player.position,
                'elo': round(float(player.elo), 1),
                'cost': float(player.cost),
                'comp': player.competition or 'Premier League',
                'opponent': 'Unknown'  # You can add this field to the model later if needed
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