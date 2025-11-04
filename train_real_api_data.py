"""
Gerçek API verisiyle ML modellerini eğitme scripti
API'den gerçek maç sonuçları alıp modelleri eğitir
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple

# Import ML modules
from feature_engineer import FeatureEngineer
from enhanced_ml_predictor import EnhancedMLPredictor
import api_utils

# API Configuration
API_KEY = "cfe9283ead7b7fa5c460e54a71f92d7f"
BASE_URL = "https://v3.football.api-sports.io"

# Leagues to fetch data from
LEAGUES = [
    {'id': 39, 'name': 'Premier League', 'country': 'England', 'season': 2024},
    {'id': 140, 'name': 'La Liga', 'country': 'Spain', 'season': 2024},
    {'id': 78, 'name': 'Bundesliga', 'country': 'Germany', 'season': 2024},
    {'id': 135, 'name': 'Serie A', 'country': 'Italy', 'season': 2024},
    {'id': 61, 'name': 'Ligue 1', 'country': 'France', 'season': 2024},
    {'id': 203, 'name': 'Süper Lig', 'country': 'Turkey', 'season': 2024},
]

def get_finished_fixtures(league_id: int, season: int, limit: int = 50) -> List[Dict]:
    """Bitmiş maçları getir"""
    print(f"📥 {league_id} numaralı ligden bitmiş maçlar alınıyor...")
    
    # Son 60 gün içindeki bitmiş maçları al
    from datetime import datetime, timedelta
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=60)
    
    fixtures, error = api_utils.get_fixtures_by_league(
        API_KEY,
        BASE_URL,
        league_id,
        season,
        skip_limit=False
    )
    
    if error:
        print(f"⚠️ Hata: {error}")
        return []
    
    if not fixtures:
        print(f"⚠️ Maç bulunamadı")
        return []
    
    # Sadece bitmiş maçları filtrele
    finished = [
        f for f in fixtures 
        if f.get('fixture', {}).get('status', {}).get('short') == 'FT'
    ]
    
    # Limit uygula
    finished = finished[:limit]
    
    print(f"✅ {len(finished)} bitmiş maç bulundu")
    return finished


def extract_features_from_fixture(fixture: Dict, feature_engineer: FeatureEngineer) -> Tuple[np.ndarray, int]:
    """
    Maçtan feature'ları çıkar ve sonucu al
    
    Returns:
        (features_array, outcome_label)
        outcome_label: 0=Away Win, 1=Draw, 2=Home Win
    """
    try:
        fixture_id = fixture['fixture']['id']
        home_team_id = fixture['teams']['home']['id']
        away_team_id = fixture['teams']['away']['id']
        league_id = fixture['league']['id']
        season = fixture['league']['season']
        
        # Gerçek sonuç
        home_score = fixture['goals']['home']
        away_score = fixture['goals']['away']
        
        if home_score > away_score:
            outcome = 2  # Home win
        elif home_score < away_score:
            outcome = 0  # Away win
        else:
            outcome = 1  # Draw
        
        # Takım verilerini al
        home_stats, _ = api_utils.get_team_stats(
            API_KEY, BASE_URL, home_team_id, league_id, season, skip_limit=False
        )
        away_stats, _ = api_utils.get_team_stats(
            API_KEY, BASE_URL, away_team_id, league_id, season, skip_limit=False
        )
        
        if not home_stats or not away_stats:
            return None, None
        
        # H2H verisi
        h2h_data, _ = api_utils.get_h2h(
            API_KEY, BASE_URL, home_team_id, away_team_id, skip_limit=False
        )
        
        # Son maçlar
        home_recent, _ = api_utils.get_team_last_matches(
            API_KEY, BASE_URL, home_team_id, limit=10, skip_limit=False
        )
        away_recent, _ = api_utils.get_team_last_matches(
            API_KEY, BASE_URL, away_team_id, limit=10, skip_limit=False
        )
        
        # Takım data yapılarını oluştur
        home_data = {
            'id': home_team_id,
            'name': fixture['teams']['home']['name'],
            'stats': home_stats,
            'recent_matches': home_recent or [],
            'form': home_stats.get('form', '') if home_stats else '',
            'elo_rating': 1500  # Default
        }
        
        away_data = {
            'id': away_team_id,
            'name': fixture['teams']['away']['name'],
            'stats': away_stats,
            'recent_matches': away_recent or [],
            'form': away_stats.get('form', '') if away_stats else '',
            'elo_rating': 1500  # Default
        }
        
        # Feature extraction (86 base features)
        features = feature_engineer.extract_all_features(
            home_data=home_data,
            away_data=away_data,
            league_id=league_id,
            h2h_data=h2h_data
        )
        
        # 4 extra features ekle (training ile aynı)
        home_elo = home_data.get('elo_rating', 1500)
        away_elo = away_data.get('elo_rating', 1500)
        elo_diff = (home_elo - away_elo) / 100.0
        
        # Form factors
        def calc_form_factor(form_str):
            if not form_str:
                return 0.5
            form_values = {'W': 1.0, 'D': 0.5, 'L': 0.0}
            scores = [form_values.get(c, 0.5) for c in form_str[-5:]]
            return sum(scores) / len(scores) if scores else 0.5
        
        form_factor_home = calc_form_factor(home_data.get('form', ''))
        form_factor_away = calc_form_factor(away_data.get('form', ''))
        home_advantage = 1.25
        
        # Tüm feature'ları birleştir (90 total)
        feature_names = sorted(features.keys())
        base_features = [features[name] for name in feature_names]
        
        all_features = base_features + [
            elo_diff,
            form_factor_home,
            form_factor_away,
            home_advantage
        ]
        
        return np.array(all_features), outcome
        
    except Exception as e:
        print(f"❌ Feature extraction hatası: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def collect_training_data(max_matches_per_league: int = 30) -> Tuple[np.ndarray, np.ndarray]:
    """
    Birden fazla ligden gerçek maç verisi topla
    
    Returns:
        X (features), y (outcomes)
    """
    print("\n" + "="*80)
    print("🎯 GERÇEK API VERİSİYLE EĞİTİM VERİSİ TOPLAMA")
    print("="*80 + "\n")
    
    feature_engineer = FeatureEngineer()
    
    all_features = []
    all_outcomes = []
    total_processed = 0
    total_successful = 0
    
    for league in LEAGUES:
        print(f"\n📊 {league['name']} ({league['country']}) - Sezon {league['season']}")
        print("-" * 60)
        
        # Bitmiş maçları al
        fixtures = get_finished_fixtures(
            league['id'], 
            league['season'], 
            limit=max_matches_per_league
        )
        
        if not fixtures:
            continue
        
        league_successful = 0
        
        for idx, fixture in enumerate(fixtures[:max_matches_per_league], 1):
            total_processed += 1
            
            # Feature extraction
            features, outcome = extract_features_from_fixture(fixture, feature_engineer)
            
            if features is not None and outcome is not None:
                all_features.append(features)
                all_outcomes.append(outcome)
                league_successful += 1
                total_successful += 1
                
                outcome_str = ['Away Win', 'Draw', 'Home Win'][outcome]
                print(f"  ✅ [{idx}/{len(fixtures)}] {fixture['teams']['home']['name']} vs "
                      f"{fixture['teams']['away']['name']} → {outcome_str}")
            else:
                print(f"  ⚠️ [{idx}/{len(fixtures)}] Feature extraction başarısız")
            
            # API rate limit için bekleme
            if idx % 10 == 0:
                print(f"    💤 Rate limit için 2 saniye bekleniyor...")
                import time
                time.sleep(2)
        
        print(f"\n  📈 {league['name']}: {league_successful}/{len(fixtures)} başarılı")
    
    print("\n" + "="*80)
    print(f"🎉 VERİ TOPLAMA TAMAMLANDI")
    print(f"   Toplam işlenen: {total_processed}")
    print(f"   Başarılı: {total_successful}")
    print(f"   Başarı oranı: {total_successful/total_processed*100:.1f}%")
    print("="*80 + "\n")
    
    if not all_features:
        raise ValueError("Hiç veri toplanamadı!")
    
    X = np.array(all_features)
    y = np.array(all_outcomes)
    
    return X, y


def train_models_with_real_data():
    """Gerçek API verisiyle modelleri eğit"""
    
    print("\n" + "🚀"*40)
    print(" "*20 + "GERÇEK VERİ İLE MODEL EĞİTİMİ")
    print("🚀"*40 + "\n")
    
    # Veri toplama
    X, y = collect_training_data(max_matches_per_league=30)
    
    print(f"\n📊 EĞİTİM VERİSİ İSTATİSTİKLERİ:")
    print(f"   Toplam örnek: {len(X)}")
    print(f"   Feature sayısı: {X.shape[1]}")
    print(f"   Sonuç dağılımı:")
    print(f"     Home Win: {np.sum(y == 2)} ({np.sum(y == 2)/len(y)*100:.1f}%)")
    print(f"     Draw: {np.sum(y == 1)} ({np.sum(y == 1)/len(y)*100:.1f}%)")
    print(f"     Away Win: {np.sum(y == 0)} ({np.sum(y == 0)/len(y)*100:.1f}%)")
    
    # Train/validation split
    from sklearn.model_selection import train_test_split
    
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"\n📂 VERİ BÖLÜNMESI:")
    print(f"   Training: {len(X_train)} örnek")
    print(f"   Validation: {len(X_val)} örnek")
    
    # Model eğitimi
    print(f"\n🤖 MODEL EĞİTİMİ BAŞLATILIYOR...")
    print("-" * 60)
    
    predictor = EnhancedMLPredictor()
    
    # Tüm modelleri eğit
    predictor.train_all_models(X_train, y_train, X_val, y_val)
    
    # Modelleri kaydet
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = f"real_api_data"
    
    print(f"\n💾 MODELLER KAYDEDİLİYOR...")
    predictor.save_models(suffix=suffix)
    
    # Training data'yı da kaydet
    os.makedirs('training_data', exist_ok=True)
    np.save(f'training_data/X_{suffix}_{timestamp}.npy', X)
    np.save(f'training_data/y_{suffix}_{timestamp}.npy', y)
    
    print(f"\n✅ Training data kaydedildi:")
    print(f"   training_data/X_{suffix}_{timestamp}.npy")
    print(f"   training_data/y_{suffix}_{timestamp}.npy")
    
    # Evaluation
    print(f"\n📊 VALIDATION EVALUATION:")
    print("-" * 60)
    
    from sklearn.metrics import accuracy_score, classification_report
    from ensemble_manager import EnsembleManager
    
    # Ensemble prediction
    ensemble = EnsembleManager()
    
    # Her model için prediction
    X_val_scaled = predictor.scaler.transform(X_val)
    
    model_predictions = {
        'xgboost': predictor.xgb_model.predict_proba(X_val_scaled),
        'random_forest': predictor.rf_model.predict_proba(X_val_scaled),
        'neural_network': predictor.nn_model.predict_proba(X_val_scaled),
        'logistic': predictor.lr_model.predict_proba(X_val_scaled),
        'poisson': predictor.poisson_model.predict_proba(X_val_scaled)
    }
    
    # Weighted ensemble prediction
    predictions = ensemble.weighted_vote(model_predictions)
    
    accuracy = accuracy_score(y_val, predictions)
    
    print(f"\n🎯 VALIDATION ACCURACY: {accuracy*100:.1f}%")
    
    print(f"\n📋 CLASSIFICATION REPORT:")
    print(classification_report(
        y_val, 
        predictions, 
        target_names=['Away Win', 'Draw', 'Home Win']
    ))
    
    # Individual model accuracies
    print(f"\n🔍 INDIVIDUAL MODEL ACCURACIES:")
    for model_name, probs in model_predictions.items():
        preds = np.argmax(probs, axis=1)
        acc = accuracy_score(y_val, preds)
        print(f"   {model_name:20s}: {acc*100:5.1f}%")
    
    print("\n" + "="*80)
    print("✅ EĞİTİM TAMAMLANDI!")
    print("="*80)
    
    print(f"\n📦 SONRAKI ADIMLAR:")
    print(f"   1. Streamlit'i yeniden başlatın: streamlit run app.py")
    print(f"   2. Yeni modeller otomatik yüklenecek")
    print(f"   3. Artık gerçek verilerle çalışan tahminler!")
    
    return predictor, X, y


if __name__ == "__main__":
    try:
        predictor, X, y = train_models_with_real_data()
        print("\n🎉 BAŞARILI!")
    except Exception as e:
        print(f"\n❌ HATA: {e}")
        import traceback
        traceback.print_exc()
