from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("data/", views.data, name="data"),
    path("team_selection/", views.team_selection, name="team_selection"),
    path("squads/", views.squads, name="squads"),
    path("player_ratings/", views.player_ratings, name="player_ratings"),
    path("gameweek_manager/", views.gameweek_manager, name="gameweek_manager"),
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
    path('api/update_costs/', views.update_player_costs_from_fpl, name='update_player_costs_from_fpl'),
    # Removed old optimized methods - now using only the player-by-player approach
    path('api/system_info/', views.system_info, name='system_info'),
]