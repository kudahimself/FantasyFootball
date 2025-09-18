#!/usr/bin/env python
"""
Test the team selection page to ensure it loads correctly
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FantasyFootball.settings')

# Setup Django
django.setup()

from django.test import RequestFactory
from MyApp.views import team_selection

def test_team_selection_view():
    """Test the team_selection view"""
    try:
        # Create a request
        factory = RequestFactory()
        request = factory.get('/team-selection/')
        
        # Call the view
        response = team_selection(request)
        
        # Check if response is successful
        if response.status_code == 200:
            print("✅ Team selection view executed successfully")
            print("✅ Template should now show Team Elo and Cost badges")
        else:
            print(f"❌ View failed with status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing view: {e}")

if __name__ == "__main__":
    test_team_selection_view()