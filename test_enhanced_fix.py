#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from api_utils import get_fixtures_by_date
from datetime import date
import os

print("🔍 ENHANCED ANALYSIS FIX TEST")
print("=" * 50)

API_KEY = os.environ.get('API_KEY', 'test_key')
print(f"API Key: {'✅ Set' if API_KEY != 'test_key' else '❌ Not set'}")

try:
    fixtures, error = get_fixtures_by_date(API_KEY, 'https://v3.football.api-sports.io', [203], date.today())
    print(f"Fixtures count: {len(fixtures) if fixtures else 0}")
    
    if fixtures:
        first_fixture = fixtures[0]
        print(f"First fixture keys: {list(first_fixture.keys())}")
        print(f"Has 'teams' key: {'teams' in first_fixture}")
        
        if 'teams' in first_fixture:
            print("✅ Teams structure exists - Enhanced analysis should work!")
            teams = first_fixture['teams']
            print(f"Home team: {teams.get('home', {}).get('name', 'N/A')}")
            print(f"Away team: {teams.get('away', {}).get('name', 'N/A')}")
        else:
            print("❌ Teams structure missing - Need to fix API format")
    else:
        print(f"Error: {error}")
        
except Exception as e:
    print(f"Exception: {e}")