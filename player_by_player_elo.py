import os
import django
import asyncio
from asgiref.sync import sync_to_async
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')
django.setup()

from MyApi.models import Player, PlayerMatch, EloCalculation

async def calculate_elo_for_player(player_name, week=4, season=2024, k_factor=32):
    """Calculate Elo for a single player across all their matches"""
    
    # Get all matches for this player (PlayerMatch doesn't have week field, uses date)
    matches = await sync_to_async(list)(
        PlayerMatch.objects.filter(
            player_name=player_name,
            season=str(season)  # season is stored as string
        ).order_by('date')
    )
    
    if not matches:
        return None
    
    # League ratings for expected performance calculation
    league_ratings = {
        'Champions League': 1600,
        'Premier League': 1500,
        'Europa League': 1400,
        'Championship': 1300,
        'League One': 1200,
        'League Two': 1100,
        'FA Cup': 1450,
        'EFL Cup': 1350,
    }
    
    current_elo = 1500  # Starting Elo
    elo_records = []
    
    for match in matches:
        # Get league rating for expected performance
        league_rating = league_ratings.get(match.competition, 1500)
        
        # Calculate expected performance based on league strength
        expected_performance = league_rating / 1500.0
        
        # Actual performance (0-1 scale based on points/rating)
        # Using fantasy points if available, otherwise a basic calculation
        if hasattr(match, 'points') and match.points is not None:
            actual_performance = max(0, min(20, match.points)) / 20.0
        else:
            # Fallback calculation based on goals, assists, minutes
            base_performance = 0.5  # baseline
            if match.goals > 0:
                base_performance += match.goals * 0.2
            if match.assists > 0:
                base_performance += match.assists * 0.1
            if match.minutes_played >= 60:
                base_performance += 0.1
            actual_performance = min(1.0, base_performance)
        
        # Elo change: k * (actual - expected)
        elo_change = k_factor * (actual_performance - expected_performance)
        current_elo += elo_change
        
        # Create Elo record for this match (using a derived week number)
        # Since PlayerMatch doesn't have week, we'll create one record per week
        match_week = week  # For now, use target week
        
        elo_records.append(EloCalculation(
            player_name=player_name,
            week=match_week,
            season=season,
            elo_rating=round(current_elo, 2),
            matches_played=1,
            last_updated=match.date
        ))
    
    # Return only the final Elo for the target week
    if elo_records:
        return [elo_records[-1]]  # Just the final calculation
    return None

async def player_by_player_elo_calculation(week=4, season=2024):
    """Calculate Elo ratings for all players, one player at a time"""
    
    print(f"🚀 Starting Player-by-Player Elo Calculation")
    print(f"📅 Season: {season}, Week: {week}")
    print("=" * 60)
    
    start_time = time.time()
    
    # Get all unique players
    unique_players = await sync_to_async(list)(
        Player.objects.values_list('name', flat=True).distinct()
    )
    
    total_players = len(unique_players)
    print(f"👥 Total unique players to process: {total_players}")
    print()
    
    # Clear existing Elo calculations for this week/season
    deleted_count = await sync_to_async(
        EloCalculation.objects.filter(week__lte=week, season=season).delete
    )()
    print(f"🗑️  Cleared {deleted_count[0]} existing Elo records")
    print()
    
    processed_players = 0
    successful_players = 0
    all_elo_records = []
    
    # Process each player individually
    for i, player_name in enumerate(unique_players, 1):
        try:
            # Calculate Elo for this player
            elo_records = await calculate_elo_for_player(player_name, week, season)
            
            if elo_records:
                all_elo_records.extend(elo_records)
                successful_players += 1
                
                # Show progress every 50 players
                if i % 50 == 0 or i == total_players:
                    final_elo = elo_records[-1].elo_rating if elo_records else 1500
                    print(f"✅ Player {i:3d}/{total_players}: {player_name[:25]:<25} → Final Elo: {final_elo:7.1f}")
            
            processed_players += 1
            
        except Exception as e:
            print(f"❌ Error processing {player_name}: {str(e)}")
    
    print()
    print(f"💾 Bulk saving {len(all_elo_records)} Elo calculations...")
    
    # Bulk save all Elo records
    try:
        await sync_to_async(EloCalculation.objects.bulk_create)(
            all_elo_records, 
            ignore_conflicts=True
        )
        print(f"✅ Successfully saved {len(all_elo_records)} Elo calculations")
        
    except Exception as e:
        print(f"⚠️  Bulk save failed, trying individual saves: {str(e)}")
        # Fallback to individual saves
        saved_count = 0
        for record in all_elo_records:
            try:
                await sync_to_async(EloCalculation.objects.update_or_create)(
                    player_name=record.player_name,
                    week=record.week,
                    season=record.season,
                    defaults={
                        'elo_rating': record.elo_rating,
                        'matches_played': record.matches_played,
                        'last_updated': record.last_updated
                    }
                )
                saved_count += 1
            except Exception as save_error:
                print(f"❌ Failed to save {record.player_name}, week {record.week}: {save_error}")
        
        print(f"✅ Individually saved {saved_count} Elo calculations")
    
    # Summary
    end_time = time.time()
    duration = end_time - start_time
    
    print()
    print("=" * 60)
    print("📊 CALCULATION SUMMARY")
    print("=" * 60)
    print(f"⏱️  Total time: {duration:.2f} seconds")
    print(f"👥 Players processed: {processed_players}/{total_players}")
    print(f"✅ Players with Elo data: {successful_players}")
    print(f"💾 Elo records created: {len(all_elo_records)}")
    
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
                week=week, 
                season=season
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
        'elo_records_created': len(all_elo_records),
        'duration': duration
    }

if __name__ == "__main__":
    asyncio.run(player_by_player_elo_calculation())