import os
import sys
import django
import pandas as pd
from pulp import LpProblem, LpVariable, lpSum, LpMaximize, LpBinary, LpStatus, value

# Setup Django environment for standalone use
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    # Add the project root to the Python path
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(project_root)
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')
    django.setup()

from MyApi.models import Player


class SquadSelector:
    def __init__(self, week):
        self.week = week
        print(f"Loading Elo data from database for week: {week}")
        
        # Load data from database instead of CSV
        players_queryset = Player.objects.filter(week=week)
        
        if not players_queryset.exists():
            raise ValueError(f"No player data found for week {week}. Please import data first using: python manage.py import_elo_data --week {week}")
        
        # Convert Django QuerySet to pandas DataFrame for compatibility with existing code
        players_data = list(players_queryset.values(
            'name', 'position', 'elo', 'cost', 'team', 'competition'
        ))
        
        self.df = pd.DataFrame(players_data)
        
        # Rename columns to match the existing CSV format
        self.df = self.df.rename(columns={
            'name': 'Player',
            'position': 'Position',
            'elo': 'Elo',
            'cost': 'Cost',
            'team': 'Team',
            'competition': 'Comp'
        })
        
        # Ensure data types are correct
        self.df['Elo'] = self.df['Elo'].astype(float)
        self.df['Cost'] = self.df['Cost'].astype(float)
        
        print(f"Loaded {len(self.df)} players from database")

    def get_top_players(self, position, n=10):
        """
        Get top n players by position, ordered by Elo rating.
        """
        return self.df[self.df['Position'] == position].nlargest(n, 'Elo')
    
    def get_all_players_by_position(self, position):
        """
        Get all players for a specific position.
        """
        return self.df[self.df['Position'] == position].sort_values('Elo', ascending=False)
    
    def get_player_by_name(self, name):
        """
        Get a specific player by name.
        """
        player_data = self.df[self.df['Player'] == name]
        if len(player_data) > 0:
            return player_data.iloc[0]
        return None
    
    def select_top_n_squads(self, budget=82.5, attacker_count=3, midfielder_count=4, defender_count=3, keeper_count=1, top_n=4):
        """
        Generate multiple optimal squads using linear programming.
        """
        gks = self.get_top_players('Keeper', 10)
        defs = self.get_top_players('Defender', 40)
        mids = self.get_top_players('Midfielder', 40)
        atts = self.get_top_players('Attacker', 40)
        squad_df = pd.concat([gks, defs, mids, atts], ignore_index=True)

        squads = []
        used_players = set()

        for squad_num in range(top_n):
            # Only use players not already selected
            available_idx = [i for i in range(len(squad_df)) if squad_df.loc[i, "Player"] not in used_players]
            if len(available_idx) < (keeper_count + defender_count + midfielder_count + attacker_count):
                print(f"Not enough players available for squad {squad_num + 1}")
                break

            choices = [LpVariable(f"player_{i}", cat=LpBinary) for i in available_idx]
            prob = LpProblem(f"FPL_Squad_Selection_{squad_num + 1}", LpMaximize)
            
            # Objective: maximize total Elo
            prob += lpSum([choices[j] * squad_df.loc[available_idx[j], "Elo"] for j in range(len(available_idx))])
            
            # Constraints
            prob += lpSum([choices[j] * squad_df.loc[available_idx[j], "Cost"] for j in range(len(available_idx))]) <= budget
            prob += lpSum([choices[j] for j in range(len(available_idx)) if squad_df.loc[available_idx[j], "Position"] == "Keeper"]) == keeper_count
            prob += lpSum([choices[j] for j in range(len(available_idx)) if squad_df.loc[available_idx[j], "Position"] == "Defender"]) == defender_count
            prob += lpSum([choices[j] for j in range(len(available_idx)) if squad_df.loc[available_idx[j], "Position"] == "Midfielder"]) == midfielder_count
            prob += lpSum([choices[j] for j in range(len(available_idx)) if squad_df.loc[available_idx[j], "Position"] == "Attacker"]) == attacker_count

            # Solve the problem
            prob.solve()
            
            if prob.status != 1:  # 1 means optimal solution found
                print(f"Could not find optimal solution for squad {squad_num + 1}")
                break
                
            selected = [available_idx[j] for j in range(len(available_idx)) if choices[j].varValue == 1]
            if not selected:
                print(f"No players selected for squad {squad_num + 1}")
                break
                
            used_players.update(squad_df.loc[selected, "Player"])
            result = squad_df.iloc[selected]
            squads.append(result)

        # Print squad summaries
        for idx, squad in enumerate(squads, 1):
            print(f"\nSquad {idx}:")
            print(f"Total Cost: £{squad['Cost'].sum():.1f}m")
            print(f"Total Elo: {squad['Elo'].sum():.1f}")
            print(f"Average Elo: {squad['Elo'].mean():.1f}")
            
            # Print by position
            for position in ['Keeper', 'Defender', 'Midfielder', 'Attacker']:
                pos_players = squad[squad['Position'] == position]
                if len(pos_players) > 0:
                    print(f"\n{position}s:")
                    for _, player in pos_players.iterrows():
                        print(f"  {player['Player']} - £{player['Cost']}m - Elo: {player['Elo']:.1f}")

        return squads

    def generate_squads(self, attacker_count=3, midfielder_count=4, defender_count=3, keeper_count=1, top_n=4):
        """
        Generate squads and return them in the format expected by the web interface.
        Optionally specify formation counts; defaults to 4-3-3 (1-3-4-3 order GK-DEF-MID-ATT maps to params).
        """
        squads = self.select_top_n_squads(
            budget=82.5,
            attacker_count=attacker_count,
            midfielder_count=midfielder_count,
            defender_count=defender_count,
            keeper_count=keeper_count,
            top_n=top_n,
        )
        
        # Convert to the format expected by the frontend (list of squad objects)
        formatted_squads = []
        for idx, squad in enumerate(squads, 1):
            # Count players by position for the positions array
            gk_count = len(squad[squad['Position'] == 'Keeper'])
            def_count = len(squad[squad['Position'] == 'Defender'])
            mid_count = len(squad[squad['Position'] == 'Midfielder'])
            att_count = len(squad[squad['Position'] == 'Attacker'])
            
            squad_data = {
                'squad_number': idx,
                'positions': [gk_count, def_count, mid_count, att_count],
                'players': {
                    'goalkeepers': [],
                    'defenders': [],
                    'midfielders': [],
                    'forwards': []
                }
            }
            
            for _, player in squad.iterrows():
                player_data = {
                    'name': player['Player'],
                    'elo': player['Elo'],
                    'cost': player['Cost'],
                    'team': player.get('Team', 'Unknown')
                }
                
                if player['Position'] == 'Keeper':
                    squad_data['players']['goalkeepers'].append(player_data)
                elif player['Position'] == 'Defender':
                    squad_data['players']['defenders'].append(player_data)
                elif player['Position'] == 'Midfielder':
                    squad_data['players']['midfielders'].append(player_data)
                elif player['Position'] == 'Attacker':
                    squad_data['players']['forwards'].append(player_data)
            
            formatted_squads.append(squad_data)
        
        return formatted_squads