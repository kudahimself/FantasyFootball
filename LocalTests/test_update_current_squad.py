import requests
import json

def test_update_current_squad(url, squad, csrf_token=None):
    headers = {'Content-Type': 'application/json'}
    if csrf_token:
        headers['X-CSRFToken'] = csrf_token
    resp = requests.post(url, headers=headers, data=json.dumps({'squad': squad}))
    try:
        return resp.status_code, resp.json()
    except Exception:
        return resp.status_code, resp.text

if __name__ == "__main__":
    # Example squad (names and positions must match your DB)
    squad = [
        {'name': 'Alisson', 'position': 'GKP'},
        {'name': 'Trent', 'position': 'DEF'},
        {'name': 'Salah', 'position': 'MID'},
        {'name': 'Haaland', 'position': 'FWD'}
    ]
    url = 'http://localhost:8000/api/update_current_squad/'
    status, result = test_update_current_squad(url, squad)
    print('Status:', status)
    print('Result:', result)
