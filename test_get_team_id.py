#!/usr/bin/env python3
"""
get_team_id fonksiyonunu debug etmek için test dosyası
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from api_utils import get_team_id

def test_get_team_id():
    """get_team_id fonksiyonunu test et"""
    
    api_key = "6336fb21e17dea87880d3b133132a13f"
    base_url = "https://v3.football.api-sports.io/"
    
    test_teams = ["Galatasaray", "Barcelona", "Real Madrid"]
    
    for team_name in test_teams:
        print(f"\n🔍 Testing: {team_name}")
        print("=" * 50)
        
        try:
            result = get_team_id(api_key, base_url, team_name, season=2024)
            
            if result:
                print(f"✅ Success: {result}")
            else:
                print(f"❌ Failed: No result returned")
        except Exception as e:
            print(f"💥 Exception: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_get_team_id()