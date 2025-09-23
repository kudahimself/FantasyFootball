# utils/squad_conversion.py
"""
Utility functions for converting frontend squad data to the format expected by CurrentSquad.squad
"""

def frontend_to_backend_squad(local_team):
    """
    Convert a flat list of player dicts (from frontend) to the grouped dict format expected by CurrentSquad.squad.
    Args:
        local_team (list): List of player dicts, each with at least 'name' and 'position'.
    Returns:
        dict: {'goalkeepers': [...], 'defenders': [...], 'midfielders': [...], 'forwards': [...]} (names only)
    """
    position_map = {
        'GKP': 'goalkeepers',
        'DEF': 'defenders',
        'MID': 'midfielders',
        'FWD': 'forwards',
        'Keeper': 'goalkeepers',
        'Defender': 'defenders',
        'Midfielder': 'midfielders',
        'Forward': 'forwards',
    }
    squad = {
        'goalkeepers': [],
        'defenders': [],
        'midfielders': [],
        'forwards': []
    }
    for player in local_team:
        pos = position_map.get(player.get('position'))
        if pos:
            # Only include relevant fields (id, name, position, team, cost, elo, etc.)
            player_obj = {k: v for k, v in player.items() if k in ['id', 'name', 'position', 'team', 'cost', 'elo', 'elo', 'projected_points']}
            # Normalize 'elo' to 'elo' for backend
            if 'elo' in player_obj and 'elo' not in player_obj:
                player_obj['elo'] = player_obj['elo']
            squad[pos].append(player_obj)
    return squad

# Example usage
if __name__ == "__main__":
    test_team = [
        {'name': 'Alisson', 'position': 'GKP'},
        {'name': 'Trent', 'position': 'DEF'},
        {'name': 'Salah', 'position': 'MID'},
        {'name': 'Haaland', 'position': 'FWD'}
    ]
    print(frontend_to_backend_squad(test_team))
