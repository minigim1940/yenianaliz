#!/usr/bin/env python3
"""
Gerçek API fixture verilerini test eden script
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from football_api_v3 import APIFootballV3

def test_real_fixtures():
    """Gerçek fixture API'sini test et"""
    
    # API başlat
    api_key = "6336fb21e17dea87880d3b133132a13f"
    api = APIFootballV3(api_key)
    
    print("🔍 Barcelona takımı aranıyor...")
    
    # Takım ara
    team_result = api.search_teams("Barcelona")
    
    if hasattr(team_result, 'status') and team_result.status.value == "success":
        if team_result.data:
            team = team_result.data[0]['team']
            team_id = team['id']
            print(f"✅ Takım bulundu: {team['name']} (ID: {team_id})")
            
            print(f"\n🔍 Takım {team_id} için fixtures aranıyor...")
            
            # Fixtures al
            fixtures_result = api.get_team_fixtures(team_id, season=2024, next=5)
            
            if hasattr(fixtures_result, 'status') and fixtures_result.status.value == "success":
                fixtures_data = fixtures_result.data
                print(f"✅ {len(fixtures_data) if fixtures_data else 0} fixture alındı")
                
                if fixtures_data:
                    print("\n📅 Bulunan fixtures:")
                    for i, fixture in enumerate(fixtures_data[:3], 1):
                        fixture_info = fixture.get('fixture', {})
                        teams = fixture.get('teams', {})
                        home = teams.get('home', {}).get('name', 'N/A')
                        away = teams.get('away', {}).get('name', 'N/A')
                        
                        from datetime import datetime
                        timestamp = fixture_info.get('timestamp', 0)
                        if timestamp:
                            date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M')
                        else:
                            date_str = fixture_info.get('date', 'N/A')
                        
                        print(f"{i}. {home} vs {away} - {date_str}")
                        print(f"   Status: {fixture_info.get('status', {}).get('short', 'N/A')}")
                        
                        # Şu anki zamandan sonra mı kontrol et
                        current_time = datetime.now().timestamp()
                        if timestamp > current_time:
                            print(f"   ✅ Yaklaşan maç!")
                        else:
                            print(f"   ⏰ Geçmiş maç")
                        print()
                else:
                    print("❌ Fixture verisi boş")
            else:
                print(f"❌ Fixtures alınamadı: {fixtures_result.error if hasattr(fixtures_result, 'error') else 'Bilinmeyen hata'}")
        else:
            print("❌ Takım verisi boş")
    else:
        print(f"❌ Takım bulunamadı: {team_result.error if hasattr(team_result, 'error') else 'Bilinmeyen hata'}")

if __name__ == "__main__":
    test_real_fixtures()