import pandas as pd
from pulp import LpProblem, LpVariable, lpSum, LpMaximize, LpBinary
from MyApi.models import Player, ProjectedPoints, SystemSettings


class SquadSelector:
    def __init__(self, formation='3-4-3'):
        # Get current week from system settings
        self.current_week = SystemSettings.get_settings().current_gameweek
        self.formation = formation
        self.position_counts = self.get_position_counts(formation)

    def get_position_counts(self, formation):
        formation_map = {
            '3-4-3': {'keeper': 1, 'defender': 3, 'midfielder': 4, 'attacker': 3},
            '3-5-2': {'keeper': 1, 'defender': 3, 'midfielder': 5, 'attacker': 2},
            '4-4-2': {'keeper': 1, 'defender': 4, 'midfielder': 4, 'attacker': 2},
            '4-3-3': {'keeper': 1, 'defender': 4, 'midfielder': 3, 'attacker': 3},
        }
        return formation_map.get(formation, formation_map['3-4-3'])

    def get_top_players(self, position, n=10):
        # Query top n players by ELO for the current week and position
        qs = Player.objects.filter(position=position, week=self.current_week).order_by('-elo')[:n]
        # Convert queryset to DataFrame for optimization
        df = pd.DataFrame([
            {
                'Player': p.name,
                'Position': p.position,
                'Elo': float(p.elo),
                'Cost': float(p.cost)
            } for p in qs
        ])
        return df

    def select_top_n_squads(self, budget=82.5, top_n=4):
        counts = self.position_counts
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
            if len(available_idx) < (counts['keeper'] + counts['defender'] + counts['midfielder'] + counts['attacker']):
                break

            choices = [LpVariable(f"player_{i}", cat=LpBinary) for i in available_idx]
            prob = LpProblem("FPL_Squad_Selection", LpMaximize)
            prob += lpSum([choices[j] * squad_df.loc[available_idx[j], "Elo"] for j in range(len(available_idx))])
            prob += lpSum([choices[j] * squad_df.loc[available_idx[j], "Cost"] for j in range(len(available_idx))]) <= budget
            prob += lpSum([choices[j] for j in range(len(available_idx)) if squad_df.loc[available_idx[j], "Position"] == "Keeper"]) == counts['keeper']
            prob += lpSum([choices[j] for j in range(len(available_idx)) if squad_df.loc[available_idx[j], "Position"] == "Defender"]) == counts['defender']
            prob += lpSum([choices[j] for j in range(len(available_idx)) if squad_df.loc[available_idx[j], "Position"] == "Midfielder"]) == counts['midfielder']
            prob += lpSum([choices[j] for j in range(len(available_idx)) if squad_df.loc[available_idx[j], "Position"] == "Attacker"]) == counts['attacker']

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
            squad_dict = {}
            squad_dict["goalkeepers"] = ", ".join(squad[squad["Position"] == "Keeper"]["Player"])
            squad_dict["defenders"] = ", ".join(squad[squad["Position"] == "Defender"]["Player"])
            squad_dict["midfielders"] = ", ".join(squad[squad["Position"] == "Midfielder"]["Player"])
            squad_dict["attackers"] = ", ".join(squad[squad["Position"] == "Attacker"]["Player"])
            print(f"Squad {idx}: {squad_dict}")
        return squads

    def generate_squads(self):
        return self.select_top_n_squads()


class SquadSelectorPoints:
    def __init__(self, formation='3-4-3'):
        self.current_week = SystemSettings.get_settings().current_gameweek
        self.formation = formation
        self.position_counts = self.get_position_counts(formation)

    def get_position_counts(self, formation):
        formation_map = {
            '3-4-3': {'keeper': 1, 'defender': 3, 'midfielder': 4, 'attacker': 3},
            '3-5-2': {'keeper': 1, 'defender': 3, 'midfielder': 5, 'attacker': 2},
            '4-4-2': {'keeper': 1, 'defender': 4, 'midfielder': 4, 'attacker': 2},
            '4-3-3': {'keeper': 1, 'defender': 4, 'midfielder': 3, 'attacker': 3},
        }
        return formation_map.get(formation, formation_map['3-4-3'])

    def get_top_players(self, position, n=10):
        qs = Player.objects.filter(position=position, week=self.current_week)
        player_data = []
        for p in qs:
            # Get the sum of projected points for the next 3 fixtures
            projections = ProjectedPoints.objects.filter(player_name=p.name).order_by('gameweek')[:3]
            projected_points = sum(float(proj.adjusted_expected_points) for proj in projections) if projections else 0.0
            player_data.append({
                'Player': p.name,
                'Position': p.position,
                'ProjectedPoints': projected_points,
                'Cost': float(p.cost)
            })
        df = pd.DataFrame(player_data)
        return df.nlargest(n, 'ProjectedPoints')

    def select_top_n_squads(self, budget=82.5, top_n=4):
        counts = self.position_counts
        gks = self.get_top_players('Keeper', 10)
        defs = self.get_top_players('Defender', 40)
        mids = self.get_top_players('Midfielder', 40)
        atts = self.get_top_players('Attacker', 40)
        squad_df = pd.concat([gks, defs, mids, atts], ignore_index=True)

        squads = []
        used_players = set()

        for _ in range(top_n):
            available_idx = [i for i in range(len(squad_df)) if squad_df.loc[i, "Player"] not in used_players]
            if len(available_idx) < (counts['keeper'] + counts['defender'] + counts['midfielder'] + counts['attacker']):
                break

            choices = [LpVariable(f"player_{i}", cat=LpBinary) for i in available_idx]
            prob = LpProblem("FPL_Squad_Selection_Points", LpMaximize)
            prob += lpSum([choices[j] * squad_df.loc[available_idx[j], "ProjectedPoints"] for j in range(len(available_idx))])
            prob += lpSum([choices[j] * squad_df.loc[available_idx[j], "Cost"] for j in range(len(available_idx))]) <= budget
            prob += lpSum([choices[j] for j in range(len(available_idx)) if squad_df.loc[available_idx[j], "Position"] == "Keeper"]) == counts['keeper']
            prob += lpSum([choices[j] for j in range(len(available_idx)) if squad_df.loc[available_idx[j], "Position"] == "Defender"]) == counts['defender']
            prob += lpSum([choices[j] for j in range(len(available_idx)) if squad_df.loc[available_idx[j], "Position"] == "Midfielder"]) == counts['midfielder']
            prob += lpSum([choices[j] for j in range(len(available_idx)) if squad_df.loc[available_idx[j], "Position"] == "Attacker"]) == counts['attacker']

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
            print(f"Total Projected Points: {squad['ProjectedPoints'].sum()}")
            print(squad)
            squad_dict = {}
            squad_dict["goalkeepers"] = ", ".join(squad[squad["Position"] == "Keeper"]["Player"])
            squad_dict["defenders"] = ", ".join(squad[squad["Position"] == "Defender"]["Player"])
            squad_dict["midfielders"] = ", ".join(squad[squad["Position"] == "Midfielder"]["Player"])
            squad_dict["attackers"] = ", ".join(squad[squad["Position"] == "Attacker"]["Player"])
            print(f"Squad {idx}: {squad_dict}")
        return squads

    def generate_squads(self):
        return self.select_top_n_squads()



