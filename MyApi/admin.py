from django.contrib import admin
from .models import PlayerMatch, EloCalculation, Player, CurrentSquad, SystemSettings, PlayerFixture, ProjectedPoints

# Register your models here.

@admin.register(PlayerMatch)
class PlayerMatchAdmin(admin.ModelAdmin):
    list_display = ['player_name', 'date', 'opponent', 'competition', 'points', 'elo_after_match']
    list_filter = ['competition', 'season', 'date']
    search_fields = ['player_name', 'opponent']
    ordering = ['-date', 'player_name']

@admin.register(EloCalculation)
class EloCalculationAdmin(admin.ModelAdmin):
    list_display = ['player_name', 'week', 'season', 'elo', 'elo_change']
    list_filter = ['week', 'season']
    search_fields = ['player_name']
    ordering = ['-week', 'player_name']

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ['name', 'team', 'position', 'elo', 'cost', 'week']
    list_filter = ['position', 'team', 'week']
    search_fields = ['name', 'team']
    ordering = ['-elo']

@admin.register(CurrentSquad)
class CurrentSquadAdmin(admin.ModelAdmin):
    list_display = ['name', 'updated_at', 'created_at']
    search_fields = ['name']
    ordering = ['-updated_at']

@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ['current_season', 'current_gameweek', 'updated_at']

@admin.register(PlayerFixture)
class PlayerFixtureAdmin(admin.ModelAdmin):
    list_display = ['player_name', 'team', 'gameweek', 'opponent', 'is_home', 'difficulty', 'fixture_date']
    list_filter = ['gameweek', 'team', 'is_home', 'difficulty', 'competition']
    search_fields = ['player_name', 'team', 'opponent']
    ordering = ['gameweek', 'fixture_date', 'player_name']

@admin.register(ProjectedPoints)
class ProjectedPointsAdmin(admin.ModelAdmin):
    list_display = ['player_name', 'gameweek', 'opponent', 'expected_points', 'adjusted_expected_points', 'difficulty_rating']
    list_filter = ['gameweek', 'difficulty_rating', 'competition']
    search_fields = ['player_name', 'opponent']
    ordering = ['gameweek', '-adjusted_expected_points']
