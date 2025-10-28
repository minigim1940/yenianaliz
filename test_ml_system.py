# -*- coding: utf-8 -*-
"""
ML Sistem Test ve İzleme Modülü
"""

from ml_predictor import ml_system
from datetime import datetime
import random

def test_ml_system():
    """ML sistemini test et"""
    
    print("🤖 ML Sistemi Test Ediliyor...")
    
    # Örnek maç sonucu ekle (Tottenham vs Everton)
    team_a_id = 47  # Tottenham
    team_b_id = 48  # Everton
    league_id = 39  # Premier League
    
    # Örnek tahmin (Tottenham favorisi)
    prediction = {
        'win_a': 55.0,  # Tottenham %55
        'draw': 25.0,   # Beraberlik %25  
        'win_b': 20.0   # Everton %20
    }
    
    # Örnek gerçek sonuç (Tottenham kazandı diyelim)
    actual_result = {
        'home_score': 2,
        'away_score': 1,
        'winner': 'home'
    }
    
    # Örnek model faktörleri
    model_factors = {
        'form_factor_a': 1.15,
        'form_factor_b': 0.85,
        'elo_diff': 51,
        'home_advantage': 1.08
    }
    
    # ML sistemine öğret
    ml_system.add_match_result(
        team_a_id, team_b_id, league_id,
        prediction, actual_result, model_factors
    )
    
    print("✅ Örnek maç sonucu ML sistemine eklendi")
    
    # Sistem istatistiklerini göster
    stats = ml_system.get_system_stats()
    print(f"📊 ML Sistem İstatistikleri:")
    print(f"   - Toplam Maç: {stats['total_matches']}")
    print(f"   - Başarı Oranı: {stats['success_rate']:.1f}%")
    print(f"   - Doğru Tahmin: {stats['correct_predictions']}/{stats['total_predictions']}")
    print(f"   - Analiz Edilen Takım: {stats['teams_analyzed']}")
    print(f"   - Analiz Edilen Lig: {stats['leagues_analyzed']}")
    
    # Takım ayarlamalarını test et
    home_adj = ml_system.get_team_learning_adjustment(team_a_id, team_b_id, "home")
    away_adj = ml_system.get_team_learning_adjustment(team_b_id, team_a_id, "away")
    
    print(f"\n🏠 Ev Sahibi ML Ayarlamaları (Tottenham):")
    print(f"   - Hücum Çarpanı: {home_adj['attack_adj']:.3f}")
    print(f"   - Savunma Çarpanı: {home_adj['defense_adj']:.3f}")
    print(f"   - Güven Çarpanı: {home_adj['confidence_adj']:.3f}")
    
    print(f"\n✈️ Deplasman ML Ayarlamaları (Everton):")
    print(f"   - Hücum Çarpanı: {away_adj['attack_adj']:.3f}")
    print(f"   - Savunma Çarpanı: {away_adj['defense_adj']:.3f}")
    print(f"   - Güven Çarpanı: {away_adj['confidence_adj']:.3f}")
    
    # Lig ayarlamalarını test et
    league_adj = ml_system.get_league_learning_adjustment(league_id)
    print(f"\n⚽ Lig ML Ayarlamaları (Premier League):")
    print(f"   - Ev Avantajı Çarpanı: {league_adj['home_advantage_adj']:.3f}")
    print(f"   - Gol Beklentisi Çarpanı: {league_adj['goal_expectancy_adj']:.3f}")
    
    # Güven çarpanını test et
    confidence_mult = ml_system.get_prediction_confidence_multiplier(model_factors)
    print(f"\n🎯 Tahmin Güven Çarpanı: {confidence_mult:.3f}")
    
    return True

def add_sample_matches():
    """Sistem eğitimi için örnek maçlar ekle"""
    
    print("📚 Örnek maçlar ML sistemine ekleniyor...")
    
    # Premier League takım ID'leri (örnek)
    teams = [
        (33, "Manchester United"), (34, "Newcastle"), (35, "Watford"),
        (36, "Fulham"), (39, "Wolves"), (40, "Liverpool"), 
        (42, "Arsenal"), (44, "Burnley"), (47, "Tottenham"), 
        (48, "Everton"), (49, "Chelsea"), (50, "Manchester City")
    ]
    
    sample_matches = [
        # Format: (home_id, away_id, home_score, away_score, prediction_accuracy)
        (40, 49, 2, 1, 0.85),  # Liverpool vs Chelsea - tahmin doğru
        (50, 42, 3, 1, 0.90),  # Man City vs Arsenal - tahmin doğru  
        (47, 48, 2, 0, 0.75),  # Tottenham vs Everton - tahmin doğru
        (33, 44, 1, 1, 0.45),  # Man United vs Burnley - tahmin yanlış
        (49, 40, 0, 2, 0.30),  # Chelsea vs Liverpool - tahmin yanlış
        (42, 50, 1, 3, 0.20),  # Arsenal vs Man City - tahmin yanlış
        (48, 47, 0, 1, 0.65),  # Everton vs Tottenham - tahmin doğru
        (34, 39, 2, 2, 0.40),  # Newcastle vs Wolves - beraberlik tahmini
    ]
    
    for i, (home_id, away_id, home_score, away_score, accuracy) in enumerate(sample_matches):
        # Skordan kazananı belirle
        if home_score > away_score:
            winner = 'home'
            prediction = {'win_a': 60, 'draw': 25, 'win_b': 15}
        elif away_score > home_score:
            winner = 'away'
            prediction = {'win_a': 20, 'draw': 25, 'win_b': 55}
        else:
            winner = 'draw'
            prediction = {'win_a': 30, 'draw': 40, 'win_b': 30}
        
        # Tahmin doğruluğuna göre ayarla (yanlış tahminler için tersini al)
        if accuracy < 0.5:
            if winner == 'home':
                prediction = {'win_a': 25, 'draw': 25, 'win_b': 50}
            elif winner == 'away':
                prediction = {'win_a': 50, 'draw': 25, 'win_b': 25}
        
        actual_result = {
            'home_score': home_score,
            'away_score': away_score,
            'winner': winner
        }
        
        model_factors = {
            'form_factor_a': 0.95 + random.uniform(0, 0.2),
            'form_factor_b': 0.95 + random.uniform(0, 0.2),
            'elo_diff': random.randint(-150, 150),
            'home_advantage': 1.08
        }
        
        ml_system.add_match_result(
            home_id, away_id, 39,  # Premier League
            prediction, actual_result, model_factors
        )
        
        print(f"   ✅ Maç {i+1}: {home_score}-{away_score} eklendi (Doğruluk: {accuracy:.0%})")
    
    # Final istatistikler
    stats = ml_system.get_system_stats()
    print(f"\n📊 Eğitim Sonrası İstatistikler:")
    print(f"   - Toplam Maç: {stats['total_matches']}")
    print(f"   - Sistem Başarı Oranı: {stats['success_rate']:.1f}%")
    print(f"   - Analiz Edilen Takım: {stats['teams_analyzed']}")

if __name__ == "__main__":
    # ML sistemini test et
    test_ml_system()
    
    # Örnek maçlar ekle
    add_sample_matches()
    
    print("\n🎯 ML Sistemi hazır! Artık tahminler geçmiş verilerden öğrenecek.")