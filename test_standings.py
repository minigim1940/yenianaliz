# -*- coding: utf-8 -*-
"""
Standings (Puan Durumu) Test
=============================
"""

import os
import api_utils

API_KEY = os.getenv('RAPIDAPI_KEY', 'YOUR_API_KEY_HERE')
BASE_URL = "https://api-football-v1.p.rapidapi.com/v3"

def test_standings():
    """Test puan durumu API çağrısı"""
    
    print("🧪 PUAN DURUMU TEST\n")
    print("="*80)
    
    # UEFA Champions League 2024
    league_id = 2
    season = 2024
    
    print(f"Lig ID: {league_id}")
    print(f"Sezon: {season}\n")
    
    try:
        standings_data, error = api_utils.get_league_standings(
            api_key=API_KEY,
            base_url=BASE_URL,
            league_id=league_id,
            season=season
        )
        
        if error:
            print(f"❌ API Hatası: {error}")
        elif standings_data:
            print(f"✅ Puan durumu başarıyla çekildi!")
            print(f"📊 {len(standings_data)} takım bulundu\n")
            
            # İlk 5 takımı göster
            print("İlk 5 Takım:")
            print("-" * 80)
            print(f"{'Sıra':<6} {'Takım':<30} {'P':<6} {'O':<6} {'Averaj':<8} {'Form':<10}")
            print("-" * 80)
            
            for team in standings_data[:5]:
                rank = team.get('rank', 'N/A')
                team_name = team.get('team', {}).get('name', 'N/A')
                points = team.get('points', 'N/A')
                played = team.get('all', {}).get('played', 'N/A')
                goal_diff = team.get('goalsDiff', 'N/A')
                form = team.get('form', 'N/A')
                
                print(f"{rank:<6} {team_name:<30} {points:<6} {played:<6} {goal_diff:<8} {form:<10}")
            
            print("\n✅ TEST BAŞARILI!")
        else:
            print("⚠️ Veri bulunamadı")
    
    except Exception as e:
        print(f"❌ Test başarısız: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)

if __name__ == "__main__":
    test_standings()
