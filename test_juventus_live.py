#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
from datetime import datetime

API_KEY = os.environ.get('API_KEY', 'test_key')
BASE_URL = "https://v3.football.api-sports.io"

def test_live_matches():
    """Test canlı maçları kontrol et"""
    print("🔍 JUVENTUS CANLI MAÇ KONTROL TEST")
    print("=" * 50)
    
    if API_KEY == 'test_key':
        print("❌ API_KEY bulunamadı")
        return
        
    headers = {
        'X-RapidAPI-Host': 'v3.football.api-sports.io',
        'X-RapidAPI-Key': API_KEY
    }
    
    # Test 1: Genel canlı maçlar
    print("\n1️⃣ TÜM CANLI MAÇLAR")
    print("-" * 25)
    
    try:
        response = requests.get(f"{BASE_URL}/fixtures", 
                              headers=headers, 
                              params={"live": "all"})
        
        if response.status_code == 200:
            data = response.json()
            fixtures = data.get('response', [])
            print(f"📊 Toplam canlı maç: {len(fixtures)}")
            
            # Juventus'u ara
            juventus_matches = []
            for fixture in fixtures:
                home_team = fixture['teams']['home']['name'].lower()
                away_team = fixture['teams']['away']['name'].lower()
                
                if 'juventus' in home_team or 'juventus' in away_team:
                    juventus_matches.append(fixture)
                    print(f"⚽ BULUNDU: {fixture['teams']['home']['name']} vs {fixture['teams']['away']['name']}")
                    print(f"   Status: {fixture['fixture']['status']['long']}")
                    print(f"   Elapsed: {fixture['fixture']['status']['elapsed']}dk")
                    
            if not juventus_matches:
                print("❌ Juventus canlı maçı bulunamadı")
                
                # En yakın Juventus maçlarını ara
                print("\n2️⃣ JUVENTUS YAKIN MAÇLARI")  
                print("-" * 30)
                
                # Bugünün tarihi
                from datetime import date
                today = date.today().strftime('%Y-%m-%d')
                
                response2 = requests.get(f"{BASE_URL}/fixtures",
                                       headers=headers,
                                       params={"team": "496", "date": today})  # 496 = Juventus ID
                
                if response2.status_code == 200:
                    data2 = response2.json()
                    today_fixtures = data2.get('response', [])
                    
                    print(f"📅 Bugün Juventus maçları: {len(today_fixtures)}")
                    
                    for fixture in today_fixtures:
                        status = fixture['fixture']['status']
                        print(f"🏟️ {fixture['teams']['home']['name']} vs {fixture['teams']['away']['name']}")
                        print(f"   Status: {status['long']} ({status['short']})")
                        print(f"   Tarih: {fixture['fixture']['date']}")
                        
        else:
            print(f"❌ API Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_live_matches()