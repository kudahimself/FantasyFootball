import datetime
import asyncio
import aiohttp
from fpl import FPL


class FantasyDataFetcher:
    """
    Fetches Premier League fantasy football player data for the last 2 years.
    """
    def __init__(self):
        self.start_date = datetime.date.today() - datetime.timedelta(days=3*365)
        self.end_date = datetime.date.today()



    async def get_player_history(self, player_id: int):
        """
        Fetches and prints the gameweek history for a given player ID.
        """
        async with aiohttp.ClientSession() as session:
            fpl = FPL(session)
            player = await fpl.get_player(player_id, include_summary=True)

            if player:
                print(f"Gameweek history for {player.first_name} {player.second_name}:\n")
                
                # The player's history is in the 'history' attribute
                history = player.history

                if history:
                    # Print a header for the data
                    header = "{:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10}".format(
                        "Gameweek", "Points", "Minutes", "Goals", "Assists", "Bonus", "CleanS", "Opponent"
                    )
                    print(header)
                    print("-" * len(header))
                    
                    # Loop through each gameweek and print the data
                    for gw_data in history:
                        gameweek = gw_data.get('round')
                        points = gw_data.get('total_points')
                        minutes = gw_data.get('minutes')
                        goals = gw_data.get('goals_scored')
                        assists = gw_data.get('assists')
                        bonus = gw_data.get('bonus')
                        clean_sheets = gw_data.get('clean_sheets')
                        
                        # The 'opponent_team' ID can be used to get the team name
                        opponent_team_id = gw_data.get('opponent_team')
                        opponent_team = "Team ID " + str(opponent_team_id)

                        # Fetch team names from FPL API if needed
                        # teams = await fpl.get_teams()
                        # opponent_team_name = next(t['name'] for t in teams if t['id'] == opponent_team_id)

                        print(f"{gameweek:<10} {points:<10} {minutes:<10} {goals:<10} {assists:<10} {bonus:<10} {clean_sheets:<10} {opponent_team:<10}")
                else:
                    print("No gameweek history found for this player.")
            else:
                print(f"Could not find player with ID {player_id}.")

# Replace 210 with the ID of the player you want to get data for (e.g., Erling Haaland)


import asyncio

async def main():
    player_id = 
    f = FantasyDataFetcher()
    await f.get_player_history(player_id)


if __name__ == "__main__":
    asyncio.run(main())