"""
Utility functions for recommending substitutes based on projected points optimization.
Uses PuLP linear programming to find optimal packages of 3-4 substitutions together.
"""

import json
import pulp
from django.db.models import Sum
from MyApi.models import Player, ProjectedPoints, SystemSettings, CurrentSquad


def get_current_squad_with_projected_points():
    """
    Get the current squad with projected points data for each player.
    
    Returns:
        dict: Current squad with projected points data
    """
    try:
        current_squad_instance = CurrentSquad.get_or_create_current_squad()
        current_squad = current_squad_instance.squad
        
        # Enrich each player with projected points data
        enriched_squad = {
            'goalkeepers': [],
            'defenders': [],
            'midfielders': [],
            'forwards': []
        }
        
        current_week = SystemSettings.get_current_gameweek()
        
        for position in ['goalkeepers', 'defenders', 'midfielders', 'forwards']:
            if position in current_squad:
                for player_data in current_squad[position]:
                    if isinstance(player_data, dict) and 'name' in player_data:
                        player_name = player_data['name']
                        
                        # Get projected points for this player
                        total_projected = ProjectedPoints.objects.filter(
                            player_name=player_name
                        ).aggregate(
                            total=Sum('adjusted_expected_points')
                        )['total'] or 0
                        
                        # Create enriched player data
                        enriched_player = player_data.copy()
                        enriched_player['projected_points'] = round(total_projected, 1)
                        enriched_squad[position].append(enriched_player)
        
        return enriched_squad
        
    except Exception as e:
        print(f"Error getting current squad with projected points: {e}")
        return {
            'goalkeepers': [],
            'defenders': [],
            'midfielders': [],
            'forwards': []
        }


def get_all_players_with_projected_points(exclude_current_squad=True):
    """
    Get all available players with their projected points data.
    
    Args:
        exclude_current_squad (bool): Whether to exclude current squad players
    
    Returns:
        list: List of all players with projected points, sorted by points descending
    """
    try:
        current_week = SystemSettings.get_current_gameweek()
        players = Player.objects.filter(week=current_week)
        
        # Get current squad player names if excluding them
        current_squad_players = set()
        if exclude_current_squad:
            current_squad_instance = CurrentSquad.get_or_create_current_squad()
            current_squad = current_squad_instance.squad
            
            for position in ['goalkeepers', 'defenders', 'midfielders', 'forwards']:
                if position in current_squad:
                    for player_data in current_squad[position]:
                        if isinstance(player_data, dict) and 'name' in player_data:
                            current_squad_players.add(player_data['name'])
        
        players_with_projections = []
        
        for player in players:
            # Skip if player is already in current squad (when excluding)
            if exclude_current_squad and player.name in current_squad_players:
                continue
                
            # Get total projected points for this player
            total_projected = ProjectedPoints.objects.filter(
                player_name=player.name
            ).aggregate(
                total=Sum('adjusted_expected_points')
            )['total'] or 0
            
            players_with_projections.append({
                'name': player.name,
                'position': player.position,
                'team': player.team,
                'cost': player.cost,
                'elo': player.elo,
                'projected_points': round(total_projected, 1)
            })
        
        # Sort by projected points (descending)
        players_with_projections.sort(key=lambda x: x['projected_points'], reverse=True)
        
        return players_with_projections
        
    except Exception as e:
        print(f"Error getting players with projected points: {e}")
        return []


def detect_formation_from_squad(current_squad):
    """
    Detect the formation from the current squad structure.
    
    Args:
        current_squad (dict): Current squad data
        
    Returns:
        str: Formation string (e.g., '3-4-3')
    """
    try:
        gk_count = len(current_squad.get('goalkeepers', []))
        def_count = len(current_squad.get('defenders', []))
        mid_count = len(current_squad.get('midfielders', []))
        fwd_count = len(current_squad.get('forwards', []))
        
        formation_string = f"{def_count}-{mid_count}-{fwd_count}"
        
        # Validate against known formations
        valid_formations = ['3-4-3', '3-5-2', '4-4-2', '4-3-3']
        if formation_string in valid_formations:
            return formation_string
        else:
            # Default to 3-4-3 if unknown formation
            return '3-4-3'
            
    except Exception as e:
        print(f"Error detecting formation: {e}")
        return '3-4-3'


def calculate_squad_total_projected_points(squad):
    """
    Calculate the total projected points for a squad.
    
    Args:
        squad (dict): Squad data with players containing projected_points
        
    Returns:
        float: Total projected points for the squad
    """
    total_points = 0
    
    for position in ['goalkeepers', 'defenders', 'midfielders', 'forwards']:
        if position in squad:
            for player in squad[position]:
                if isinstance(player, dict) and 'projected_points' in player:
                    total_points += player['projected_points']
    
    return round(total_points, 1)


def find_substitute_candidates(current_squad, all_players, position_to_improve):
    """
    Find potential substitute candidates for a specific position.
    Only considers players NOT already in the current squad.
    
    Args:
        current_squad (dict): Current squad with projected points
        all_players (list): All available players with projected points (excluding current squad)
        position_to_improve (str): Position to find substitutes for
        
    Returns:
        list: List of substitute candidates with improvement data
    """
    position_mapping = {
        'goalkeepers': 'Keeper',
        'defenders': 'Defender', 
        'midfielders': 'Midfielder',
        'forwards': 'Attacker'
    }
    
    player_position = position_mapping.get(position_to_improve)
    if not player_position:
        return []
    
    # Get current players in this position
    current_players = current_squad.get(position_to_improve, [])
    
    # Get all current squad player names (across all positions) to ensure we don't recommend them
    all_current_player_names = set()
    for pos in ['goalkeepers', 'defenders', 'midfielders', 'forwards']:
        for player in current_squad.get(pos, []):
            if isinstance(player, dict) and 'name' in player:
                all_current_player_names.add(player['name'])
    
    # Find available players for this position (excluding ALL current squad members)
    available_players = [
        p for p in all_players 
        if p['position'] == player_position and p['name'] not in all_current_player_names
    ]
    
    substitute_candidates = []
    
    # For each current player in this position, find better alternatives
    for current_player in current_players:
        if not isinstance(current_player, dict):
            continue
            
        current_points = current_player.get('projected_points', 0)
        current_cost = current_player.get('cost', 0)
        current_name = current_player.get('name', '')
        
        # Find players with higher projected points
        for candidate in available_players:
            if candidate['projected_points'] > current_points:
                improvement = candidate['projected_points'] - current_points
                cost_diff = candidate['cost'] - current_cost
                efficiency = improvement / max(abs(cost_diff), 0.1) if cost_diff != 0 else improvement * 10
                
                substitute_candidates.append({
                    'current_player': current_player,
                    'substitute': candidate,
                    'improvement': round(improvement, 1),
                    'cost_difference': round(cost_diff, 1),
                    'efficiency': round(efficiency, 2),
                    'position': position_to_improve,
                    'swap_description': f"Replace {current_name} with {candidate['name']}"
                })
    
    # Sort by improvement potential
    substitute_candidates.sort(key=lambda x: x['improvement'], reverse=True)
    
    return substitute_candidates


def recommend_substitutes_test(max_recommendations=4, budget_constraint=100.0):
    """
    Optimized function to recommend a package of 3-4 substitutes using PuLP linear programming.
    Finds the best combination of substitutions that maximizes points within budget constraints.
    
    Args:
        max_recommendations (int): Target number of substitutes (3-4)
        budget_constraint (float): Maximum budget for the squad (82.5)
        
    Returns:
        dict: Recommendation data including optimal substitution package
    """
    try:
        # Get current squad with projected points
        current_squad = get_current_squad_with_projected_points()
        
        # Get all available players (excluding current squad players)
        all_players = get_all_players_with_projected_points(exclude_current_squad=True)
        
        # Detect current formation
        current_formation = detect_formation_from_squad(current_squad)
        
        # Calculate current squad stats
        current_total_points = calculate_squad_total_projected_points(current_squad)
        current_total_cost = 0
        current_squad_players = {}  # Dict mapping position to list of players
        
        for position in ['goalkeepers', 'defenders', 'midfielders', 'forwards']:
            current_squad_players[position] = []
            for player in current_squad.get(position, []):
                if isinstance(player, dict) and 'cost' in player:
                    current_total_cost += player['cost']
                    current_squad_players[position].append(player)
        
        # Build optimization problem using PuLP
        prob = pulp.LpProblem("Squad_Optimization", pulp.LpMaximize)
        
        # Decision variables: for each current player and each potential substitute
        substitution_vars = {}  # (current_player_name, substitute_name): binary variable
        current_player_vars = {}  # current_player_name: binary variable (1 if kept, 0 if substituted)
        
        # Create variables for each possible substitution
        substitution_options = []
        
        for position in ['goalkeepers', 'defenders', 'midfielders', 'forwards']:
            position_mapping = {
                'goalkeepers': 'Keeper',
                'defenders': 'Defender', 
                'midfielders': 'Midfielder',
                'forwards': 'Attacker'
            }
            
            player_position = position_mapping.get(position)
            if not player_position:
                continue
                
            # Get available substitutes for this position
            available_substitutes = [
                p for p in all_players 
                if p['position'] == player_position
            ]
            
            # For each current player in this position
            for current_player in current_squad_players[position]:
                current_name = current_player.get('name', '')
                if not current_name:
                    continue
                    
                # Create variable for keeping this player
                current_player_vars[current_name] = pulp.LpVariable(
                    f"keep_{current_name.replace(' ', '_')}", 
                    cat='Binary'
                )
                
                # Create variables for substituting this player
                for substitute in available_substitutes:
                    substitute_name = substitute['name']
                    
                    # Only consider substitutions that improve points
                    if substitute['projected_points'] > current_player.get('projected_points', 0):
                        var_name = f"sub_{current_name.replace(' ', '_')}_with_{substitute_name.replace(' ', '_')}"
                        substitution_vars[(current_name, substitute_name)] = pulp.LpVariable(
                            var_name, 
                            cat='Binary'
                        )
                        
                        substitution_options.append({
                            'current_player': current_player,
                            'substitute': substitute,
                            'position': position,
                            'improvement': substitute['projected_points'] - current_player.get('projected_points', 0),
                            'cost_difference': substitute['cost'] - current_player.get('cost', 0),
                            'var': substitution_vars[(current_name, substitute_name)]
                        })
        
        # Objective: Maximize total point improvement
        prob += pulp.lpSum([
            option['improvement'] * option['var'] 
            for option in substitution_options
        ])
        
        # Constraints
        
        # 1. Each current player can only be kept OR substituted (not both)
        for current_name in current_player_vars:
            # Find all substitution variables for this player
            player_substitutions = [
                substitution_vars[(curr, sub)] 
                for (curr, sub) in substitution_vars.keys() 
                if curr == current_name
            ]
            
            if player_substitutions:
                prob += current_player_vars[current_name] + pulp.lpSum(player_substitutions) == 1
            else:
                # If no substitutions available, player must be kept
                prob += current_player_vars[current_name] == 1
        
        # 2. Budget constraint
        total_cost_expr = 0
        
        # Add cost of kept players
        for current_name in current_player_vars:
            # Find the current player's cost
            player_cost = 0
            for position in current_squad_players:
                for player in current_squad_players[position]:
                    if player.get('name') == current_name:
                        player_cost = player.get('cost', 0)
                        break
                if player_cost > 0:
                    break
            
            total_cost_expr += player_cost * current_player_vars[current_name]
        
        # Add cost of substitutes
        for option in substitution_options:
            substitute_cost = option['substitute']['cost']
            total_cost_expr += substitute_cost * option['var']
        
        prob += total_cost_expr <= budget_constraint
        
        # 3. Formation constraints (maintain same formation)
        formation_requirements = {
            'goalkeepers': 1,
            'defenders': int(current_formation.split('-')[0]),
            'midfielders': int(current_formation.split('-')[1]),
            'forwards': int(current_formation.split('-')[2])
        }
        
        for position in ['goalkeepers', 'defenders', 'midfielders', 'forwards']:
            required_count = formation_requirements[position]
            
            # Count kept players in this position
            kept_players_expr = pulp.lpSum([
                current_player_vars[player.get('name', '')] 
                for player in current_squad_players[position]
                if player.get('name', '') in current_player_vars
            ])
            
            # Count substituted players in this position
            substituted_players_expr = pulp.lpSum([
                option['var'] 
                for option in substitution_options
                if option['position'] == position
            ])
            
            prob += kept_players_expr + substituted_players_expr == required_count
        
        # 4. Limit number of substitutions to 3-4
        total_substitutions = pulp.lpSum([option['var'] for option in substitution_options])
        prob += total_substitutions >= 3
        prob += total_substitutions <= max_recommendations
        
        # 5. No duplicate substitute players constraint
        # Each substitute player can only be selected once across all positions
        substitute_player_usage = {}
        for option in substitution_options:
            substitute_name = option['substitute']['name']
            if substitute_name not in substitute_player_usage:
                substitute_player_usage[substitute_name] = []
            substitute_player_usage[substitute_name].append(option['var'])
        
        # Add constraint: each substitute player can be used at most once
        for substitute_name, variables in substitute_player_usage.items():
            if len(variables) > 1:  # Only add constraint if player appears multiple times
                prob += pulp.lpSum(variables) <= 1
        
        # Solve the optimization problem
        prob.solve(pulp.PULP_CBC_CMD(msg=0))
        
        # Extract results
        recommended_substitutes = []
        total_improvement = 0
        total_cost_change = 0
        
        if prob.status == pulp.LpStatusOptimal:
            for option in substitution_options:
                if option['var'].varValue == 1:  # This substitution is selected
                    recommended_substitutes.append({
                        'current_player': option['current_player'],
                        'substitute': option['substitute'],
                        'improvement': round(option['improvement'], 1),
                        'cost_difference': round(option['cost_difference'], 1),
                        'position': option['position'],
                        'swap_description': f"Replace {option['current_player']['name']} with {option['substitute']['name']}"
                    })
                    total_improvement += option['improvement']
                    total_cost_change += option['cost_difference']
        
        available_budget = budget_constraint - current_total_cost - total_cost_change
        
        return {
            'success': True,
            'optimization_status': 'optimal' if prob.status == pulp.LpStatusOptimal else 'suboptimal',
            'current_squad': current_squad,
            'current_formation': current_formation,
            'current_total_points': current_total_points,
            'current_total_cost': round(current_total_cost, 1),
            'budget_constraint': budget_constraint,
            'available_budget': round(available_budget, 1),
            'recommended_substitutes': recommended_substitutes,
            'total_potential_improvement': round(total_improvement, 1),
            'projected_new_total': round(current_total_points + total_improvement, 1),
            'total_cost_change': round(total_cost_change, 1),
            'number_of_recommendations': len(recommended_substitutes),
            'package_optimization': True,
            'verification': {
                'budget_respected': (current_total_cost + total_cost_change) <= budget_constraint,
                'formation_maintained': current_formation,
                'substitution_count': len(recommended_substitutes)
            }
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Failed to generate optimized substitute recommendations: {str(e)}',
            'current_squad': {},
            'recommended_substitutes': [],
            'package_optimization': True
        }


def analyze_squad_weaknesses_test(current_squad=None):
    """
    Test function to analyze weaknesses in the current squad.
    
    Args:
        current_squad (dict, optional): Squad to analyze, defaults to current squad
        
    Returns:
        dict: Analysis of squad weaknesses and improvement areas
    """
    try:
        if current_squad is None:
            current_squad = get_current_squad_with_projected_points()
        
        analysis = {
            'position_analysis': {},
            'overall_strength': 'Unknown',
            'weakest_positions': [],
            'strongest_positions': [],
            'improvement_suggestions': []
        }
        
        # Analyze each position
        for position in ['goalkeepers', 'defenders', 'midfielders', 'forwards']:
            players = current_squad.get(position, [])
            
            if players:
                total_points = sum(p.get('projected_points', 0) for p in players if isinstance(p, dict))
                avg_points = total_points / len(players)
                total_cost = sum(p.get('cost', 0) for p in players if isinstance(p, dict))
                
                analysis['position_analysis'][position] = {
                    'player_count': len(players),
                    'total_projected_points': round(total_points, 1),
                    'average_projected_points': round(avg_points, 1),
                    'total_cost': round(total_cost, 1),
                    'efficiency': round(total_points / max(total_cost, 0.1), 2)
                }
            else:
                analysis['position_analysis'][position] = {
                    'player_count': 0,
                    'total_projected_points': 0,
                    'average_projected_points': 0,
                    'total_cost': 0,
                    'efficiency': 0
                }
        
        # Determine strongest and weakest positions
        positions_by_efficiency = sorted(
            analysis['position_analysis'].items(),
            key=lambda x: x[1]['efficiency'],
            reverse=True
        )
        
        analysis['strongest_positions'] = [pos[0] for pos in positions_by_efficiency[:2]]
        analysis['weakest_positions'] = [pos[0] for pos in positions_by_efficiency[-2:]]
        
        # Overall strength assessment
        total_squad_points = sum(
            pos_data['total_projected_points'] 
            for pos_data in analysis['position_analysis'].values()
        )
        
        if total_squad_points >= 80:
            analysis['overall_strength'] = 'Strong'
        elif total_squad_points >= 60:
            analysis['overall_strength'] = 'Average'
        else:
            analysis['overall_strength'] = 'Weak'
        
        # Generate improvement suggestions
        for position in analysis['weakest_positions']:
            pos_data = analysis['position_analysis'][position]
            if pos_data['efficiency'] < 1.0:
                analysis['improvement_suggestions'].append(
                    f"Consider upgrading {position} - current efficiency: {pos_data['efficiency']}"
                )
        
        return analysis
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Failed to analyze squad: {str(e)}',
            'position_analysis': {},
            'improvement_suggestions': []
        }


def simulate_substitution_impact_test(substitutions):
    """
    Test function to simulate the impact of proposed substitutions.
    
    Args:
        substitutions (list): List of substitution dicts with current_player and substitute
        
    Returns:
        dict: Impact analysis of the substitutions
    """
    try:
        current_squad = get_current_squad_with_projected_points()
        
        # Create a copy of the squad for simulation
        simulated_squad = json.loads(json.dumps(current_squad))
        
        total_points_improvement = 0
        total_cost_change = 0
        successful_substitutions = []
        
        for substitution in substitutions:
            current_player = substitution['current_player']
            substitute = substitution['substitute']
            position = substitution['position']
            
            # Find and replace the player in the simulated squad
            position_players = simulated_squad.get(position, [])
            
            for i, player in enumerate(position_players):
                if isinstance(player, dict) and player.get('name') == current_player['name']:
                    # Replace with substitute
                    position_players[i] = {
                        'name': substitute['name'],
                        'team': substitute['team'],
                        'cost': substitute['cost'],
                        'elo': substitute['elo'],
                        'projected_points': substitute['projected_points'],
                        'position': substitute['position']
                    }
                    
                    # Track changes
                    points_improvement = substitute['projected_points'] - current_player.get('projected_points', 0)
                    cost_change = substitute['cost'] - current_player.get('cost', 0)
                    
                    total_points_improvement += points_improvement
                    total_cost_change += cost_change
                    
                    successful_substitutions.append({
                        'position': position,
                        'out': current_player['name'],
                        'in': substitute['name'],
                        'points_improvement': round(points_improvement, 1),
                        'cost_change': round(cost_change, 1)
                    })
                    break
        
        # Calculate new totals
        original_total_points = calculate_squad_total_projected_points(current_squad)
        new_total_points = calculate_squad_total_projected_points(simulated_squad)
        
        return {
            'success': True,
            'original_total_points': original_total_points,
            'new_total_points': new_total_points,
            'total_points_improvement': round(total_points_improvement, 1),
            'total_cost_change': round(total_cost_change, 1),
            'successful_substitutions': successful_substitutions,
            'simulated_squad': simulated_squad,
            'improvement_percentage': round((total_points_improvement / max(original_total_points, 1)) * 100, 1)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Failed to simulate substitution impact: {str(e)}',
            'total_points_improvement': 0,
            'successful_substitutions': []
        }
