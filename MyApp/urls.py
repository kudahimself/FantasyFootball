from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("team_selection/", views.team_selection, name="team_selection"),
    path("squad_elo/", views.squad_elo, name="squad_elo"),
    path("player_ratings/", views.player_ratings, name="player_ratings"),
    path("data_manager/", views.data_manager, name="data_manager"),
    path("player/<str:player_name>/", views.player_info, name="player_info"),
    path('squad_points/', views.squad_points_page, name='squad_points'),
    path('profile/', views.profile, name='profile'),
    path('api/', include('MyApi.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('signup/', views.signup, name='signup'),
]
