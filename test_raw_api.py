#!/usr/bin/env python3
"""
Raw API response formatını kontrol eden test dosyası
"""

import requests

def test_raw_api():
    """Raw API response'unu kontrol et"""
    
    api_key = "6336fb21e17dea87880d3b133132a13f"
    base_url = "https://v3.football.api-sports.io/"
    
    headers = {
        'x-rapidapi-key': api_key,
        'x-rapidapi-host': 'v3.football.api-sports.io'
    }
    
    # Test team search
    print("🔍 Testing team search API...")
    url = f"{base_url}teams"
    params = {'search': 'Galatasaray'}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            json_response = response.json()
            print(f"Response keys: {json_response.keys()}")
            
            if 'response' in json_response:
                response_data = json_response['response']
                print(f"Response type: {type(response_data)}")
                print(f"Response length: {len(response_data) if isinstance(response_data, list) else 'Not a list'}")
                
                if isinstance(response_data, list) and len(response_data) > 0:
                    first_item = response_data[0]
                    print(f"First item type: {type(first_item)}")
                    print(f"First item keys: {first_item.keys() if isinstance(first_item, dict) else 'Not a dict'}")
                    
                    if isinstance(first_item, dict):
                        print(f"First item: {first_item}")
                        
                        # Check if 'team' key exists
                        if 'team' in first_item:
                            team_data = first_item['team']
                            print(f"Team data: {team_data}")
                        else:
                            print("No 'team' key found, first_item might be the team data directly")
            else:
                print("No 'response' key in JSON")
                print(f"Full response: {json_response}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {str(e)}")

if __name__ == "__main__":
    test_raw_api()