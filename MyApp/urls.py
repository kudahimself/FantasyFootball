from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("team_selection/", views.team_selection, name="team_selection"),
    path("squads/", views.squads, name="squads"),
    path("player_ratings/", views.player_ratings, name="player_ratings"),
    path("data_manager/", views.data_manager, name="data_manager"),
    path("player/<str:player_name>/", views.player_info, name="player_info"),
    path('api/squads/', views.get_squads, name='get_squads'),
    path('api/current_squad/', views.get_current_squad, name='get_current_squad'),
    path('api/all-players/', views.get_all_players, name='get_all_players'),
    path('api/add-player/', views.add_player_to_squad, name='add_player_to_squad'),
    path('api/remove-player/', views.remove_player_from_squad, name='remove_player_from_squad'),
    path('api/set_gameweek/', views.set_gameweek, name='set_gameweek'),
    path('api/refresh_players/', views.refresh_players, name='refresh_players'),
    path('api/refresh_fixtures/', views.refresh_fixtures, name='refresh_fixtures'),
    path('api/full_refresh/', views.full_refresh, name='full_refresh'),
    path('api/update_positions/', views.update_player_positions_from_fpl, name='update_player_positions_from_fpl'),
    path('api/recalculate_elos/', views.recalculate_player_elos, name='recalculate_player_elos'),
    path('api/import_gameweek/', views.import_current_gameweek_data, name='import_current_gameweek_data'),
    path('api/gameweek_info/', views.get_current_gameweek_info, name='get_current_gameweek_info'),
    path('api/import_season/', views.import_season_gameweeks, name='import_season_gameweeks'),
    path('api/update_costs/', views.update_player_costs_from_fpl, name='update_player_costs_from_fpl'),
    # Projected Points API endpoints
    path('api/calculate_projected_points/', views.calculate_projected_points, name='calculate_projected_points'),
    path('api/recalculate_multipliers/', views.recalculate_multipliers, name='recalculate_multipliers'),
    path('api/projected_points/<str:player_name>/', views.get_player_projected_points, name='get_player_projected_points'),
    path('api/all_projected_points/', views.get_all_projected_points, name='get_all_projected_points'),
    # Squad Points API endpoints
    path('squad_points/', views.squad_points_page, name='squad_points'),
    path('api/generate_squads_points/', views.generate_squads_points, name='generate_squads_points'),
    path('api/squad_points/<int:squad_number>/', views.get_squad_points, name='get_squad_points'),
    # Removed old optimized methods - now using only the player-by-player approach
    path('api/system_info/', views.system_info, name='system_info'),
    # TEST ENDPOINTS for substitute recommendations (do not affect existing functionality)
    path('api/test/recommend_substitutes/', views.test_recommend_substitutes, name='test_recommend_substitutes'),
    path('api/test/analyze_squad/', views.test_analyze_squad_weaknesses, name='test_analyze_squad_weaknesses'),
    path('api/test/simulate_substitutions/', views.test_simulate_substitutions, name='test_simulate_substitutions'),
    path('api/update_current_squad/', views.update_current_squad, name='update_current_squad'),
]