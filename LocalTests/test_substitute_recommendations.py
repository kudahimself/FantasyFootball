"""
Test script for substitute recommendation utility functions.
This script demonstrates how to use the new substitute recommendation functions.

Usage:
1. Run the Django server: python manage.py runserver
2. Execute this script: python test_substitute_recommendations.py
3. Or use the API endpoints directly

API Endpoints (all are test endpoints that don't affect existing functionality):
- POST /api/test/recommend_substitutes/ - Get substitute recommendations
- GET /api/test/analyze_squad/ - Analyze current squad weaknesses  
- POST /api/test/simulate_substitutions/ - Simulate substitution impact

Example API calls:
1. Get recommendations:
   POST /api/test/recommend_substitutes/
   Body: {"max_recommendations": 4, "budget_constraint": 100.0}

2. Analyze squad:
   GET /api/test/analyze_squad/

3. Simulate substitutions:
   POST /api/test/simulate_substitutions/
   Body: {"substitutions": [{"current_player": {...}, "substitute": {...}, "position": "defenders"}]}
"""

import requests
import json

def test_substitute_recommendations():
    """Test the substitute recommendation functionality."""
    
    base_url = "http://localhost:8000"  # Adjust if your server runs on different port
    
    print("=" * 60)
    print("TESTING SUBSTITUTE RECOMMENDATION UTILITY FUNCTIONS")
    print("=" * 60)
    
    # Test 1: Get substitute recommendations
    print("\n1. Testing substitute recommendations...")
    try:
        response = requests.post(
            f"{base_url}/api/test/recommend_substitutes/",
            json={
                "max_recommendations": 4,
                "budget_constraint": 100.0
            },
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Substitute recommendations retrieved successfully!")
                print(f"Current total points: {data.get('current_total_points', 0)}")
                print(f"Potential improvement: +{data.get('total_potential_improvement', 0)} points")
                print(f"Number of recommendations: {data.get('number_of_recommendations', 0)}")
                
                for i, sub in enumerate(data.get('recommended_substitutes', [])[:3]):
                    print(f"  Recommendation {i+1}: {sub['current_player']['name']} → {sub['substitute']['name']} (+{sub['improvement']} pts)")
            else:
                print(f"❌ Error: {data.get('error', 'Unknown error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
    
    # Test 2: Analyze squad weaknesses
    print("\n2. Testing squad analysis...")
    try:
        response = requests.get(f"{base_url}/api/test/analyze_squad/")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success', True):  # Analyze function doesn't use success field
                print("✅ Squad analysis completed successfully!")
                print(f"Overall strength: {data.get('overall_strength', 'Unknown')}")
                print(f"Strongest positions: {', '.join(data.get('strongest_positions', []))}")
                print(f"Weakest positions: {', '.join(data.get('weakest_positions', []))}")
                
                if data.get('improvement_suggestions'):
                    print("Suggestions:")
                    for suggestion in data.get('improvement_suggestions', [])[:2]:
                        print(f"  • {suggestion}")
            else:
                print(f"❌ Error: {data.get('error', 'Unknown error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
    
    # Test 3: Simulate substitutions (example with dummy data)
    print("\n3. Testing substitution simulation...")
    try:
        # First get recommendations to use for simulation
        rec_response = requests.post(
            f"{base_url}/api/test/recommend_substitutes/",
            json={"max_recommendations": 2},
            headers={'Content-Type': 'application/json'}
        )
        
        if rec_response.status_code == 200:
            rec_data = rec_response.json()
            if rec_data.get('success') and rec_data.get('recommended_substitutes'):
                # Use first recommendation for simulation
                first_rec = rec_data['recommended_substitutes'][0]
                
                simulation_data = {
                    "substitutions": [{
                        "current_player": first_rec['current_player'],
                        "substitute": first_rec['substitute'],
                        "position": first_rec['position']
                    }]
                }
                
                sim_response = requests.post(
                    f"{base_url}/api/test/simulate_substitutions/",
                    json=simulation_data,
                    headers={'Content-Type': 'application/json'}
                )
                
                if sim_response.status_code == 200:
                    sim_data = sim_response.json()
                    if sim_data.get('success'):
                        print("✅ Substitution simulation completed successfully!")
                        print(f"Original points: {sim_data.get('original_total_points', 0)}")
                        print(f"New points: {sim_data.get('new_total_points', 0)}")
                        print(f"Improvement: +{sim_data.get('total_points_improvement', 0)} points")
                        print(f"Cost change: £{sim_data.get('total_cost_change', 0)}m")
                    else:
                        print(f"❌ Simulation error: {sim_data.get('error', 'Unknown error')}")
                else:
                    print(f"❌ Simulation HTTP Error: {sim_response.status_code}")
            else:
                print("⚠️ No recommendations available for simulation test")
        else:
            print("⚠️ Could not get recommendations for simulation test")
            
    except Exception as e:
        print(f"❌ Simulation connection error: {e}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    print("\nNOTE: These are test functions and do not affect existing functionality.")
    print("To integrate into your app, use the utility functions in MyApi/utils/recommend_substitutes.py")


if __name__ == "__main__":
    test_substitute_recommendations()