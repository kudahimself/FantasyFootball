#!/usr/bin/env python3
"""
Test script to compare original vs optimized recalculate Elo functions.
"""

import requests
import json
import time

def test_both_versions():
    """
    Test both the original and optimized recalculate Elo functions.
    """
    
    print("="*70)
    print("COMPARING ORIGINAL VS OPTIMIZED RECALCULATE ELO FUNCTIONS")
    print("="*70)
    
    # Test parameters
    test_params = {
        'max_players': 10,  # Test with 10 players
        'batch_size': 5     # Small batch size
    }
    
    print(f"Testing with parameters: {test_params}")
    print()
    
    # Test original version
    print("1. Testing ORIGINAL version:")
    print("-" * 40)
    
    try:
        start_time = time.time()
        response = requests.post(
            'http://127.0.0.1:8000/api/recalculate_elos/',
            headers={'Content-Type': 'application/json'},
            data=json.dumps(test_params),
            timeout=60
        )
        original_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS: {result.get('message', 'No message')}")
            print(f"   Updated: {result.get('updated_count', 0)} players")
            print(f"   Time: {original_time:.4f} seconds")
            original_success = True
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"   Response: {response.text}")
            original_success = False
            original_time = float('inf')
            
    except requests.exceptions.Timeout:
        print("❌ TIMEOUT: Original version took too long")
        original_success = False
        original_time = float('inf')
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        original_success = False
        original_time = float('inf')
    
    print()
    
    # Test optimized version
    print("2. Testing OPTIMIZED version:")
    print("-" * 40)
    
    try:
        start_time = time.time()
        response = requests.post(
            'http://127.0.0.1:8000/api/recalculate_elos_optimized/',
            headers={'Content-Type': 'application/json'},
            data=json.dumps(test_params),
            timeout=60
        )
        optimized_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS: {result.get('message', 'No message')}")
            print(f"   Updated: {result.get('updated_count', 0)} players")
            print(f"   Time: {optimized_time:.4f} seconds")
            print(f"   Method: {result.get('method', 'unknown')}")
            optimized_success = True
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"   Response: {response.text}")
            optimized_success = False
            optimized_time = float('inf')
            
    except requests.exceptions.Timeout:
        print("❌ TIMEOUT: Optimized version took too long")
        optimized_success = False
        optimized_time = float('inf')
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        optimized_success = False
        optimized_time = float('inf')
    
    print()
    
    # Comparison
    print("3. PERFORMANCE COMPARISON:")
    print("-" * 40)
    
    if original_success and optimized_success:
        speedup = original_time / optimized_time if optimized_time > 0 else float('inf')
        print(f"Original time:   {original_time:.4f} seconds")
        print(f"Optimized time:  {optimized_time:.4f} seconds")
        print(f"Speedup:         {speedup:.2f}x faster")
        
        if speedup > 1.5:
            print(f"🎉 OPTIMIZATION SUCCESS! {speedup:.2f}x speedup achieved!")
        elif speedup > 1.0:
            print(f"✅ Slight improvement: {speedup:.2f}x speedup")
        else:
            print(f"⚠️  No significant improvement: {speedup:.2f}x")
    else:
        print("❌ Cannot compare - one or both functions failed")
        if not original_success:
            print("   Original function failed")
        if not optimized_success:
            print("   Optimized function failed")
    
    print()
    print("="*70)
    
    return original_success and optimized_success


def test_large_batch():
    """
    Test with a larger number of players to see the real performance difference.
    """
    print("TESTING WITH LARGER DATASET:")
    print("-" * 40)
    
    # Test parameters for larger batch
    test_params = {
        'max_players': 50,  # Test with 50 players
        'batch_size': 25    # Larger batch size
    }
    
    print(f"Testing optimized version with {test_params['max_players']} players...")
    
    try:
        start_time = time.time()
        response = requests.post(
            'http://127.0.0.1:8000/api/recalculate_elos_optimized/',
            headers={'Content-Type': 'application/json'},
            data=json.dumps(test_params),
            timeout=120  # 2 minute timeout
        )
        processing_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS: Processed {result.get('updated_count', 0)} of {result.get('total_players', 0)} players")
            print(f"   Time: {processing_time:.4f} seconds")
            print(f"   Rate: {result.get('updated_count', 0) / processing_time:.2f} players/second")
            return True
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False


if __name__ == "__main__":
    # Test both versions with small dataset
    success = test_both_versions()
    
    if success:
        print("\n" + "="*70)
        proceed = input("Test optimized version with 50 players? (y/N): ")
        if proceed.lower() == 'y':
            test_large_batch()
    
    print("\n✨ Testing complete!")