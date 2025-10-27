"""
LSTM Tabanlı Maç Sonucu Tahmin Modülü
Takım performansını zaman serisi olarak modelleyerek gelecek maç sonuçlarını tahmin eder.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import json

# TensorFlow/Keras import - opsiyonel (yüklü değilse basit model kullanılır)
try:
    from tensorflow import keras
    from tensorflow.keras.models import Sequential, load_model, save_model
    from tensorflow.keras.layers import LSTM, Dense, Dropout, Bidirectional
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
    KERAS_AVAILABLE = True
except ImportError:
    KERAS_AVAILABLE = False
    print("⚠️ TensorFlow/Keras bulunamadı. LSTM modeli için basit tahmin kullanılacak.")


class LSTMMatchPredictor:
    """
    LSTM tabanlı maç sonucu tahmin modeli
    
    Özellikler:
    - Son N maçın performans trendlerini analiz eder
    - Ev sahibi/deplasman avantajını öğrenir
    - Gol ortalamaları, kazanma oranları, form trendlerini modeller
    - Bidirectional LSTM ile hem ileri hem geri temporal pattern öğrenir
    """
    
    def __init__(self, sequence_length: int = 10, model_path: Optional[str] = None):
        """
        Args:
            sequence_length: Kaç maçlık geçmiş kullanılacak (varsayılan: 10)
            model_path: Eğitilmiş model dosya yolu (yoksa yeni model oluşturulur)
        """
        self.sequence_length = sequence_length
        self.model_path = model_path
        self.model = None
        self.feature_scaler = None
        self.is_trained = False
        
        # Feature isimleri
        self.feature_names = [
            'goals_scored', 'goals_conceded', 'win', 'draw', 'loss',
            'xg_for', 'xg_against', 'possession', 'shots_on_target',
            'is_home', 'opponent_strength', 'days_since_last_match'
        ]
        
        if KERAS_AVAILABLE and model_path:
            self._load_model()
    
    def _create_model(self, input_shape: Tuple[int, int]) -> 'keras.Model':
        """LSTM modelini oluştur"""
        if not KERAS_AVAILABLE:
            return None
        
        model = Sequential([
            # İlk LSTM katmanı (Bidirectional - hem ileri hem geri öğrenir)
            Bidirectional(LSTM(128, return_sequences=True, 
                              dropout=0.2, recurrent_dropout=0.2)),
            
            # İkinci LSTM katmanı
            Bidirectional(LSTM(64, return_sequences=False,
                              dropout=0.2, recurrent_dropout=0.2)),
            
            # Dense katmanlar
            Dense(64, activation='relu'),
            Dropout(0.3),
            Dense(32, activation='relu'),
            Dropout(0.2),
            
            # Çıkış katmanı: [win_prob, draw_prob, loss_prob]
            Dense(3, activation='softmax')
        ])
        
        # Model compile
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='categorical_crossentropy',
            metrics=['accuracy', 'AUC']
        )
        
        return model
    
    def prepare_sequences(self, team_matches: List[Dict]) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Maç geçmişinden LSTM için sequence oluştur
        
        Args:
            team_matches: Takımın geçmiş maçları (kronolojik sırayla, en eski önce)
        
        Returns:
            X: Feature sequences, shape (n_sequences, sequence_length, n_features)
            y: Labels (varsa), shape (n_sequences, 3) - [win, draw, loss]
        """
        if len(team_matches) < self.sequence_length + 1:
            return np.array([]), None
        
        sequences = []
        labels = []
        
        for i in range(len(team_matches) - self.sequence_length):
            # Son N maçı al (feature sequence)
            sequence_matches = team_matches[i:i + self.sequence_length]
            
            # Feature extraction
            features = []
            for match in sequence_matches:
                match_features = self._extract_match_features(match)
                features.append(match_features)
            
            sequences.append(features)
            
            # Label: Bir sonraki maç sonucu (eğer varsa)
            if i + self.sequence_length < len(team_matches):
                next_match = team_matches[i + self.sequence_length]
                label = self._get_match_label(next_match)
                labels.append(label)
        
        X = np.array(sequences, dtype=np.float32)
        y = np.array(labels, dtype=np.float32) if labels else None
        
        return X, y
    
    def _extract_match_features(self, match: Dict) -> List[float]:
        """Bir maçtan feature'ları çıkar"""
        features = [
            match.get('goals_scored', 0),
            match.get('goals_conceded', 0),
            1.0 if match.get('result') == 'W' else 0.0,
            1.0 if match.get('result') == 'D' else 0.0,
            1.0 if match.get('result') == 'L' else 0.0,
            match.get('xg_for', match.get('goals_scored', 0) * 0.8),
            match.get('xg_against', match.get('goals_conceded', 0) * 0.8),
            match.get('possession', 50.0) / 100.0,  # Normalize
            match.get('shots_on_target', 0) / 20.0,  # Normalize
            1.0 if match.get('is_home', True) else 0.0,
            match.get('opponent_elo', 1500) / 2000.0,  # Normalize
            min(match.get('days_since_last', 7), 30) / 30.0  # Normalize
        ]
        
        return features
    
    def _get_match_label(self, match: Dict) -> List[float]:
        """Maç sonucunu one-hot encoding'e çevir"""
        result = match.get('result', 'D')
        
        if result == 'W':
            return [1.0, 0.0, 0.0]  # Win
        elif result == 'D':
            return [0.0, 1.0, 0.0]  # Draw
        else:
            return [0.0, 0.0, 1.0]  # Loss
    
    def train(self, training_data: List[Dict], epochs: int = 50, 
              validation_split: float = 0.2, batch_size: int = 32) -> Dict:
        """
        Modeli eğit
        
        Args:
            training_data: Tüm takımların maç geçmişleri
            epochs: Eğitim epoch sayısı
            validation_split: Validation oranı
            batch_size: Batch boyutu
        
        Returns:
            Eğitim metrikleri
        """
        if not KERAS_AVAILABLE:
            print("❌ Keras yüklü değil, model eğitilemedi")
            return {"error": "Keras not available"}
        
        # Tüm takımlardan sequence oluştur
        all_sequences = []
        all_labels = []
        
        for team_data in training_data:
            matches = team_data.get('matches', [])
            X, y = self.prepare_sequences(matches)
            
            if X.shape[0] > 0 and y is not None:
                all_sequences.append(X)
                all_labels.append(y)
        
        if not all_sequences:
            return {"error": "Yeterli veri yok"}
        
        # Birleştir
        X_train = np.concatenate(all_sequences, axis=0)
        y_train = np.concatenate(all_labels, axis=0)
        
        print(f"📊 Eğitim verisi: {X_train.shape[0]} sequence, {X_train.shape[1]} timesteps, {X_train.shape[2]} features")
        
        # Model oluştur
        self.model = self._create_model(input_shape=(X_train.shape[1], X_train.shape[2]))
        
        # Callbacks
        callbacks = [
            EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True),
            ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=0.00001)
        ]
        
        # Eğitim
        history = self.model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            callbacks=callbacks,
            verbose=1
        )
        
        self.is_trained = True
        
        # Modeli kaydet
        if self.model_path:
            self.model.save(self.model_path)
            print(f"✅ Model kaydedildi: {self.model_path}")
        
        # Eğitim metrikleri
        return {
            "final_loss": float(history.history['loss'][-1]),
            "final_accuracy": float(history.history['accuracy'][-1]),
            "final_val_loss": float(history.history['val_loss'][-1]),
            "final_val_accuracy": float(history.history['val_accuracy'][-1]),
            "epochs_trained": len(history.history['loss'])
        }
    
    def predict(self, team_matches: List[Dict]) -> Dict:
        """
        Bir takımın sonraki maç sonucunu tahmin et
        
        Args:
            team_matches: Takımın son maçları (kronolojik, en eski önce)
        
        Returns:
            Tahmin sonuçları: {win_prob, draw_prob, loss_prob, confidence, trend}
        """
        # Basit tahmin (LSTM yoksa veya model eğitilmemişse)
        if not KERAS_AVAILABLE or not self.is_trained or self.model is None:
            return self._simple_prediction(team_matches)
        
        # LSTM ile tahmin
        X, _ = self.prepare_sequences(team_matches)
        
        if X.shape[0] == 0:
            return self._simple_prediction(team_matches)
        
        # Son sequence'i al (en güncel)
        last_sequence = X[-1:, :, :]
        
        # Tahmin
        prediction = self.model.predict(last_sequence, verbose=0)[0]
        
        win_prob = float(prediction[0])
        draw_prob = float(prediction[1])
        loss_prob = float(prediction[2])
        
        # Güven skoru
        confidence = float(np.max(prediction)) * 100
        
        # Trend analizi (son 5 maç)
        trend = self._analyze_trend(team_matches[-5:] if len(team_matches) >= 5 else team_matches)
        
        return {
            'win_probability': win_prob,
            'draw_probability': draw_prob,
            'loss_probability': loss_prob,
            'confidence': confidence,
            'trend': trend,
            'prediction_method': 'LSTM'
        }
    
    def _simple_prediction(self, team_matches: List[Dict]) -> Dict:
        """
        Basit istatistiksel tahmin (LSTM olmadan)
        Son N maçın istatistiklerine göre tahmin yapar
        """
        if not team_matches:
            return {
                'win_probability': 0.33,
                'draw_probability': 0.33,
                'loss_probability': 0.34,
                'confidence': 50.0,
                'trend': 'stable',
                'prediction_method': 'statistical'
            }
        
        # Son 10 maçı al
        recent_matches = team_matches[-min(10, len(team_matches)):]
        
        # İstatistikler
        wins = sum(1 for m in recent_matches if m.get('result') == 'W')
        draws = sum(1 for m in recent_matches if m.get('result') == 'D')
        losses = sum(1 for m in recent_matches if m.get('result') == 'L')
        total = len(recent_matches)
        
        # Sıfıra bölme kontrolü
        if total == 0:
            return {
                'win_probability': 0.33,
                'draw_probability': 0.33,
                'loss_probability': 0.34,
                'confidence': 50.0,
                'trend': 'stable',
                'prediction_method': 'statistical'
            }
        
        # Basit olasılıklar
        win_prob = wins / total
        draw_prob = draws / total
        loss_prob = losses / total
        
        # Form bazlı düzeltme (son 3 maç daha önemli)
        if len(recent_matches) >= 3:
            recent_3 = recent_matches[-3:]
            recent_wins = sum(1 for m in recent_3 if m.get('result') == 'W')
            recent_weight = 0.3
            
            win_prob = win_prob * (1 - recent_weight) + (recent_wins / 3) * recent_weight
            draw_prob = draw_prob * (1 - recent_weight) + (sum(1 for m in recent_3 if m.get('result') == 'D') / 3) * recent_weight
            loss_prob = 1.0 - win_prob - draw_prob
        
        # Normalize
        total_prob = win_prob + draw_prob + loss_prob
        if total_prob > 0:
            win_prob /= total_prob
            draw_prob /= total_prob
            loss_prob /= total_prob
        
        confidence = max(win_prob, draw_prob, loss_prob) * 100
        trend = self._analyze_trend(recent_matches)
        
        return {
            'win_probability': float(win_prob),
            'draw_probability': float(draw_prob),
            'loss_probability': float(loss_prob),
            'confidence': float(confidence),
            'trend': trend,
            'prediction_method': 'statistical'
        }
    
    def _analyze_trend(self, matches: List[Dict]) -> str:
        """
        Form trendini analiz et
        
        Returns:
            'improving', 'declining', 'stable'
        """
        if len(matches) < 3:
            return 'stable'
        
        # Puanları hesapla (W=3, D=1, L=0)
        points = []
        for match in matches:
            result = match.get('result', 'D')
            if result == 'W':
                points.append(3)
            elif result == 'D':
                points.append(1)
            else:
                points.append(0)
        
        # İlk yarı vs ikinci yarı
        mid = len(points) // 2
        first_half_avg = np.mean(points[:mid]) if mid > 0 else 0
        second_half_avg = np.mean(points[mid:])
        
        diff = second_half_avg - first_half_avg
        
        if diff > 0.5:
            return 'improving'
        elif diff < -0.5:
            return 'declining'
        else:
            return 'stable'
    
    def _load_model(self):
        """Eğitilmiş modeli yükle"""
        if not KERAS_AVAILABLE:
            return
        
        try:
            self.model = load_model(self.model_path)
            self.is_trained = True
            print(f"✅ Model yüklendi: {self.model_path}")
        except Exception as e:
            print(f"⚠️ Model yüklenemedi: {e}")
            self.is_trained = False


def predict_match_with_lstm(home_team_matches: List[Dict], 
                            away_team_matches: List[Dict],
                            lstm_model: Optional[LSTMMatchPredictor] = None) -> Dict:
    """
    İki takım arasındaki maçı LSTM ile tahmin et
    
    Args:
        home_team_matches: Ev sahibi takımın son maçları
        away_team_matches: Deplasman takımının son maçları
        lstm_model: Eğitilmiş LSTM model (None ise yeni oluşturulur)
    
    Returns:
        Detaylı tahmin sonuçları
    """
    if lstm_model is None:
        lstm_model = LSTMMatchPredictor(sequence_length=10)
    
    # Her iki takım için tahmin
    home_prediction = lstm_model.predict(home_team_matches)
    away_prediction = lstm_model.predict(away_team_matches)
    
    # Ev sahibi avantajı (istatistiksel)
    home_advantage = 1.15
    
    # Home team kazanma olasılığı
    home_win = home_prediction['win_probability'] * home_advantage
    
    # Away team kazanma olasılığı (home team'in kaybetme olasılığı)
    away_win = away_prediction['win_probability'] / home_advantage
    
    # Beraberlik olasılığı (her iki takımın beraberlik olasılığı ortalaması)
    draw = (home_prediction['draw_probability'] + away_prediction['draw_probability']) / 2
    
    # Normalize - Sıfıra bölme kontrolü
    total = home_win + draw + away_win
    if total > 0:
        home_win /= total
        draw /= total
        away_win /= total
    else:
        # Eğer toplam sıfırsa, eşit olasılık ver
        home_win = 0.33
        draw = 0.34
        away_win = 0.33
    
    # Toplam güven skoru
    avg_confidence = (home_prediction['confidence'] + away_prediction['confidence']) / 2
    
    # Tahmin
    if home_win > draw and home_win > away_win:
        prediction = 'home_win'
        confidence = home_win * 100
    elif away_win > draw and away_win > home_win:
        prediction = 'away_win'
        confidence = away_win * 100
    else:
        prediction = 'draw'
        confidence = draw * 100
    
    return {
        'prediction': prediction,
        'home_win_probability': float(home_win),
        'draw_probability': float(draw),
        'away_win_probability': float(away_win),
        'confidence': float(avg_confidence),
        'home_team_trend': home_prediction['trend'],
        'away_team_trend': away_prediction['trend'],
        'home_team_form': home_prediction,
        'away_team_form': away_prediction,
        'method': f"LSTM ({home_prediction['prediction_method']})"
    }


# Test fonksiyonu
if __name__ == "__main__":
    print("🧠 LSTM Maç Tahmin Modülü Test")
    print("=" * 60)
    
    # Örnek veri oluştur
    sample_matches = []
    for i in range(15):
        sample_matches.append({
            'goals_scored': np.random.randint(0, 4),
            'goals_conceded': np.random.randint(0, 3),
            'result': np.random.choice(['W', 'D', 'L'], p=[0.4, 0.3, 0.3]),
            'is_home': i % 2 == 0,
            'opponent_elo': 1500 + np.random.randint(-200, 200),
            'days_since_last': 7
        })
    
    # Model oluştur
    predictor = LSTMMatchPredictor(sequence_length=10)
    
    # Tahmin yap
    prediction = predictor.predict(sample_matches)
    
    print(f"\n📊 Tahmin Sonuçları:")
    print(f"   Kazanma Olasılığı: {prediction['win_probability']*100:.1f}%")
    print(f"   Beraberlik Olasılığı: {prediction['draw_probability']*100:.1f}%")
    print(f"   Kaybetme Olasılığı: {prediction['loss_probability']*100:.1f}%")
    print(f"   Güven Skoru: {prediction['confidence']:.1f}%")
    print(f"   Trend: {prediction['trend']}")
    print(f"   Metod: {prediction['prediction_method']}")
    
    print("\n" + "=" * 60)
    if KERAS_AVAILABLE:
        print("✅ TensorFlow/Keras kullanılabilir - LSTM modeli aktif")
    else:
        print("⚠️ TensorFlow/Keras yok - İstatistiksel model kullanılıyor")
        print("   Yüklemek için: pip install tensorflow")
