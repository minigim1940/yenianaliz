#!/usr/bin/env python3
"""
Tüm takım ID mapping'lerini test eden script
"""

from api_utils import get_team_id, make_api_request
import time

def test_all_team_mappings():
    API_KEY = '6336fb21e17dea87880d3b133132a13f'
    BASE_URL = 'https://v3.football.api-sports.io'
    
    # Mevcut mapping'deki tüm takımlar
    team_mappings = {
        # Turkish teams
        'galatasaray': 645,
        'fenerbahce': 611, 
        'besiktas': 549,
        'trabzonspor': 998,
        # Major European teams
        'juventus': 496,
        'barcelona': 529,
        'real madrid': 541,
        'manchester united': 33,
        'liverpool': 40,
        'arsenal': 42,
        'chelsea': 49,
        'bayern munich': 157,
        'psg': 85,
        'ac milan': 489,
        'inter': 505
    }
    
    print("🔍 TÜM TAKIM ID'LERİ TEST EDİLİYOR...")
    print("=" * 60)
    
    correct_mappings = {}
    incorrect_mappings = {}
    
    for team_name, expected_id in team_mappings.items():
        try:
            print(f"\n📊 Test: {team_name} (Expected ID: {expected_id})")
            
            # API'den gerçek takım bilgisini al
            response, error = make_api_request(API_KEY, BASE_URL, "teams", {'id': expected_id}, skip_limit=True)
            
            if error:
                print(f"❌ API Error for {team_name}: {error}")
                continue
                
            if not response or len(response) == 0:
                print(f"❌ No team found for ID {expected_id}")
                # API search ile doğru ID'yi bul
                search_response, search_error = make_api_request(API_KEY, BASE_URL, "teams", {'search': team_name}, skip_limit=True)
                if search_response and len(search_response) > 0:
                    real_team = search_response[0]['team']
                    print(f"🔍 API Search Result: {real_team['name']} (ID: {real_team['id']})")
                    incorrect_mappings[team_name] = {
                        'expected_id': expected_id,
                        'correct_id': real_team['id'],
                        'correct_name': real_team['name']
                    }
                continue
            
            # Takım bilgisini kontrol et
            team_raw = response[0]
            team_info = team_raw['team'] if 'team' in team_raw else team_raw
            
            # Takım ismi benzerlğini kontrol et
            api_name = team_info.get('name', '').lower()
            search_name = team_name.lower()
            
            # Basit benzerlik kontrolleri
            is_similar = (
                search_name in api_name or 
                api_name in search_name or
                any(word in api_name for word in search_name.split()) or
                (team_name == 'psg' and 'paris' in api_name) or
                (team_name == 'bayern munich' and 'bayern' in api_name) or
                (team_name == 'manchester united' and 'manchester united' in api_name) or
                (team_name == 'real madrid' and 'real madrid' in api_name) or
                (team_name == 'ac milan' and 'milan' in api_name) or
                (team_name == 'inter' and 'inter' in api_name)
            )
            
            if is_similar:
                print(f"✅ CORRECT: {team_name} → {team_info['name']} (ID: {team_info['id']})")
                correct_mappings[team_name] = expected_id
            else:
                print(f"❌ INCORRECT: {team_name} → {team_info['name']} (ID: {team_info['id']})")
                # Doğru takımı bul
                search_response, search_error = make_api_request(API_KEY, BASE_URL, "teams", {'search': team_name}, skip_limit=True)
                if search_response and len(search_response) > 0:
                    real_team = search_response[0]['team']
                    print(f"🔍 Correct team: {real_team['name']} (ID: {real_team['id']})")
                    incorrect_mappings[team_name] = {
                        'expected_id': expected_id,
                        'correct_id': real_team['id'],
                        'correct_name': real_team['name']
                    }
                
            time.sleep(0.2)  # API rate limit
            
        except Exception as e:
            print(f"❌ Exception for {team_name}: {e}")
    
    print("\n" + "=" * 60)
    print("📊 TEST SONUÇLARI:")
    print("=" * 60)
    print(f"✅ Doğru mapping'ler: {len(correct_mappings)}")
    print(f"❌ Yanlış mapping'ler: {len(incorrect_mappings)}")
    
    if incorrect_mappings:
        print("\n🔧 DÜZELTİLMESİ GEREKEN MAPPING'LER:")
        for team, info in incorrect_mappings.items():
            print(f"  '{team}': {info['expected_id']} → {info['correct_id']},  # {info['correct_name']}")
    
    return correct_mappings, incorrect_mappings

if __name__ == "__main__":
    test_all_team_mappings()