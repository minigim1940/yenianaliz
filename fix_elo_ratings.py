# ELO düzeltme scripti - Türk takımları için gerçekçi değerler

import json
from datetime import datetime

# Gerçekçi Türk takımları ELO ratingleri
TURKISH_TEAMS_ELO = {
    # Süper Lig (2024-25 Gerçekçi ELO)
    "644": 1650,  # Galatasaray (Şampiyon, en güçlü)
    "645": 1620,  # Fenerbahçe  
    "646": 1580,  # Beşiktaş
    "2833": 1540, # İstanbul Başakşehir (Eski şampiyon)
    "643": 1520,  # Trabzonspor
    "3569": 1480, # Kasımpaşa
    "612": 1460,  # Konyaspor
    "558": 1440,  # Antalyaspor (Alt sıralarda)
    "613": 1420,  # Sivasspor
    "609": 1520,  # İstanbul Başakşehir (Düzeltme)
    
    # Alt sıralar
    "614": 1400,  # Kayserispor
    "2281": 1380, # Hatayspor
    "610": 1360,  # Alanyaspor (düşme tehlikesi)
    "615": 1340,  # Adana Demirspor (düşme tehlikesi)
}

def update_elo_ratings():
    """ELO ratinglerini güncel ve gerçekçi değerlerle güncelle"""
    try:
        # Mevcut ELO dosyasını oku
        with open('elo_ratings.json', 'r', encoding='utf-8') as f:
            ratings = json.load(f)
        
        # Türk takımları için gerçekçi değerleri ata
        updated_count = 0
        for team_id, elo_rating in TURKISH_TEAMS_ELO.items():
            if team_id in ratings:
                old_rating = ratings[team_id]["rating"]
                ratings[team_id]["rating"] = elo_rating
                ratings[team_id]["last_updated"] = datetime.now().isoformat()
                print(f"Takım {team_id}: {old_rating} → {elo_rating}")
                updated_count += 1
            else:
                # Takım yoksa ekle
                ratings[team_id] = {
                    "rating": elo_rating,
                    "last_updated": datetime.now().isoformat()
                }
                print(f"Yeni takım {team_id}: {elo_rating}")
                updated_count += 1
        
        # Güncellenmiş dosyayı kaydet
        with open('elo_ratings.json', 'w', encoding='utf-8') as f:
            json.dump(ratings, f, indent=4, ensure_ascii=False)
        
        print(f"\n✅ {updated_count} takımın ELO ratingleri güncellendi!")
        
        # Kontrol için güncellenmiş değerleri yazdır
        print("\n=== GÜNCEL TÜRK TAKIMLARI ELO ===")
        for team_id, expected_elo in TURKISH_TEAMS_ELO.items():
            if team_id in ratings:
                actual_elo = ratings[team_id]["rating"]
                print(f"Takım {team_id}: {actual_elo} ({'✅' if actual_elo == expected_elo else '❌'})")
    
    except Exception as e:
        print(f"ELO güncelleme hatası: {e}")

if __name__ == "__main__":
    update_elo_ratings()