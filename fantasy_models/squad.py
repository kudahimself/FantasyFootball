



import pandas as pd
from pulp import LpProblem, LpVariable, lpSum, LpMaximize, LpBinary, LpStatus, value


class SquadSelector:
    def __init__(self, csv_path="elo_ratings.csv"):
        self.csv_path = csv_path
        self.df = pd.read_csv(self.csv_path)
        self.df['Elo'] = self.df['Elo'].astype(float)
        self.df['Cost'] = self.df['Cost'].astype(float)

    def get_top_players(self, position, n=10):
        return self.df[self.df['Position'] == position].nlargest(n, 'Elo')
    def select_top_n_squads(self, budget=82.5, attacker_count=3, midfielder_count=4, defender_count=3, keeper_count=1, top_n=4):
        gks = self.get_top_players('Keeper', 10)
        defs = self.get_top_players('Defender', 40)
        mids = self.get_top_players('Midfielder', 40)
        atts = self.get_top_players('Attacker', 40)
        squad_df = pd.concat([gks, defs, mids, atts], ignore_index=True)

        squads = []
        used_players = set()

        for _ in range(top_n):
            # Only use players not already selected
            available_idx = [i for i in range(len(squad_df)) if squad_df.loc[i, "Player"] not in used_players]
            if len(available_idx) < (keeper_count + defender_count + midfielder_count + attacker_count):
                break

            choices = [LpVariable(f"player_{i}", cat=LpBinary) for i in available_idx]
            prob = LpProblem("FPL_Squad_Selection", LpMaximize)
            prob += lpSum([choices[j] * squad_df.loc[available_idx[j], "Elo"] for j in range(len(available_idx))])
            prob += lpSum([choices[j] * squad_df.loc[available_idx[j], "Cost"] for j in range(len(available_idx))]) <= budget
            prob += lpSum([choices[j] for j in range(len(available_idx)) if squad_df.loc[available_idx[j], "Position"] == "Keeper"]) == keeper_count
            prob += lpSum([choices[j] for j in range(len(available_idx)) if squad_df.loc[available_idx[j], "Position"] == "Defender"]) == defender_count
            prob += lpSum([choices[j] for j in range(len(available_idx)) if squad_df.loc[available_idx[j], "Position"] == "Midfielder"]) == midfielder_count
            prob += lpSum([choices[j] for j in range(len(available_idx)) if squad_df.loc[available_idx[j], "Position"] == "Attacker"]) == attacker_count

            prob.solve()
            selected = [available_idx[j] for j in range(len(available_idx)) if choices[j].varValue == 1]
            if not selected:
                break
            used_players.update(squad_df.loc[selected, "Player"])
            result = squad_df.iloc[selected]
            squads.append(result)

        for idx, squad in enumerate(squads, 1):
            print(f"\nSquad {idx}:")
            print(f"Total Cost: {squad['Cost'].sum()} million")
            print(f"Total Elo: {squad['Elo'].sum()}")
            print(squad)
        return squads

# Example usage:
squad = SquadSelector('elo_ratings2.csv')
squad.select_top_n_squads()
