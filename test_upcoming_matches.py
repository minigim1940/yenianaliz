import api_utils

API_KEY = "6336fb21e17dea87880d3b133132a13f"
BASE_URL = "https://api-football-v1.p.rapidapi.com/v3"

print("=== GALATASARAY YAKIN MAÇLAR TESTİ ===")

# 1. Önce takımı bul
team_data = api_utils.get_team_id(API_KEY, BASE_URL, "galatasaray")
if team_data:
    print(f"✅ Takım bulundu: {team_data['name']} (ID: {team_data['id']})")
    team_id = team_data['id']
    
    # 2. Yaklaşan maç ara
    print(f"\n🔍 {team_data['name']} yaklaşan maçları aranıyor...")
    
    next_fixture, error = api_utils.get_next_team_fixture(API_KEY, BASE_URL, team_id)
    if error:
        print(f"❌ Hata: {error}")
        
        # Alternatif yöntem dene
        print("🔄 Alternatif yöntemle deneniyor...")
        fixtures, alt_error = api_utils.get_team_upcoming_fixtures(API_KEY, BASE_URL, team_id, 5)
        
        if alt_error:
            print(f"❌ Alternatif hata: {alt_error}")
        elif fixtures:
            print(f"✅ Alternatif yöntemle {len(fixtures)} maç bulundu!")
            for i, fixture in enumerate(fixtures[:3]):
                teams = fixture.get('teams', {})
                home = teams.get('home', {}).get('name', 'Bilinmiyor')
                away = teams.get('away', {}).get('name', 'Bilinmiyor')
                date = fixture.get('fixture', {}).get('date', 'Tarih bilinmiyor')
                print(f"  {i+1}. {home} vs {away} - {date}")
        else:
            print("❌ Hiç maç bulunamadı")
    else:
        print("✅ Yaklaşan maç bulundu!")
        teams = next_fixture.get('teams', {})
        home = teams.get('home', {}).get('name', 'Bilinmiyor')
        away = teams.get('away', {}).get('name', 'Bilinmiyor')
        date = next_fixture.get('fixture', {}).get('date', 'Tarih bilinmiyor')
        print(f"  Maç: {home} vs {away} - {date}")
        
else:
    print("❌ Takım bulunamadı")