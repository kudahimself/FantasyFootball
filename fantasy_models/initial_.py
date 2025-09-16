import re, os
import pandas as pd
import aiohttp
from fpl import FPL

class FootballerEloModel:
    
    def __init__(self, player_name):
        self.player_name = player_name
        self.df_player = pd.read_csv(f"./fbref_data/{self.player_name}.csv")
        self.df_player.dropna(subset=['Date'], inplace=True)  # Ensure 'Date' column has no NaN values
        self.df_player['Date'] = pd.to_datetime(self.df_player['Date'], errors='coerce').dt.strftime('%Y-%m-%d')
        self.df_player.fillna(0, inplace=True)  # Fill NaN values with 0
        if 'Gls' not in self.df_player.columns:
            self.df_player['Gls'] = 0
        if 'Ast' not in self.df_player.columns:
            self.df_player['Ast'] = 0
        self.df_player = self.df_player[self.df_player['Date'].notna() & (self.df_player['Date'].str.strip() != "")]
        # Ensure 'Saves' column exists for all players
        if 'Saves' not in self.df_player.columns:
            self.df_player['Saves'] = 0
        self.df_player = self.df_player[['Season', 'Date', 'Comp', 'Round', 'Opponent', 'Result', 'Pos', 'Min', 'Gls', 'Ast', 'Saves']]
        self.df_player['Result'] = self.df_player['Result'].apply(lambda x: re.sub(r"\(\d+\)", "", x))
        self.df_player['GoalsConceded'] = self.df_player['Result'].apply(
            lambda x: x.replace("W ", "")
                    .replace("L ", "")
                    .replace("D ", "")
                    .replace("–", "-")
                    .strip().split("-")[1]
        )
        self.df_player['GoalsScored'] = self.df_player['Result'].apply(
            lambda x: x.replace("W ", "")
                    .replace("L ", "")
                    .replace("D ", "")
                    .replace("–", "-")
                    .strip().split("-")[0]
        )
        self.df_player['CleanSheets'] = self.df_player['GoalsConceded'].astype(int).apply(lambda x: 1 if x == 0 else 0)
        self.df_player['GoalDifference'] = self.df_player['GoalsScored'].astype(int) - self.df_player['GoalsConceded'].astype(int)
        self.main_position = self.get_player_position()

        if self.main_position == 'Midfielder':
            self.df_player = self.midfielder_points()
        elif self.main_position == 'Attacker':
            self.df_player = self.attacker_points()
        elif self.main_position == 'Defender':
            self.df_player = self.defender_points()
        elif self.main_position == 'Keeper':
            self.df_player = self.keeper_points()

        self.players_elo = self.player_elo()

    def get_player_position(self):
        positions = self.df_player['Pos'].dropna().astype(str)
        attacker_count = positions.str.count(r'(S|F)').sum()
        midfielder_count = positions.str.count(r'M|RW|LW').sum()
        defender_count = positions.str.count(r'B').sum()
        keeper_count = positions.str.count(r'G').sum()
        counts = {
            'Attacker': attacker_count,
            'Midfielder': midfielder_count,
            'Defender': defender_count,
            'Keeper': keeper_count
        }
        main_position = max(counts, key=counts.get)
        return main_position



    def midfielder_points(self):
        """
        Calculate points for a midfielder based on goals and assists.
        Points: 5 for a goal, 3 for an assist.
        """
        self.df_player['Points'] = (
            (self.df_player['Gls'].astype(int) * 5) + 
            (self.df_player['Ast'].astype(int) * 3) +
            (self.df_player['CleanSheets'].astype(int) * 1))
        return self.df_player[['Season', 'Date', 'Comp', 'Round', 'Opponent', 'Result', 'Pos', 'Min', 'Gls', 'Ast', 'Points']]

    def attacker_points(self):
        """
        Calculate points for an attacker based on goals, assists, and clean sheets.
        Points: 5 for a goal, 3 for an assist, 1 for a clean sheet.
        """
        self.df_player['Points'] = (
            (self.df_player['Gls'].astype(int) * 5) +
            (self.df_player['Ast'].astype(int) * 3))
        return self.df_player[['Season', 'Date', 'Comp', 'Round', 'Opponent', 'Result', 'Pos', 'Min', 'Gls', 'Ast', 'Points']]


    def defender_points(self):
        """
        Calculate points for a defender based on goals, assists, and clean sheets.
        Points: 6 for a goal, 3 for an assist, 1 for a clean sheet.
        """
        self.df_player['Points'] = (
            (self.df_player['Gls'].astype(int) * 6) +
            (self.df_player['Ast'].astype(int) * 3) +
            (self.df_player['CleanSheets'].astype(int) * 4))
        return self.df_player[['Season', 'Date', 'Comp', 'Round', 'Opponent', 'Result', 'Pos', 'Min', 'Gls', 'Ast', 'Points']]

    def keeper_points(self):
        """
        Calculate points for a goalkeeper based on clean sheets and saves.
        Points: 4 for a clean sheet, 1 for every 3 saves.
        """
        self.df_player['Points'] = (self.df_player['CleanSheets'].astype(int) * 4 +
                            self.df_player['Saves'].astype(int) // 3)
        return self.df_player[['Season', 'Date', 'Comp', 'Round', 'Opponent', 'Result', 'Pos', 'Min', 'Gls', 'Ast', 'Points']]


    def player_elo(self, k=20):
        initial_elo = 1200.0  # Starting Elo rating
        self.df_player = self.df_player.reset_index(drop=True) # Ensure DataFrame is indexed correctly
        self.df_player['Elo'] = 0.0  # Initialize Elo column
        self.df_player.at[0, 'Elo'] = initial_elo  # Only the first match starts at 1200
        for i in range(1, len(self.df_player)):
            Ra = self.df_player.loc[i-1, 'Elo']
            Pa = self.df_player.loc[i-1, 'Points']
            League = self.df_player.loc[i-1, 'Comp']
        
            if League == 'Champions League' or League == 'Champions Lg':
                League_Rating = 1600
            elif League in ['Premier League', 'FA Cup', 'Europa League']:
                League_Rating = 1500
            elif League in ['Bundesliga', 'La Liga', 'Serie A']:
                League_Rating = 1300
            elif League in ['Ligue 1', 'Eredivisie']:
                League_Rating = 1250
            elif League in ['Championship', 'Primeira Liga']:
                League_Rating = 1000
            else:
                League_Rating = 900
            # Expected score based on Elo (normalized to points scale)
            E_a = round( k/(1 + 10**(League_Rating/Ra)), 2)
            # Update Elo
            if Pa >= E_a:
                self.df_player.at[i, 'Elo'] = round((Ra + k * (Pa - E_a)), 3)
            else:
                # Lose points: penalize by k * (E_a * Pa - Pa)
                self.df_player.at[i, 'Elo'] = round((Ra + k * (Pa - E_a)), 3)
            last_elo = self.df_player.at[i, 'Elo']
            
            self.df_player.to_csv(f'./elo_data/{self.player_name}.csv', index=False)
        return last_elo



async def all_players_elo():
    """
    Function to calculate Elo ratings for all players.
    """
    players = []
    for file in os.listdir('./fbref_data'):
        if file.endswith('.csv'):
            player_name = file[:-4]
            players.append(player_name)
    elo_data = []
    for player_name in players:
        try:
            player_model = FootballerEloModel(player_name)
            elo_rating = player_model.players_elo
            main_position = player_model.main_position
            name_parts = player_name.split('_')
            first_name = name_parts[0]
            second_name = " ".join(name_parts[1:])
            player_name_fpl = f"{first_name} {second_name}"
            cost = await get_player_cost(player_name_fpl)
            elo_data.append({
                'Player': player_name,
                'Position': main_position,
                'Elo': elo_rating,
                'Cost': cost
            })
            print(f"Processed {player_name}: Elo = {elo_rating}, Position = {main_position}, Cost = {cost}")
        except Exception as e:
            print(f"Error processing player {player_name}: {e}")
    elo_df = pd.DataFrame(elo_data)
    elo_df = elo_df.sort_values(by='Elo', ascending=False)
    elo_df.to_csv('initial_elo.csv', index=False)
    return elo_df


async def get_player_cost(player_name):
    async with aiohttp.ClientSession() as session:
        fpl = FPL(session)
        players = await fpl.get_players()
        for player in players:
            full_name = f"{player.first_name} {player.second_name}"
            if full_name.lower() == player_name.lower():
                print(f"{full_name} costs £{player.now_cost / 10}m")
                return player.now_cost / 10
        print(f"Player '{player_name}' not found.")
        return None

# Example usage:

import asyncio

if __name__ == "__main__":
    asyncio.run(all_players_elo())