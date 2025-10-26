from football_api_v3 import APIFootballV3
import analysis_logic

# Antalyaspor vs Istanbul Basaksehir test
api = APIFootballV3("6336fb21e17dea87880d3b133132a13f")

# Takım ID'leri (Antalyaspor: 558, Istanbul Basaksehir: 609 tahmin ediyorum)
antalyaspor_id = 558
basaksehir_id = 609
fixture_id = 1311465  # Güncel fixture ID

print("=== TAKIMLAR ===")
print(f"Antalyaspor ID: {antalyaspor_id}")
print(f"İstanbul Başakşehir ID: {basaksehir_id}")

# Bu sezon istatistiklerini kontrol et
print("\n=== SEZON İSTATİSTİKLERİ ===")
league_info = {'league_id': 203, 'season': 2024}  # Süper Lig 2024-25

try:
    stats_antalya = analysis_logic.calculate_general_stats_v2(
        "6336fb21e17dea87880d3b133132a13f", 
        "https://api-football-v1.p.rapidapi.com/v3", 
        antalyaspor_id, 
        203, 2024, 
        skip_api_limit=True
    )
    
    stats_basaksehir = analysis_logic.calculate_general_stats_v2(
        "6336fb21e17dea87880d3b133132a13f", 
        "https://api-football-v1.p.rapidapi.com/v3", 
        basaksehir_id, 
        203, 2024, 
        skip_api_limit=True
    )
    
    print(f"\nAntalyaspor İstatistikleri:")
    print(f"  Gol ortalaması (ev): {stats_antalya['goals_for']}")
    print(f"  Yenilen gol (ev): {stats_antalya['goals_against']}")
    print(f"  Form faktörü: {stats_antalya.get('form_factor', 'N/A')}")
    
    print(f"\nBaşakşehir İstatistikleri:")
    print(f"  Gol ortalaması (deplasman): {stats_basaksehir['goals_for']}")
    print(f"  Yenilen gol (deplasman): {stats_basaksehir['goals_against']}")
    print(f"  Form faktörü: {stats_basaksehir.get('form_factor', 'N/A')}")
    
except Exception as e:
    print(f"İstatistik hatası: {e}")

# ELO ratinglerini kontrol et
print("\n=== ELO RATİNGLERİ ===")
try:
    import elo_utils
    ratings = elo_utils.read_ratings()
    antalya_elo = elo_utils.get_team_rating(antalyaspor_id, ratings)
    basaksehir_elo = elo_utils.get_team_rating(basaksehir_id, ratings)
    
    print(f"Antalyaspor ELO: {antalya_elo}")
    print(f"Başakşehir ELO: {basaksehir_elo}")
    print(f"ELO Farkı: {basaksehir_elo - antalya_elo} (Başakşehir lehine)")
    
except Exception as e:
    print(f"ELO hatası: {e}")