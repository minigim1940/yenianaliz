#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Eski maçları test etmek için basit test scripti
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from football_api_v3 import APIFootballV3
import api_utils
from datetime import datetime

def test_galatasaray_matches():
    """Galatasaray'ın maçlarını test et"""
    print("=" * 60)
    print("🔍 GALATASARAY MAÇLARI TEST")
    print("=" * 60)
    
    api_key = "6336fb21e17dea87880d3b133132a13f"
    
    try:
        api = APIFootballV3(api_key)
        
        # Takım ara
        teams_result = api.search_teams("galatasaray")
        if teams_result.status.name != "SUCCESS" or not teams_result.data:
            print("❌ Galatasaray bulunamadı")
            return
        
        team = teams_result.data[0]
        team_id = team.get('team', {}).get('id')
        team_name = team.get('team', {}).get('name')
        
        print(f"✅ Takım bulundu: {team_name} (ID: {team_id})")
        
        # Gelecek maçları al
        print("\n🔍 Gelecek maçları alınıyor...")
        fixtures_result = api.get_team_fixtures(team_id, season=2024, next=10)
        
        if fixtures_result.status.name == "SUCCESS" and fixtures_result.data:
            print(f"\n📋 {len(fixtures_result.data)} maç bulundu:")
            
            current_date = datetime.now().strftime('%Y-%m-%d')
            print(f"📅 Bugünkü tarih: {current_date}")
            
            for i, fixture in enumerate(fixtures_result.data, 1):
                fixture_date = fixture.get('fixture', {}).get('date', '')
                status = fixture.get('fixture', {}).get('status', {}).get('short', '')
                home_team = fixture.get('teams', {}).get('home', {}).get('name', '')
                away_team = fixture.get('teams', {}).get('away', {}).get('name', '')
                
                # Tarih karşılaştırması
                date_comparison = ""
                if fixture_date:
                    fixture_date_str = fixture_date[:10]
                    if fixture_date_str < current_date:
                        date_comparison = "❌ GEÇMİŞ"
                    elif fixture_date_str == current_date:
                        date_comparison = "⏰ BUGÜN"
                    else:
                        date_comparison = "✅ GELECEK"
                
                print(f"   {i}. {fixture_date[:10]} | {status} | {home_team} vs {away_team} | {date_comparison}")
        else:
            print("❌ Maç bulunamadı")
            
    except Exception as e:
        print(f"❌ Hata: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_galatasaray_matches()