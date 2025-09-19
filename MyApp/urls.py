from django.urls import path

from . import views
from django.urls import path, include

urlpatterns = [
    path("", views.home, name="home"),
    path("team_selection/", views.team_selection, name="team_selection"),
    path("squads/", views.squads, name="squads"),
    path("player_ratings/", views.player_ratings, name="player_ratings"),
    path("data_manager/", views.data_manager, name="data_manager"),
    path("player/<str:player_name>/", views.player_info, name="player_info"),
    # Squad Points API endpoints
    path('squad_points/', views.squad_points_page, name='squad_points'),
    path('api/', include('MyApi.urls')),
]
