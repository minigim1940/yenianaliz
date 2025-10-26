from football_api_v3 import APIFootballV3
import api_utils

API_KEY = "6336fb21e17dea87880d3b133132a13f"
BASE_URL = "https://api-football-v1.p.rapidapi.com/v3"

print("=== API TEST - GERÇEK VERİ ÇEKİMİ ===")

# Test 1: API durumu kontrol
api = APIFootballV3(API_KEY)
print(f"API Key: {API_KEY[:20]}...")

# Test 2: Galatasaray için gerçek veri çekmeyi dene
print("\n🔍 Galatasaray verileri test ediliyor...")

# Takım arama
team_result = api.search_teams("galatasaray")
print(f"Takım arama: Status={team_result.status.value}")

if team_result.status.value == "success" and team_result.data:
    team = team_result.data[0]['team']
    team_id = team['id']
    print(f"✅ Takım bulundu: {team['name']} (ID: {team_id})")
    
    # Yaklaşan maçlar test
    print(f"\n🏆 {team['name']} yaklaşan maçları...")
    fixtures_result = api.get_team_fixtures(team_id, 2024, last=5)  # Sezon parametresi eklendi
    print(f"Fixtures: Status={fixtures_result.status.value}")
    
    if fixtures_result.status.value == "success":
        if fixtures_result.data:
            print(f"✅ {len(fixtures_result.data)} maç bulundu")
            for i, fixture in enumerate(fixtures_result.data[:3]):
                home = fixture.get('teams', {}).get('home', {}).get('name', 'N/A')
                away = fixture.get('teams', {}).get('away', {}).get('name', 'N/A')
                date = fixture.get('fixture', {}).get('date', 'N/A')
                print(f"  {i+1}. {home} vs {away} - {date}")
        else:
            print("❌ Maç verisi yok")
    
    # Sakatlıklar test
    print(f"\n🏥 {team['name']} sakatlık durumu...")
    injuries_result = api.get_team_injuries(team_id)
    print(f"Injuries: Status={injuries_result.status.value}")
    
    if injuries_result.status.value == "success":
        if injuries_result.data:
            print(f"✅ {len(injuries_result.data)} sakatlık bulundu")
            for i, injury in enumerate(injuries_result.data[:5]):
                player = injury.get('player', {}).get('name', 'N/A')
                injury_type = injury.get('injury', {}).get('type', 'N/A')
                print(f"  {i+1}. {player} - {injury_type}")
        else:
            print("✅ Sakatlık yok")
    
else:
    print("❌ Takım bulunamadı veya API hatası")

print("\n=== API CALL COUNT ===")
print("Bu test sırasında 3 API çağrısı yapıldı:")
print("1. search_teams")
print("2. get_team_fixtures") 
print("3. get_team_injuries")