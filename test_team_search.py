from football_api_v3 import APIFootballV3

api = APIFootballV3("6336fb21e17dea87880d3b133132a13f")

print("=== GALATASARAY ARAMA TESTİ ===")

# Test 1: Sadece isimle arama
result1 = api.search_teams("galatasaray")
print(f"Test 1 - Sadece isim: Status={result1.status.value}, Data count={len(result1.data) if result1.data else 0}")
if result1.data:
    for i, team_data in enumerate(result1.data[:3]):
        team = team_data.get('team', {})
        print(f"  {i+1}. {team.get('name')} (ID: {team.get('id')}) - {team.get('country')}")

# Test 2: Türkiye ligi ile arama
result2 = api.search_teams("galatasaray", league_id=203, season=2024)
print(f"\nTest 2 - Süper Lig 2024: Status={result2.status.value}, Data count={len(result2.data) if result2.data else 0}")
if result2.data:
    for i, team_data in enumerate(result2.data[:3]):
        team = team_data.get('team', {})
        print(f"  {i+1}. {team.get('name')} (ID: {team.get('id')}) - {team.get('country')}")

# Test 3: Farklı sezon deneme
result3 = api.search_teams("galatasaray", season=2023)
print(f"\nTest 3 - 2023 sezonu: Status={result3.status.value}, Data count={len(result3.data) if result3.data else 0}")
if result3.data:
    for i, team_data in enumerate(result3.data[:3]):
        team = team_data.get('team', {})
        print(f"  {i+1}. {team.get('name')} (ID: {team.get('id')}) - {team.get('country')}")

# Test 4: Kısaltma ile arama
result4 = api.search_teams("gala")
print(f"\nTest 4 - Kısaltma: Status={result4.status.value}, Data count={len(result4.data) if result4.data else 0}")
if result4.data:
    for i, team_data in enumerate(result4.data[:3]):
        team = team_data.get('team', {})
        print(f"  {i+1}. {team.get('name')} (ID: {team.get('id')}) - {team.get('country')}")

# Test 5: Direkt ID ile kontrol (Galatasaray ID: 644)
result5 = api.get_team_by_id(644)
print(f"\nTest 5 - Direkt ID: Status={result5.status.value}")
if result5.data:
    team = result5.data.get('team', {})
    print(f"  Takım: {team.get('name')} (ID: {team.get('id')}) - {team.get('country')}")