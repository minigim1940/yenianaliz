# -*- coding: utf-8 -*-
"""
Over/Under API Test - Gerçek verilerin çekilip çekilmediğini test et
"""

import requests
import json
from api_utils import get_fixture_detailed_odds

def test_over_under_api():
    """Over/Under API'sini test et"""
    
    # API bilgileri
    api_key = "bb8f0636e1mshad70f982d4e36b7p16e880jsn4ed9c5d84732"
    base_url = "https://api-football-v1.p.rapidapi.com/v3"
    
    # Test için bir fixture ID (yakın gelecekteki maç)
    fixture_id = 1271896  # Galatasaray - Trabzonspor
    
    print(f"🔍 Fixture ID {fixture_id} için over/under verilerini test ediyoruz...")
    
    # 1. Doğrudan API çağrısı
    headers = {
        'X-RapidAPI-Key': api_key,
        'X-RapidAPI-Host': 'api-football-v1.p.rapidapi.com'
    }
    
    url = f"{base_url}/odds"
    params = {
        'fixture': fixture_id,
        'bet': 'Goals Over/Under'
    }
    
    try:
        print("📡 Doğrudan API çağrısı yapılıyor...")
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Response Status: {response.status_code}")
            print(f"📊 Response Keys: {list(data.keys())}")
            
            if 'response' in data and data['response']:
                print(f"🎯 Toplam Odds Sayısı: {len(data['response'])}")
                
                # İlk birkaç sonucu göster
                for i, odds_data in enumerate(data['response'][:2]):
                    print(f"\n--- Odds {i+1} ---")
                    print(f"League: {odds_data.get('league', {}).get('name', 'N/A')}")
                    print(f"Fixture: {odds_data.get('fixture', {}).get('id', 'N/A')}")
                    
                    bookmakers = odds_data.get('bookmakers', [])
                    print(f"Bookmakers: {len(bookmakers)}")
                    
                    for j, bookmaker in enumerate(bookmakers[:3]):
                        print(f"  Bookmaker {j+1}: {bookmaker.get('name', 'N/A')}")
                        
                        bets = bookmaker.get('bets', [])
                        for bet in bets:
                            bet_name = bet.get('name', '')
                            if 'over' in bet_name.lower() or 'under' in bet_name.lower():
                                print(f"    Bet: {bet_name}")
                                
                                values = bet.get('values', [])[:4]  # İlk 4 değer
                                for value in values:
                                    print(f"      {value.get('value', '')}: {value.get('odd', 'N/A')}")
            else:
                print("❌ Response boş!")
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ API çağrısı hatası: {e}")
    
    print("\n" + "="*50)
    
    # 2. Kendi fonksiyonumuz ile test
    print("🔧 get_fixture_detailed_odds fonksiyonu ile test...")
    
    try:
        detailed_odds, error = get_fixture_detailed_odds(api_key, base_url, fixture_id)
        
        if error:
            print(f"❌ Fonksiyon Hatası: {error}")
        elif detailed_odds:
            print("✅ Fonksiyon başarılı!")
            print(f"📂 Kategoriler: {list(detailed_odds.keys())}")
            
            # Over/Under kategorisini kontrol et
            over_under = detailed_odds.get('over_under', [])
            print(f"🎯 Over/Under verisi: {len(over_under)} adet")
            
            for i, ou_data in enumerate(over_under[:2]):
                print(f"\n--- Over/Under {i+1} ---")
                print(f"Bookmaker: {ou_data.get('bookmaker', 'N/A')}")
                print(f"Bet Name: {ou_data.get('bet_name', 'N/A')}")
                
                values = ou_data.get('values', [])[:6]
                for value in values:
                    print(f"  {value.get('value', '')}: {value.get('odd', 'N/A')}")
        else:
            print("❌ Fonksiyon boş sonuç döndü")
            
    except Exception as e:
        print(f"❌ Fonksiyon hatası: {e}")

if __name__ == "__main__":
    test_over_under_api()