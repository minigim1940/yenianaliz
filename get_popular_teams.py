#!/usr/bin/env python3
"""
Popüler takımları test et ve mapping'e ekle
"""

from api_utils import make_api_request
import time

def get_popular_teams():
    API_KEY = '6336fb21e17dea87880d3b133132a13f'
    BASE_URL = 'https://v3.football.api-sports.io'
    
    # Eklenmesi gereken popüler takımlar
    popular_teams = [
        'manchester city', 'tottenham', 'atletico madrid', 
        'borussia dortmund', 'napoli', 'roma', 'lazio', 
        'valencia', 'sevilla', 'ajax', 'porto', 'benfica',
        'lyon', 'marseille', 'monaco', 'villarreal',
        'atalanta', 'fiorentina', 'eintracht frankfurt',
        'leicester', 'everton', 'west ham'
    ]
    
    print("🔍 POPÜLER TAKIMLARIN ID'LERİNİ BULMA...")
    print("=" * 60)
    
    results = []
    
    for team in popular_teams:
        try:
            print(f"📊 Aranıyor: {team}")
            response, error = make_api_request(API_KEY, BASE_URL, "teams", {'search': team}, skip_limit=True)
            
            if error:
                print(f"❌ Error: {error}")
                continue
                
            if not response or len(response) == 0:
                print(f"❌ Bulunamadı: {team}")
                continue
            
            team_info = response[0]['team']
            print(f"✅ {team}: {team_info['name']} (ID: {team_info['id']})")
            
            # Mapping format'ına dönüştür
            mapping_line = f"            '{team}': {team_info['id']}, '{team.replace(' ', '')}': {team_info['id']},"
            results.append(mapping_line)
            
            time.sleep(0.2)  # Rate limit
            
        except Exception as e:
            print(f"❌ Exception for {team}: {e}")
    
    print("\n" + "=" * 60)
    print("📝 MAPPING İÇİN EKLENECEK SATIRLAR:")
    print("=" * 60)
    for line in results:
        print(line)
    
    return results

if __name__ == "__main__":
    get_popular_teams()