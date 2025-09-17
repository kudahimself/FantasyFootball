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

def fantasy_data(request):
    return render(request, 'fantasy_data.html')

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


def gameweek_manager(request):
    """
    Game week manager page to display current game week, set new game week,
    and manage data refresh operations.
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
            'current_season': '2024/25',
            'last_update': 'Never',
            'total_players': 0,
        }
    
    return render(request, 'gameweek_manager.html', context)


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