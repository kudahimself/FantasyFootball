import django
import os
import sys

# Setup Django environment
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')
django.setup()

from django.contrib.auth.models import User
from MyApi.models import CurrentSquad, UserSquad

def copy_current_to_gw6():
    users = User.objects.all()
    count = 0
    for user in users:
        try:
            current = CurrentSquad.objects.get(user=user)
            # Check if UserSquad for GW6 already exists
            if UserSquad.objects.filter(user=user, week=6).exists():
                print(f"User {user.username}: GW6 squad already exists, skipping.")
                continue
            squad = UserSquad(
                user=user,
                week=6,
                name="Gameweek 6 Squad",
                squad_data=current.squad_data
            )
            squad.save()
            print(f"User {user.username}: GW6 squad created.")
            count += 1
        except CurrentSquad.DoesNotExist:
            print(f"User {user.username}: No current squad, skipping.")
    print(f"Done. {count} squads created.")

if __name__ == "__main__":
    copy_current_to_gw6()
