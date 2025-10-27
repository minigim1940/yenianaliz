"""
LSTM Model Streamlit Sayfası
"""

import streamlit as st
from lstm_predictor import LSTMMatchPredictor, predict_match_with_lstm
from lstm_display import (display_lstm_prediction, display_team_form_analysis,
                          display_lstm_comparison, display_training_history)
from typing import Dict, List
import numpy as np


def display_lstm_page():
    """LSTM model sayfası - demo ve açıklama"""
    
    st.markdown("""
    <h1 style='text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
               -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
               background-clip: text; font-size: 2.5em; margin: 10px 0;'>
        🧠 LSTM Derin Öğrenme Tahmini
    </h1>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Açıklama bölümü
    with st.expander("📖 LSTM Nedir? Nasıl Kullanılır?", expanded=False):
        st.markdown("""
        ### 🧠 LSTM (Long Short-Term Memory) Nedir?
        
        **LSTM**, zaman içinde değişen verileri analiz etmek için geliştirilmiş bir **yapay sinir ağı** türüdür. 
        Futbol maçlarında takımların **geçmiş performanslarını** öğrenerek gelecekteki sonuçları tahmin eder.
        
        #### 🎯 Ne İşe Yarar?
        
        1. **Form Analizi**: Son 10 maçın trendini öğrenir
        2. **Gol Tahmini**: Her iki takım için beklenen gol sayısı
        3. **Sonuç Olasılığı**: Ev sahibi kazanır/Beraberlik/Deplasman kazanır
        4. **Momentum Takibi**: Takımın yükseliş/düşüş trendini yakalar
        
        #### 📊 Nasıl Çalışır?
        
        **Model Girdi Verileri:**
        - 📈 Atılan Goller (Son 10 maç)
        - 📉 Yenilen Goller (Son 10 maç)
        - 🏠 Ev Sahibi Avantajı (1 = Ev, 0 = Deplasman)
        - 🎯 Rakip Gücü (Elo rating bazlı)
        - 📊 Şut İstatistikleri
        - 🔄 Form Trendi
        
        **Model Çıktıları:**
        - ⚽ Beklenen Ev Sahibi Golü
        - ⚽ Beklenen Deplasman Golü
        - 📊 Sonuç Olasılıkları (%)
        - 📈 Güven Skoru
        
        #### 💡 Nasıl Kullanılır?
        
        1. **Demo Kullan**: Aşağıdaki örnek takımlarla modeli test edin
        2. **Gerçek Maç Gir**: İki takım seçip gerçek tahmin alın
        3. **Form Analizi**: Takımların son performansını inceleyin
        4. **Karşılaştır**: LSTM tahminini diğer modellerle karşılaştırın
        
        #### ⚠️ Önemli Notlar:
        
        - 🔄 **Fallback Modu**: TensorFlow yoksa istatistiksel tahmin kullanılır
        - 📊 **Veri Gereksinimi**: En az 10 maçlık geçmiş veri gerekir
        - 🎯 **Güven Skoru**: %70+ güven skorları daha güvenilirdir
        - ⚡ **Gerçek Zamanlı**: Model saniyeler içinde tahmin verir
        
        #### 🆚 Diğer Modellerle Farkı:
        
        | Özellik | LSTM | Poisson | xG |
        |---------|------|---------|-----|
        | **Trend Öğrenme** | ✅ Mükemmel | ❌ Yok | ⚠️ Sınırlı |
        | **Uzun Vade** | ✅ İyi | ⚠️ Orta | ❌ Kısa |
        | **Form Takibi** | ✅ Detaylı | ❌ Yok | ⚠️ Basit |
        | **Hız** | ⚡ Hızlı | ⚡ Çok Hızlı | ⚡ Hızlı |
        """)
    
    # Eski açıklama bölümü
    with st.expander("ℹ️ Teknik Detaylar", expanded=False):
        st.markdown("""
        ### 🎯 LSTM (Long Short-Term Memory) Nedir?
        
        LSTM, **zaman serisi verileri** için özel olarak tasarlanmış bir **derin öğrenme** algoritmasıdır.
        Futbol maçlarında:
        - ✅ Takımların **form trendlerini** öğrenir
        - ✅ **Uzun vadeli** performans desenlerini yakalar
        - ✅ Ev sahibi/deplasman **avantajını** modeller
        - ✅ Rakip gücüne göre **uyarlanabilir** tahminler yapar
        
        ### 📊 Model Özellikleri:
        
        **Girdi Verileri (Her Maç İçin):**
        - Atılan ve yenilen goller
        - Kazanma/beraberlik/kaybetme sonuçları
        - xG (Expected Goals) değerleri
        - Top hakimiyeti
        - İsabetli şutlar
        - Ev sahibi/deplasman bilgisi
        - Rakip gücü (ELO rating)
        - Son maçtan bu yana geçen süre
        
        **Model Mimarisi:**
        ```
        Bidirectional LSTM (128 units) 
        ↓
        Bidirectional LSTM (64 units)
        ↓
        Dense (64 units) + Dropout
        ↓
        Dense (32 units) + Dropout
        ↓
        Output (3 units): [Win, Draw, Loss]
        ```
        
        **Avantajları:**
        - 📈 Temporal patterns (zaman içindeki değişimleri yakalar)
        - 🎯 Yüksek doğruluk oranı (gerçek verilerle eğitildiğinde)
        - 🔄 Form değişimlerini algılar
        - 💡 Geleneksel modelleri tamamlar
        
        ### ⚠️ Sınırlamalar:
        - Yeterli eğitim verisi gerektirir (minimum 1000+ maç)
        - TensorFlow/Keras kurulumu gerekir
        - Eğitim süresi uzun olabilir
        - Beklenmedik olayları (sakatlıklar, transferler) tahmin edemez
        """)
    
    st.markdown("---")
    
    # Demo bölümü
    st.markdown("## 🎮 Interaktif Demo")
    st.info("💡 **Not:** Bu demo, örnek verilerle çalışır. Gerçek maç tahminleri için model eğitilmeli ve gerçek verilerle beslenmeli.")
    
    # Takım seçimi
    col1, col2 = st.columns(2)
    
    with col1:
        home_team = st.text_input("🏠 Ev Sahibi Takım", value="Galatasaray", key="lstm_home")
    
    with col2:
        away_team = st.text_input("✈️ Deplasman Takımı", value="Fenerbahçe", key="lstm_away")
    
    # Form simülasyonu
    st.markdown("### 📊 Takım Form Parametreleri")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"#### {home_team} Formu")
        home_wins = st.slider(f"{home_team} - Son 10 Maçta Galibiyet", 0, 10, 6, key="home_wins")
        home_draws = st.slider(f"{home_team} - Son 10 Maçta Beraberlik", 0, 10-home_wins, 2, key="home_draws")
        home_goals_avg = st.slider(f"{home_team} - Maç Başı Gol Ortalaması", 0.0, 5.0, 2.1, 0.1, key="home_goals")
    
    with col2:
        st.markdown(f"#### {away_team} Formu")
        away_wins = st.slider(f"{away_team} - Son 10 Maçta Galibiyet", 0, 10, 5, key="away_wins")
        away_draws = st.slider(f"{away_team} - Son 10 Maçta Beraberlik", 0, 10-away_wins, 3, key="away_draws")
        away_goals_avg = st.slider(f"{away_team} - Maç Başı Gol Ortalaması", 0.0, 5.0, 1.8, 0.1, key="away_goals")
    
    if st.button("🔮 LSTM ile Tahmin Et", type="primary", use_container_width=True):
        with st.spinner("🧠 LSTM modeli hesaplıyor..."):
            # Örnek veri oluştur
            home_matches = _generate_sample_matches(
                wins=home_wins, 
                draws=home_draws, 
                goals_avg=home_goals_avg,
                is_home=True
            )
            
            away_matches = _generate_sample_matches(
                wins=away_wins,
                draws=away_draws,
                goals_avg=away_goals_avg,
                is_home=False
            )
            
            # LSTM model
            lstm_model = LSTMMatchPredictor(sequence_length=10)
            
            # Tahmin
            prediction = predict_match_with_lstm(home_matches, away_matches, lstm_model)
            
            # Görselleştirme
            st.success("✅ Tahmin tamamlandı!")
            
            display_lstm_prediction(prediction, home_team, away_team)
            
            st.markdown("---")
            
            # Takım form analizleri
            col1, col2 = st.columns(2)
            
            with col1:
                display_team_form_analysis(prediction['home_team_form'], home_team)
            
            with col2:
                display_team_form_analysis(prediction['away_team_form'], away_team)
            
            # Geleneksel model ile karşılaştırma (simülasyon)
            st.markdown("---")
            traditional_pred = _simulate_traditional_prediction(home_wins, home_draws, away_wins, away_draws)
            display_lstm_comparison(prediction, traditional_pred, home_team, away_team)
    
    # Model eğitimi bölümü
    st.markdown("---")
    st.markdown("## 🎓 Model Eğitimi")
    
    with st.expander("🔧 Kendi Modelinizi Eğitin"):
        st.markdown("""
        ### Model Eğitim Adımları:
        
        1. **Veri Toplama:**
           ```python
           # API'den maç verilerini çekin
           training_data = collect_team_match_history(team_ids, seasons)
           ```
        
        2. **Model Oluşturma:**
           ```python
           from lstm_predictor import LSTMMatchPredictor
           
           model = LSTMMatchPredictor(sequence_length=10)
           ```
        
        3. **Eğitim:**
           ```python
           history = model.train(
               training_data=training_data,
               epochs=50,
               batch_size=32,
               validation_split=0.2
           )
           ```
        
        4. **Model Kaydetme:**
           ```python
           # Model otomatik kaydedilir
           # Yol: ./models/lstm_match_predictor.h5
           ```
        
        5. **Tahmin:**
           ```python
           prediction = model.predict(team_recent_matches)
           ```
        
        ### 📝 Gereksinimler:
        - Python 3.8+
        - TensorFlow 2.x
        - Minimum 1000+ maç verisi
        - GPU önerilir (eğitim hızı için)
        
        ### 💾 Kurulum:
        ```bash
        pip install tensorflow
        pip install keras
        ```
        """)
        
        st.info("⚠️ **Not:** Gerçek model eğitimi için yeterli veri ve hesaplama gücü gereklidir. Bu demo sadece algoritmanın nasıl çalıştığını gösterir.")


def _generate_sample_matches(wins: int, draws: int, goals_avg: float, is_home: bool) -> List[Dict]:
    """Demo için örnek maç verisi oluştur"""
    total_matches = 15
    losses = total_matches - wins - draws
    
    results = ['W'] * wins + ['D'] * draws + ['L'] * losses
    np.random.shuffle(results)
    
    matches = []
    for i, result in enumerate(results):
        # Gol sayıları (sonuca göre)
        if result == 'W':
            goals_scored = max(1, int(np.random.normal(goals_avg * 1.2, 1)))
            goals_conceded = max(0, int(np.random.normal(goals_avg * 0.5, 0.8)))
        elif result == 'D':
            base = max(0, int(np.random.normal(goals_avg * 0.8, 0.8)))
            goals_scored = base
            goals_conceded = base
        else:
            goals_scored = max(0, int(np.random.normal(goals_avg * 0.6, 0.8)))
            goals_conceded = max(1, int(np.random.normal(goals_avg * 1.1, 1)))
        
        matches.append({
            'goals_scored': goals_scored,
            'goals_conceded': goals_conceded,
            'result': result,
            'xg_for': goals_scored * np.random.uniform(0.8, 1.2),
            'xg_against': goals_conceded * np.random.uniform(0.8, 1.2),
            'possession': np.random.uniform(40, 60),
            'shots_on_target': max(0, int(np.random.normal(5, 2))),
            'is_home': is_home,
            'opponent_elo': int(np.random.normal(1500, 200)),
            'days_since_last': 7
        })
    
    return matches


def _simulate_traditional_prediction(home_wins: int, home_draws: int, 
                                     away_wins: int, away_draws: int) -> Dict:
    """Geleneksel model simülasyonu"""
    # Basit win rate hesabı
    total_home = 10
    total_away = 10
    
    home_win_rate = home_wins / total_home
    home_draw_rate = home_draws / total_home
    
    away_win_rate = away_wins / total_away
    away_draw_rate = away_draws / total_away
    
    # Ev sahibi avantajı
    home_advantage = 1.15
    
    # Olasılıklar
    home_win_prob = home_win_rate * home_advantage * (1 - away_win_rate)
    draw_prob = (home_draw_rate + away_draw_rate) / 2
    away_win_prob = away_win_rate * (1 - home_win_rate) / home_advantage
    
    # Normalize
    total = home_win_prob + draw_prob + away_win_prob
    home_win_prob /= total
    draw_prob /= total
    away_win_prob /= total
    
    confidence = max(home_win_prob, draw_prob, away_win_prob) * 100
    
    return {
        'home_win_probability': home_win_prob,
        'draw_probability': draw_prob,
        'away_win_probability': away_win_prob,
        'confidence': confidence,
        'method': 'Geleneksel İstatistik'
    }


# Test
if __name__ == "__main__":
    print("✅ LSTM Sayfa modülü hazır")
