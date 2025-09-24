from django.shortcuts import render, HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from MyApi.models import CurrentSquad, Player
import json

def home(request):
    """
    Render the home page.
    """
    return render(request, 'home.html')

def team_selection(request):
    """
    Team Selection page for building and managing fantasy squads.
    Renders player list on the server-side like player_ratings.
    """
    try:
        from MyApi.models import SystemSettings
        week = SystemSettings.get_settings().current_gameweek
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
                'elo': round(float(player.elo), 1),
                'cost': float(player.cost),
                'projected_points': projected_points,
            })

        players_data.sort(key=lambda x: x['elo'], reverse=True)

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
        # Load data from database using current gameweek from SystemSettings
        from MyApi.models import SystemSettings
        week = SystemSettings.get_settings().current_gameweek
        players_queryset = Player.objects.filter(week=week)
        print(f"[DEBUG] player_ratings: current_week from SystemSettings = {week}")

        if not players_queryset.exists():
            context = {
                'players': [],
                'total_players': 0,
                'error': f'No player data found for week {week}. Please import data first.'
            }
            return render(request, 'player_ratings.html', context)

        # Import models for fixtures and projected points
        from MyApi.models import PlayerFixture, ProjectedPoints, Team

        # Build a mapping from FPL team ID (as string) to team name
        team_id_to_name = {str(team.fpl_team_id): team.name for team in Team.objects.all()}

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
                    # Substitute team ID with name if possible
                    opponent_display = team_id_to_name.get(str(fixture.opponent), fixture.opponent)
                    next_fixtures.append({
                        'text': f"{home_away} {opponent_display}",
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


def squad_points_page(request):
    """
    Render the squad points page.
    """
    return render(request, 'squad_points.html')

