"""
Poisson & Monte Carlo Simülasyon Streamlit Sayfası
"""

import streamlit as st
from poisson_simulator import PoissonMatchSimulator, MonteCarloSimulator, compare_poisson_vs_monte_carlo
from monte_carlo_display import (display_probability_matrix, display_match_outcome_probabilities,
                                 display_over_under_analysis, display_btts_analysis,
                                 display_monte_carlo_distribution)
import time


def display_simulation_page():
    """Poisson & Monte Carlo simülasyon sayfası"""
    
    st.markdown("""
    <h1 style='text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
               -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
               background-clip: text; font-size: 2.5em; margin: 10px 0;'>
        🎲 Poisson & Monte Carlo Simülasyon
    </h1>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Ana açıklama bölümü
    with st.expander("📖 Poisson & Monte Carlo Nedir? Nasıl Kullanılır?", expanded=False):
        st.markdown("""
        ### 🎲 Poisson & Monte Carlo Simülasyonu Nedir?
        
        **İki güçlü istatistiksel yöntemin birleşimi** ile maç sonuçlarını tahmin eder:
        
        #### 📊 1. Poisson Dağılımı
        
        Futbol maçlarında **gol sayılarını** modellemek için kullanılan matematiksel formül.
        
        **Ne İşe Yarar:**
        - ⚽ Her takımın atacağı gol sayısının olasılığını hesaplar
        - 📈 0-0, 1-1, 2-1 gibi **tüm skor olasılıklarını** bulur
        - 🎯 Matematiksel olarak **doğrulanmış** bir yöntemdir
        
        **Örnek:**
        - Barcelona beklenen gol: 2.1
        - Real Madrid beklenen gol: 1.5
        - Poisson ile: 2-1 olasılığı %14.3
        
        #### 🎰 2. Monte Carlo Simülasyonu
        
        Maçı **10,000+ kez simüle ederek** tüm olası sonuçları bulur.
        
        **Nasıl Çalışır:**
        1. 🎲 Her simülasyonda rastgele bir maç sonucu üret
        2. 🔄 Bunu 10,000 kez tekrarla
        3. 📊 Sonuçların dağılımını analiz et
        4. 📈 En olası skorları ve olasılıkları bul
        
        **Avantajları:**
        - ✅ Rastgelelik faktörünü dahil eder
        - ✅ Çok nadir skorları da tespit eder
        - ✅ Görselleştirmesi kolaydır
        
        #### 💡 Ne İşe Yarar?
        
        1. **Skor Tahmini**: En olası maç skorlarını bulun
        2. **Alt/Üst Analizi**: 2.5, 3.5 üst/alt bahisleri için olasılıklar
        3. **BTTS (Her İki Takım Gol Atar mı)**: İki takımın da gol atma olasılığı
        4. **Olasılık Matrisi**: Tüm skor kombinasyonlarını görün
        5. **Bahis Stratejisi**: Değerli bahisleri tespit edin
        
        #### 📈 Nasıl Kullanılır?
        
        **Adım 1: Takım Verilerini Girin**
        - Ev sahibi ve deplasman takımlarının ortalama gol istatistikleri
        - Son 5-10 maçın verileri yeterlidir
        
        **Adım 2: Simülasyonu Çalıştırın**
        - "Simülasyonu Başlat" butonuna tıklayın
        - 10,000 simülasyon ~2-3 saniye sürer
        
        **Adım 3: Sonuçları Analiz Edin**
        - 📊 Olasılık matrisini inceleyin (hangi skorlar daha olası?)
        - 🎯 En olası 3 skoru görün
        - 📈 Alt/Üst ve BTTS analizlerini kullanın
        
        **Adım 4: Karşılaştırın**
        - Poisson vs Monte Carlo sonuçlarını karşılaştırın
        - Her iki metodun da uyuştuğu sonuçlar daha güvenilirdir
        
        #### 🎯 Örnek Kullanım Senaryoları:
        
        **Senaryo 1: Value Bet Arama**
        - Poisson: Ev sahibi kazanır %45
        - Bahisçi oranı: 2.50 (implied %40)
        - ✅ Value bet var! (Model > Bahisçi)
        
        **Senaryo 2: Alt/Üst Bahsi**
        - 2.5 Üst olasılığı: %68
        - 2.5 Üst oranı: 1.80 (implied %55)
        - ✅ İyi bahis fırsatı!
        
        **Senaryo 3: BTTS Analizi**
        - Her iki takım gol atar: %62
        - BTTS Var oranı: 1.70 (implied %59)
        - ✅ Küçük value var
        
        #### ⚙️ Ayarlar:
        
        - **Simülasyon Sayısı**: 10,000 (önerilen), daha fazla = daha doğru
        - **Ev Sahibi Avantajı**: Varsayılan %10 bonus
        - **Lambda Düzeltme**: Poisson parametrelerini manuel ayarlayın
        
        #### 📊 Çıktı Göstergeleri:
        
        - 🟢 **Yüksek Olasılık** (>20%): Güvenilir tahmin
        - 🟡 **Orta Olasılık** (10-20%): Makul tahmin
        - 🔴 **Düşük Olasılık** (<10%): Riskli tahmin
        """)
    
    # Teknik detaylar
    with st.expander("ℹ️ Teknik Detaylar", expanded=False):
        st.markdown("""
        ### 📊 Poisson Dağılımı
        
        **Poisson dağılımı**, futbol maçlarında gol sayılarını modellemek için en yaygın kullanılan istatistiksel yöntemdir.
        
        **Temel Prensipler:**
        - Gol sayıları **bağımsız olaylar** olarak kabul edilir
        - Her takım için **lambda (λ)** parametresi hesaplanır (beklenen gol)
        - Olasılık formülü: `P(X=k) = (λ^k * e^-λ) / k!`
        
        **Lambda Hesaplama:**
        ```
        λ_home = (Hücum Gücü / Lig Ort.) * (Rakip Savunma / Lig Ort.) * Lig Ort. * Ev Avantajı
        λ_away = (Hücum Gücü / Lig Ort.) * (Rakip Savunma / Lig Ort.) * Lig Ort.
        ```
        
        ### 🎲 Monte Carlo Simülasyonu
        
        **Monte Carlo**, binlerce maç simülasyonu yaparak **olasılık dağılımını** oluşturur.
        
        **Nasıl Çalışır:**
        1. Her simülasyonda Poisson dağılımından rastgele gol sayısı üretilir
        2. 10,000+ simülasyon yapılır
        3. Sonuçlar toplanarak olasılıklar hesaplanır
        4. Skor dağılımı ve istatistikler elde edilir
        
        **Avantajları:**
        - Gerçek dünya varyasyonunu simüle eder
        - Nadir sonuçları da yakalar
        - Poisson'u doğrular
        - Güven aralıkları verir
        
        ### 🎯 Kullanım Alanları:
        
        - ✅ **1X2 Tahminleri** - Ev sahibi/Beraberlik/Deplasman
        - ✅ **Over/Under** - Toplam gol tahmini
        - ✅ **BTTS** - Karşılıklı gol var/yok
        - ✅ **Correct Score** - Doğru skor tahminleri
        - ✅ **Asian Handicap** - Handikap bahisleri
        """)
    
    st.markdown("---")
    
    # Takım seçimi
    st.markdown("## ⚽ Maç Parametreleri")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🏠 Ev Sahibi Takım")
        home_team = st.text_input("Takım Adı", value="Galatasaray", key="sim_home")
        home_attack = st.slider(
            "Hücum Gücü (maç başı gol)",
            0.5, 4.0, 1.8, 0.1,
            key="home_attack",
            help="Son maçlarda attığı ortalama gol sayısı"
        )
        home_defense = st.slider(
            "Savunma Gücü (maç başı yediği gol)",
            0.2, 3.0, 1.1, 0.1,
            key="home_defense",
            help="Son maçlarda yediği ortalama gol sayısı"
        )
    
    with col2:
        st.markdown("### ✈️ Deplasman Takımı")
        away_team = st.text_input("Takım Adı", value="Fenerbahçe", key="sim_away")
        away_attack = st.slider(
            "Hücum Gücü (maç başı gol)",
            0.5, 4.0, 1.6, 0.1,
            key="away_attack"
        )
        away_defense = st.slider(
            "Savunma Gücü (maç başı yediği gol)",
            0.2, 3.0, 1.3, 0.1,
            key="away_defense"
        )
    
    # Genel parametreler
    st.markdown("### ⚙️ Genel Parametreler")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        league_avg = st.number_input(
            "Lig Ortalama Gol",
            1.0, 4.0, 2.7, 0.1,
            key="league_avg",
            help="Lig genelinde maç başı toplam gol ortalaması"
        )
    
    with col2:
        home_advantage = st.number_input(
            "Ev Sahibi Avantajı",
            1.0, 1.5, 1.15, 0.05,
            key="home_adv",
            help="Ev sahibi avantaj çarpanı (genelde 1.10-1.20)"
        )
    
    with col3:
        n_simulations = st.select_slider(
            "Monte Carlo Simülasyon Sayısı",
            options=[1000, 5000, 10000, 25000, 50000],
            value=10000,
            key="n_sims",
            help="Daha fazla simülasyon = Daha doğru sonuç"
        )
    
    st.markdown("---")
    
    # Simülasyon butonu
    if st.button("🎲 Simülasyonu Başlat", type="primary", use_container_width=True):
        
        # Progress bar
        progress_bar = st.progress(0, text="Hesaplamalar başlatılıyor...")
        
        # Poisson simülatörü
        progress_bar.progress(20, text="Poisson dağılımı hesaplanıyor...")
        time.sleep(0.3)
        
        poisson_sim = PoissonMatchSimulator(
            home_attack=home_attack,
            home_defense=home_defense,
            away_attack=away_attack,
            away_defense=away_defense,
            league_avg_goals=league_avg,
            home_advantage=home_advantage
        )
        
        poisson_results = poisson_sim.calculate_match_probabilities(max_goals=10)
        
        progress_bar.progress(50, text="Monte Carlo simülasyonu çalışıyor...")
        time.sleep(0.3)
        
        # Monte Carlo simülasyonu
        mc_sim = MonteCarloSimulator(poisson_sim)
        mc_results = mc_sim.run_simulation(n_simulations=n_simulations)
        
        progress_bar.progress(100, text="Tamamlandı!")
        time.sleep(0.3)
        progress_bar.empty()
        
        # Başarı mesajı
        st.success(f"✅ {n_simulations:,} simülasyon tamamlandı!")
        
        st.markdown("---")
        
        # Beklenen Goller
        st.markdown("## 🎯 Beklenen Gol Sayıları (Lambda)")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                f"⚽ {home_team}",
                f"{poisson_results['lambda_home']:.2f}",
                help="Ev sahibi takımın beklenen gol sayısı"
            )
        
        with col2:
            st.metric(
                "📊 Toplam",
                f"{poisson_results['lambda_home'] + poisson_results['lambda_away']:.2f}",
                help="Maçta beklenen toplam gol"
            )
        
        with col3:
            st.metric(
                f"⚽ {away_team}",
                f"{poisson_results['lambda_away']:.2f}",
                help="Deplasman takımın beklenen gol sayısı"
            )
        
        st.markdown("---")
        
        # Maç sonucu olasılıkları
        display_match_outcome_probabilities(poisson_results, mc_results, home_team, away_team)
        
        st.markdown("---")
        
        # Olasılık matrisi
        display_probability_matrix(poisson_results['probability_matrix'], max_display=6)
        
        st.markdown("---")
        
        # Over/Under analizi
        display_over_under_analysis(poisson_results, mc_results)
        
        st.markdown("---")
        
        # BTTS analizi
        display_btts_analysis(poisson_results, mc_results)
        
        st.markdown("---")
        
        # Monte Carlo dağılımı
        display_monte_carlo_distribution(mc_results)
        
        st.markdown("---")
        
        # Karşılaştırma tablosu
        st.markdown("### 📋 Poisson vs Monte Carlo Karşılaştırma")
        
        comparison_df = compare_poisson_vs_monte_carlo(poisson_results, mc_results)
        st.dataframe(comparison_df, use_container_width=True, hide_index=True)
        
        # Sonuç özeti
        st.markdown("---")
        st.markdown("## 💡 Tavsiyeler ve Yorumlar")
        
        # En olası sonuç
        max_prob = max(
            poisson_results['home_win'],
            poisson_results['draw'],
            poisson_results['away_win']
        )
        
        if max_prob == poisson_results['home_win']:
            prediction = f"{home_team} Kazanır"
            prob_pct = poisson_results['home_win'] * 100
        elif max_prob == poisson_results['draw']:
            prediction = "Beraberlik"
            prob_pct = poisson_results['draw'] * 100
        else:
            prediction = f"{away_team} Kazanır"
            prob_pct = poisson_results['away_win'] * 100
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.info(f"""
            **🎯 Ana Tahmin:** {prediction} ({prob_pct:.1f}%)
            
            **📊 En Olası Skor:** {poisson_results['most_likely_score'][0]}-{poisson_results['most_likely_score'][1]} 
            ({poisson_results['probability_matrix'][poisson_results['most_likely_score'][0], poisson_results['most_likely_score'][1]]*100:.2f}%)
            
            **⚽ Beklenen Gol:** {poisson_results['lambda_home'] + poisson_results['lambda_away']:.2f}
            """)
        
        with col2:
            # Güvenilirlik skoru
            confidence = max_prob * 100
            
            if confidence > 60:
                confidence_level = "Yüksek"
                confidence_color = "🟢"
            elif confidence > 45:
                confidence_level = "Orta"
                confidence_color = "🟡"
            else:
                confidence_level = "Düşük"
                confidence_color = "🔴"
            
            st.metric(
                "Güven Seviyesi",
                f"{confidence_color} {confidence_level}",
                f"{confidence:.1f}%"
            )
    
    else:
        st.info("👆 Parametreleri ayarlayın ve simülasyonu başlatın")
    
    # Alt bilgi
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray; font-size: 0.9em;'>
        <p>⚠️ <b>Uyarı:</b> Bu simülasyonlar istatistiksel modellerdir ve gerçek maç sonucunu garanti etmez.</p>
        <p>Bahis yaparken her zaman sorumlu olun ve kendi araştırmanızı yapın.</p>
    </div>
    """, unsafe_allow_html=True)


# Test
if __name__ == "__main__":
    print("✅ Simülasyon sayfa modülü hazır")
