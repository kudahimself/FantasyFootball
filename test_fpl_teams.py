#!/usr/bin/env python3

import asyncio
import aiohttp
from fpl import FPL

async def test_fpl_teams():
    """Test what team information is available from FPL API."""
    async with aiohttp.ClientSession() as session:
        fpl = FPL(session)
        
        try:
            # Get first few players to see what data is available
            players = await fpl.get_players()
            
            print("FPL Player Data Structure:")
            for i, player in enumerate(players[:5]):  # First 5 players
                print(f"\nPlayer {i+1}: {player.first_name} {player.second_name}")
                print(f"  Element Type (position): {player.element_type}")
                print(f"  Team: {player.team}")
                print(f"  Team Code: {getattr(player, 'team_code', 'Not available')}")
                
                # Check available attributes
                attrs = [attr for attr in dir(player) if not attr.startswith('_')]
                team_attrs = [attr for attr in attrs if 'team' in attr.lower()]
                print(f"  Team-related attributes: {team_attrs}")
                
            # Also get teams to see team mapping
            teams = await fpl.get_teams()
            print(f"\nAvailable teams ({len(teams)}):")
            for team in teams[:10]:  # First 10 teams
                print(f"  {team.id}: {team.name} ({team.short_name})")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_fpl_teams())