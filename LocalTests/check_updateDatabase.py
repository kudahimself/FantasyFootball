import requests
import json

def check_update_database_squad(url, player, action, csrf_token=None):
    """
    Test the updateDatabaseSquad logic from the frontend in Python.
    Args:
        url (str): The endpoint URL (e.g., '/add_player/' or '/remove_player/')
        player (dict): Player dict with at least 'name' and 'position'
        action (str): 'add' or 'remove'
        csrf_token (str, optional): CSRF token if required
    Returns:
        dict: Response JSON or error info
    """
    position_mapping = {
        'GKP': 'goalkeepers',
        'DEF': 'defenders',
        'MID': 'midfielders',
        'FWD': 'forwards'
    }
    db_position = position_mapping.get(player.get('position'))
    if not db_position:
        return {'error': f'Unknown position: {player.get("position")}', 'success': False}
    data = {
        'position': db_position,
        'player_name': player.get('name')
    }
    headers = {'Content-Type': 'application/json'}
    if csrf_token:
        headers['X-CSRFToken'] = csrf_token
    try:
        resp = requests.post(url, headers=headers, data=json.dumps(data))
        content_type = resp.headers.get('content-type', '')
        if 'application/json' in content_type:
            return resp.json()
        else:
            return {'error': f'Non-JSON response: {resp.text[:200]}', 'success': False}
    except Exception as e:
        return {'error': str(e), 'success': False}

# Example usage:
if __name__ == "__main__":
    # Example player
    player = {'name': 'John Doe', 'position': 'MID'}
    # Example: test add
    print(check_update_database_squad('http://localhost:8000/add_player/', player, 'add'))
    # Example: test remove
    print(check_update_database_squad('http://localhost:8000/remove_player/', player, 'remove'))
