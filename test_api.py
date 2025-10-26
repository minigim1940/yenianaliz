#!/usr/bin/env python3
"""
API-Football test script to debug team search
"""

import requests
import json

# Test direct API call
API_KEY = "your-key-here"  # Replace with actual key
BASE_URL = "https://v3.football.api-sports.io"

def test_api():
    headers = {
        'x-rapidapi-key': API_KEY,
        'x-rapidapi-host': "v3.football.api-sports.io"
    }
    
    # Test 1: Search for Juventus
    print("=== Testing Juventus Search ===")
    url = f"{BASE_URL}/teams"
    params = {'search': 'juventus'}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {response.headers}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response structure: {json.dumps(data, indent=2)[:500]}...")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

    # Test 2: Get Juventus by ID (496)
    print("\n=== Testing Juventus by ID ===")
    params = {'id': 496}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)[:300]}...")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_api()