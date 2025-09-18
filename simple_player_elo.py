import os
import django
import asyncio
from asgiref.sync import sync_to_async
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')
django.setup()

from MyApi.models import Player, PlayerMatch, EloCalculation

def calculate_elo_change(current_elo, points, competition, k=20):
    """Calculate Elo change using the EXACT same method as elo_model.py"""
    
    # League ratings matching elo_model.py exactly
    if competition == 'Champions League' or competition == 'Champions Lg':
        League_Rating = 1600
    elif competition in ['Premier League', 'FA Cup', 'Europa League']:
        League_Rating = 1500
    elif competition in ['Bundesliga', 'La Liga', 'Serie A']:
        League_Rating = 1300
    elif competition in ['Ligue 1', 'Eredivisie']:
        League_Rating = 1250
    elif competition in ['Championship', 'Primeira Liga']:
        League_Rating = 1000
    else:
        League_Rating = 900
    
    # Expected score based on Elo (normalized to points scale) - EXACT formula from elo_model.py
    E_a = round(k/(1 + 10**(League_Rating/current_elo)), 2)
    
    # Calculate new Elo using EXACT formula from elo_model.py
    # The formula is the same for both Pa >= E_a and Pa < E_a cases
    new_elo = round((current_elo + k * (points - E_a)), 3)
    
    return new_elo

async def calculate_elo_for_single_player(player_name, current_week=4):
    """Calculate Elo for a single player using EXACT same method as elo_model.py"""
    
    try:
        # Get all matches for this player, ordered by date
        matches = await sync_to_async(list)(
            PlayerMatch.objects.filter(player_name=player_name)
            .order_by('date')
        )
        
        if not matches:
            return None
        
        # Get player record
        try:
            player_obj = await sync_to_async(Player.objects.get)(
                name=player_name, week=current_week
            )
        except Player.DoesNotExist:
            return None
        
        # Calculate Elo progression using EXACT same method as elo_model.py
        initial_elo = 1200.0  # Starting Elo rating - EXACT same as elo_model.py
        current_elo = initial_elo
        
        # First match starts at 1200 - EXACT same as elo_model.py
        if matches:
            matches[0].elo_before_match = initial_elo
            
            # Process first match
            if matches[0].points is not None:
                new_elo = calculate_elo_change(current_elo, matches[0].points, matches[0].competition)
                matches[0].elo_after_match = new_elo
                current_elo = new_elo
            else:
                matches[0].elo_after_match = initial_elo
            
            # Process remaining matches - EXACT same logic as elo_model.py
            for i in range(1, len(matches)):
                Ra = current_elo  # Previous Elo
                Pa = matches[i].points if matches[i].points is not None else 0  # Points from this match
                League = matches[i].competition  # Competition
                
                matches[i].elo_before_match = Ra
                
                # Calculate new Elo using EXACT same method as elo_model.py
                new_elo = calculate_elo_change(Ra, Pa, League)
                matches[i].elo_after_match = new_elo
                current_elo = new_elo
        
        # Update player record
        final_elo = current_elo
        player_obj.elo = final_elo
        player_obj.cost = max(4.0, min(15.0, 4.0 + (final_elo - 1200) / 100))
        
        # Save updates
        await sync_to_async(PlayerMatch.objects.bulk_update)(
            matches, ['elo_before_match', 'elo_after_match']
        )
        await sync_to_async(player_obj.save)()
        
        # Create/update EloCalculation
        if matches:
            latest_match = matches[-1]
            elo_calc, created = await sync_to_async(EloCalculation.objects.update_or_create)(
                player_name=player_name,
                week=current_week,
                season="2024-2025",
                defaults={
                    'elo_rating': final_elo,
                    'previous_elo': initial_elo,
                    'elo_change': final_elo - initial_elo,
                    'matches_played': len(matches),
                    'last_match_date': latest_match.date,
                    'form_rating': latest_match.points if latest_match.points else 0,
                }
            )
        
        return {
            'player_name': player_name,
            'final_elo': final_elo,
            'matches_processed': len(matches),
            'status': 'success'
        }
        
    except Exception as e:
        return {
            'player_name': player_name,
            'error': str(e),
            'status': 'error'
        }

async def player_by_player_elo_calculation(current_week=4):
    """Calculate Elo ratings for all players, one player at a time"""
    
    print(f"🚀 Starting Player-by-Player Elo Calculation")
    print(f"📅 Week: {current_week}")
    print("=" * 60)
    
    start_time = time.time()
    
    # Get all unique players for the current week
    unique_players = await sync_to_async(list)(
        Player.objects.filter(week=current_week).values_list('name', flat=True).distinct()
    )
    
    total_players = len(unique_players)
    print(f"👥 Total players to process: {total_players}")
    print()
    
    processed_players = 0
    successful_players = 0
    failed_players = 0
    
    # Process each player individually
    for i, player_name in enumerate(unique_players, 1):
        result = await calculate_elo_for_single_player(player_name, current_week)
        
        if result:
            if result['status'] == 'success':
                successful_players += 1
                
                # Show progress every 25 players
                if i % 25 == 0 or i == total_players:
                    print(f"✅ Player {i:3d}/{total_players}: {result['player_name'][:30]:<30} → Elo: {result['final_elo']:7.1f} ({result['matches_processed']} matches)")
            else:
                failed_players += 1
                if failed_players <= 5:  # Show first few errors
                    print(f"❌ Player {i:3d}/{total_players}: {result['player_name'][:30]:<30} → Error: {result['error']}")
        
        processed_players += 1
    
    # Summary
    end_time = time.time()
    duration = end_time - start_time
    
    print()
    print("=" * 60)
    print("📊 CALCULATION SUMMARY")
    print("=" * 60)
    print(f"⏱️  Total time: {duration:.2f} seconds")
    print(f"👥 Players processed: {processed_players}")
    print(f"✅ Successful calculations: {successful_players}")
    print(f"❌ Failed calculations: {failed_players}")
    
    if successful_players > 0:
        rate = successful_players / duration
        print(f"🚀 Processing rate: {rate:.2f} players/second")
    
    # Show top 10 players
    print()
    print("🏆 TOP 10 PLAYERS BY ELO RATING:")
    print("-" * 50)
    
    try:
        top_players = await sync_to_async(list)(
            EloCalculation.objects.filter(
                week=current_week, 
                season="2024-2025"
            ).order_by('-elo_rating')[:10]
        )
        
        for i, calc in enumerate(top_players, 1):
            print(f"{i:2d}. {calc.player_name[:30]:<30} {calc.elo_rating:7.1f}")
            
    except Exception as e:
        print(f"❌ Error retrieving top players: {e}")
    
    return {
        'success': True,
        'players_processed': processed_players,
        'successful_players': successful_players,
        'failed_players': failed_players,
        'duration': duration
    }

if __name__ == "__main__":
    asyncio.run(player_by_player_elo_calculation())