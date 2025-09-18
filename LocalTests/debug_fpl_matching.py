#!/usr/bin/env python3

import asyncio
import aiohttp
from fpl import FPL
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')
import django
django.setup()
from MyApi.models import Player
from asgiref.sync import sync_to_async

async def debug_fpl_matching():
    """Debug why FPL players aren't matching our database."""
    async with aiohttp.ClientSession() as session:
        fpl = FPL(session)
        
        try:
            # Get our database players using sync_to_async
            db_players = await sync_to_async(list)(Player.objects.values_list('name', flat=True))
            print(f"Database has {len(db_players)} players")
            
            # Get first few FPL players to see naming format
            fpl_players = await fpl.get_players()
            
            print("\nFirst 10 FPL players:")
            for i, player in enumerate(fpl_players[:10]):
                fpl_name = f"{player.first_name} {player.second_name}"
                fpl_name_clean = fpl_name.replace(' ', '_')
                print(f"  {fpl_name} (clean: {fpl_name_clean})")
                
                # Check if this matches any player in our DB
                matches = []
                for db_name in db_players:
                    if db_name in [fpl_name, fpl_name_clean, fpl_name.replace('_', ' ')]:
                        matches.append(db_name)
                    # Also check partial matches
                    elif fpl_name.split()[-1] in db_name or db_name.split()[-1] in fpl_name:
                        matches.append(f"Partial: {db_name}")
                
                if matches:
                    print(f"    Matches: {matches}")
                else:
                    print(f"    No match found")
            
            # Check some known players from our database
            print("\nChecking known players from our database:")
            test_players = ["Erling Haaland", "Mohamed Salah", "Bruno Borges Fernandes"]
            for db_name in test_players:
                print(f"\nLooking for: {db_name}")
                fpl_matches = []
                for player in fpl_players:
                    fpl_name = f"{player.first_name} {player.second_name}"
                    if db_name.split()[-1] in fpl_name or fpl_name.split()[-1] in db_name:
                        fpl_matches.append(f"{fpl_name} (team: {player.team})")
                
                if fpl_matches:
                    print(f"  Potential FPL matches: {fpl_matches[:3]}")
                else:
                    print("  No FPL matches found")
                    
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_fpl_matching())