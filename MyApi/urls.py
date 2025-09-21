from django.urls import path

from . import views

urlpatterns = [
    path('squads/', views.get_squads, name='get_squads'),
    path('squads/', views.generate_squads_points, name='generate_squads_points'),
    path('current_squad/', views.get_current_squad, name='get_current_squad'),
    path('all-players/', views.get_all_players, name='get_all_players'),
    path('add-player/', views.add_player_to_squad, name='add_player_to_squad'),
    path('remove-player/', views.remove_player_from_squad, name='remove_player_from_squad'),
    path('set_gameweek/', views.set_gameweek, name='set_gameweek'),
    path('refresh_players/', views.refresh_players, name='refresh_players'),
    path('refresh_fixtures/', views.refresh_fixtures, name='refresh_fixtures'),
    path('full_refresh/', views.full_refresh, name='full_refresh'),
    path('update_positions/', views.update_player_positions_from_fpl, name='update_player_positions_from_fpl'),
    path('recalculate_elos/', views.recalculate_player_elos, name='recalculate_player_elos'),
    path('import_gameweek/', views.import_current_gameweek_data, name='import_current_gameweek_data'),
    path('gameweek_info/', views.get_current_gameweek_info, name='get_current_gameweek_info'),
    path('import_season/', views.import_season_gameweeks, name='import_season_gameweeks'),
    path('update_costs/', views.update_player_costs_from_fpl, name='update_player_costs_from_fpl'),
    # Projected Points API endpoints
    path('calculate_projected_points/', views.calculate_projected_points, name='calculate_projected_points'),
    path('recalculate_multipliers/', views.recalculate_multipliers, name='recalculate_multipliers'),
    path('projected_points/<str:player_name>/', views.get_player_projected_points, name='get_player_projected_points'),
    path('all_projected_points/', views.get_all_projected_points, name='get_all_projected_points'),
    path('generate_squads_points/', views.generate_squads_points, name='generate_squads_points'),
    path('squad_points/<int:squad_number>/', views.get_squad_points, name='get_squad_points'),
    # Removed old optimized methods - now using only the player-by-player approach
    path('system_info/', views.system_info, name='system_info'),
    # TEST ENDPOINTS for substitute recommendations (do not affect existing functionality)
    path('test/recommend_substitutes/', views.test_recommend_substitutes, name='test_recommend_substitutes'),
    path('test/analyze_squad/', views.test_analyze_squad_weaknesses, name='test_analyze_squad_weaknesses'),
    path('test/simulate_substitutions/', views.test_simulate_substitutions, name='test_simulate_substitutions'),
    path('update_current_squad/', views.update_current_squad, name='update_current_squad'),
]