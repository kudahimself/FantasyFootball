import django
import os
import sys

# Setup Django environment
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')
django.setup()

from django.contrib.auth.models import User
from MyApi.models import UserSquad

def copy_gw8_to_gw6():
    users = User.objects.all()
    count = 0
    for user in users:
        gw8 = UserSquad.objects.filter(user=user, week=8).first()
        if not gw8:
            print(f"User {user.username}: No GW8 squad, skipping.")
            continue
        # Check if GW6 squad already exists
        if UserSquad.objects.filter(user=user, week=6).exists():
            print(f"User {user.username}: GW6 squad already exists, skipping.")
            continue
        squad = UserSquad(
            user=user,
            week=6,
            name="Gameweek 6 Squad",
            squad_data=gw8.squad_data
        )
        squad.save()
        print(f"User {user.username}: GW8 squad copied to GW6.")
        count += 1
    print(f"Done. {count} squads copied.")

if __name__ == "__main__":
    copy_gw8_to_gw6()
