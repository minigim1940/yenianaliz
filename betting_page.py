"""
Value Bet Detector Interaktif Sayfa
"""

import streamlit as st
from value_bet_detector import (
    BettingOdds, ValueBetDetector, ArbitrageDetector, 
    BankrollManager, KellyCriterion
)
from betting_display import (
    display_value_bets_table, display_odds_comparison,
    display_kelly_calculator, display_arbitrage_opportunity,
    display_bankroll_tracker
)


def render_betting_page():
    """Value Bet Detector ana sayfası"""
    
    # Session state temizleme (eski versiyon uyumluluk)
    if 'bankroll_manager' in st.session_state:
        manager = st.session_state.bankroll_manager
        # Eski versiyonda kelly_fraction varsa sil
        if hasattr(manager, 'kelly_fraction'):
            del st.session_state.bankroll_manager
    
    st.title("💎 Value Bet Detector")
    st.markdown("""
    Bu modül, bahis oranlarını matematiksel olarak analiz eder ve **pozitif beklenen değer** (Expected Value) sunan
    fırsatları bulur. Kelly Criterion kullanarak optimal bahis miktarını hesaplar.
    """)
    
    # Ana açıklama bölümü
    with st.expander("📖 Value Bet Nedir? Nasıl Kullanılır?", expanded=False):
        st.markdown("""
        ### 💎 Value Bet Nedir?
        
        **Value Bet**, bahisçinin sunduğu oranın gerçek olasılıktan **daha yüksek** olduğu bahislerdir. 
        Uzun vadede kar garantisi sunan matematiksel bir avantajdır.
        
        #### 🆕 Yeni Bahis Türleri Eklendi!
        
        🕐 **İlk Yarı Sonuçları:** İlk 45 dakikadaki sonuç (1Y - Ev Sahibi/Beraberlik/Deplasman)
        
        ⚽ **Alt/Üst Bahisleri:**
        - **2.5 Alt/Üst:** Maçta toplam 3+ gol atılır mı?
        
        💡 **Avantaj:** Farklı pazarlarda daha fazla value bet fırsatı!
        
        #### 🎯 Temel Kavramlar
        
        **1. Expected Value (EV) - Beklenen Değer**
        ```
        EV = (Gerçek Olasılık × Oran) - 1
        ```
        - EV > 0: Uzun vadede kar
        - EV < 0: Uzun vadede zarar
        - EV = 0: Başabaş
        
        **Örnek:**
        - Bahisçi oranı: 2.10 (implied %47.6)
        - Model tahmini: %55 
        - EV = (0.55 × 2.10) - 1 = +0.155 (%15.5) ✅
        
        **2. Value Percentage**
        ```
        Value % = ((Gerçek Olasılık - Implied Olasılık) / Implied Olasılık) × 100
        ```
        - %5+: İyi value
        - %10+: Mükemmel value
        - %15+: Çok nadir, dikkatli ol!
        
        **3. Kelly Criterion - Optimal Bahis Miktarı**
        ```
        Kelly % = ((Oran × Gerçek Olasılık - 1) / (Oran - 1)) × 100
        ```
        - Bankroll'unuzun ne kadarını bahse yatırmanız gerektiğini hesaplar
        - **Fractional Kelly** kullanılır (Quarter Kelly önerilen)
        
        #### 💡 Nasıl Kullanılır?
        
        **TAB 1: Tek Maç Analizi** 🔍
        
        1. **Model Tahminlerini Girin:**
           - **Maç Sonucu (90 dk):** Ev Sahibi %45, Beraberlik %30, Deplasman %25
           - **İlk Yarı Sonucu:** 1Y Ev Sahibi %35, 1Y Beraberlik %45, 1Y Deplasman %20  
           - **Alt/Üst Tahminleri:** 2.5 Üst %55
        
        2. **Bahisçi Oranlarını Girin:**
           - **Ana Sonuç:** Ev Sahibi 2.10, Beraberlik 3.40, Deplasman 3.80
           - **İlk Yarı:** 1Y Ev Sahibi 2.80, 1Y Beraberlik 2.20, 1Y Deplasman 4.50
           - **Alt/Üst:** 2.5 Üst 1.85, 2.5 Alt 1.95
        
        3. **Analiz Et:**
           - **Tüm bahis türlerinde** value betler aranır
           - EV, Value %, Kelly stake hesaplanır
           - Rating verilir (⭐⭐⭐)
           - **Kategori bazlı** karşılaştırma grafiği
        
        4. **Kararı Verin:**
           - EV %5+: Bahis yapılabilir
           - Value %10+: İyi fırsat
           - **Farklı bahis türlerinden** en iyiyi seç
        
        **TAB 2: Çoklu Bahisçi Karşılaştırma** 📊
        
        1. **Farklı Bahisçilerin Oranlarını Girin** (2-5 bahisçi)
        2. **En İyi Oranları Otomatik Seç**
        3. **Arbitrage Fırsatı Ara:**
           - Farklı bahisçilerde farklı sonuçlara bahis
           - Garanti kar hesapla
           - Stake dağılımını gör
        
        **TAB 3: Value Bet Simulator** 🎲
        
        1. **Simülasyon Parametreleri:**
           - Bahis sayısı: 100
           - Kazanma oranı: %55
           - Ortalama oran: 2.1
           - Ortalama value: %5
        
        2. **Simülasyonu Çalıştır:**
           - Kelly Criterion ile bahis yap
           - 100 bahis simüle et
           - Bankroll gelişimini gör
        
        3. **ROI Analizi:**
           - Final bankroll
           - Toplam kar/zarar
           - Win rate
        
        **TAB 4: Bankroll Tracker** 📈
        
        1. **Gerçek Bahislerinizi Kaydedin:**
           - Bahis açıklaması
           - Stake miktarı
           - Oran
           - Kazandı mı?
        
        2. **İstatistikleri Takip Edin:**
           - Win rate
           - ROI
           - Profit/Loss grafikleri
        
        #### 🎯 Kelly Criterion Stratejileri
        
        | Strateji | Yüzde | Risk | Önerilen Durum |
        |----------|-------|------|----------------|
        | **Full Kelly** | %100 | 🔴 Çok Yüksek | Sadece profesyoneller |
        | **Half Kelly** | %50 | 🟡 Orta | Deneyimli bahisçiler |
        | **Quarter Kelly** | %25 | 🟢 Dengeli | ✅ **ÖNERİLEN** |
        | **Conservative** | %12.5 | 🟢 Düşük | Yeni başlayanlar |
        
        #### ⚠️ Önemli Uyarılar
        
        1. **Model Doğruluğu**: Tahminleriniz %100 doğru değilse value bet değildir!
        2. **Bahisçi Limitleri**: Sürekli kazananları kısıtlayabilir
        3. **Oran Değişimi**: Oranlar hızla değişebilir
        4. **Variance**: Kısa vadede şanssızlık olabilir
        5. **Disiplin**: Kelly'e sadık kalın, duygusal karar vermeyin
        
        #### 📊 Başarı Metrikleri
        
        **İyi Value Betting:**
        - ROI: %5-15 (uzun vadede)
        - Win Rate: %50-60
        - Bankroll Büyümesi: %10-30/yıl
        
        **Kötü Signaller:**
        - Sürekli negatif EV bahisler
        - %40 altı win rate
        - Aşırı stake değişimleri
        
        #### 🚀 İleri Seviye İpuçları
        
        1. **CLV (Closing Line Value)**: Kapanış oranlarına göre value kontrolü
        2. **Soft Bookmakers**: Daha yüksek limitler
        3. **Arbitrage ile Combo**: Kesin + Value bahis karması
        4. **Multi-Way Arbitrage**: 3+ sonuçta arbitrage
        5. **Asian Handicap**: Daha az marj, daha fazla value
        """)
    
    st.markdown("""
    """)
    
    # Sidebar - Bankroll ayarları
    with st.sidebar:
        st.markdown("### ⚙️ Ayarlar")
        
        bankroll = st.number_input(
            "💰 Bankroll (TL)",
            min_value=100.0,
            max_value=1000000.0,
            value=1000.0,
            step=100.0,
            help="Toplam bahis bütçeniz"
        )
        
        min_value = st.slider(
            "📊 Min Value % ",
            min_value=0.0,
            max_value=20.0,
            value=5.0,
            step=1.0,
            help="Value yüzdesi eşiği"
        )
        
        min_ev = st.slider(
            "📈 Min Expected Value %",
            min_value=0.0,
            max_value=20.0,
            value=3.0,
            step=1.0,
            help="Beklenen değer eşiği"
        )
        
        kelly_fraction = st.selectbox(
            "🎯 Kelly Stratejisi",
            options=[0.5, 0.25, 0.125],
            format_func=lambda x: {
                0.5: "Half Kelly (Dengeli)",
                0.25: "Quarter Kelly (Önerilen)",
                0.125: "1/8 Kelly (Güvenli)"
            }[x],
            index=1
        )
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔍 Tek Maç Analizi",
        "📊 Çoklu Bahisçi Karşılaştırma",
        "🎲 Value Bet Simulator",
        "📈 Bankroll Tracker"
    ])
    
    # TAB 1: Tek Maç Analizi
    with tab1:
        render_single_match_analysis(bankroll, min_value, min_ev, kelly_fraction)
    
    # TAB 2: Çoklu Bahisçi
    with tab2:
        render_multiple_bookmaker_analysis(bankroll)
    
    # TAB 3: Simulator
    with tab3:
        render_value_bet_simulator(bankroll, kelly_fraction)
    
    # TAB 4: Bankroll Tracker
    with tab4:
        render_bankroll_tracker(bankroll)


def render_single_match_analysis(bankroll, min_value, min_ev, kelly_fraction):
    """Tek maç value bet analizi"""
    
    st.markdown("### 🔍 Maç ve Oranlar")
    
    col1, col2 = st.columns(2)
    
    with col1:
        home_team = st.text_input("🏠 Ev Sahibi Takım", value="Barcelona")
        away_team = st.text_input("✈️ Deplasman Takımı", value="Real Madrid")
    
    with col2:
        st.markdown("#### 📊 Model Tahminleri (%)")
        home_prob = st.slider("Ev Sahibi Galibiyeti", 0, 100, 45) / 100
        draw_prob = st.slider("Beraberlik", 0, 100, 30) / 100
        away_prob = st.slider("Deplasman Galibiyeti", 0, 100, 25) / 100
        
        # İlk yarı tahminleri
        st.markdown("##### 🕐 İlk Yarı Tahminleri")
        ht_home_prob = st.slider("1Y - Ev Sahibi", 0, 100, 35) / 100
        ht_draw_prob = st.slider("1Y - Beraberlik", 0, 100, 45) / 100
        ht_away_prob = st.slider("1Y - Deplasman", 0, 100, 20) / 100
        
        # Alt/Üst tahminleri (sadece 2.5)
        st.markdown("##### ⚽ Gol Tahminleri")
        over_2_5_prob = st.slider("2.5 Üst Olasılık", 0, 100, 55) / 100
    
    # Olasılık kontrolü
    total_prob = home_prob + draw_prob + away_prob
    if abs(total_prob - 1.0) > 0.05:
        st.warning(f"⚠️ Toplam olasılık %{total_prob*100:.1f} - %100'e yakın olmalı!")
    
    st.markdown("---")
    st.markdown("### 💵 Bahisçi Oranları")
    
    # Ana maç sonucu
    st.markdown("#### 🏆 Maç Sonucu (90 dk)")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        home_odds = st.number_input("🏠 Ev Sahibi", min_value=1.01, max_value=50.0, value=2.10, step=0.05)
    
    with col2:
        draw_odds = st.number_input("🤝 Beraberlik", min_value=1.01, max_value=50.0, value=3.40, step=0.05)
    
    with col3:
        away_odds = st.number_input("✈️ Deplasman", min_value=1.01, max_value=50.0, value=3.80, step=0.05)
    
    # İlk yarı sonucu
    st.markdown("#### 🕐 İlk Yarı Sonucu")
    ht_col1, ht_col2, ht_col3 = st.columns(3)
    
    with ht_col1:
        ht_home_odds = st.number_input("🏠 1Y - Ev Sahibi", min_value=1.01, max_value=50.0, value=2.80, step=0.05, key="ht_home")
    
    with ht_col2:
        ht_draw_odds = st.number_input("🤝 1Y - Beraberlik", min_value=1.01, max_value=50.0, value=2.20, step=0.05, key="ht_draw")
    
    with ht_col3:
        ht_away_odds = st.number_input("✈️ 1Y - Deplasman", min_value=1.01, max_value=50.0, value=4.50, step=0.05, key="ht_away")
    
    # Alt/Üst bahisleri (sadece 2.5)
    st.markdown("#### ⚽ Alt/Üst Bahisleri")
    ou_col1, ou_col2 = st.columns(2)
    
    with ou_col1:
        over_2_5_odds = st.number_input("⬆️ 2.5 Üst", min_value=1.01, max_value=50.0, value=1.85, step=0.05, key="over_2_5")
    
    with ou_col2:
        under_2_5_odds = st.number_input("⬇️ 2.5 Alt", min_value=1.01, max_value=50.0, value=1.95, step=0.05, key="under_2_5")
    
    if st.button("🔍 Analiz Et", type="primary", use_container_width=True):
        # BettingOdds oluştur (yeni alanlarla)
        betting_odds = BettingOdds(
            home_win=home_odds,
            draw=draw_odds,
            away_win=away_odds,
            # İlk yarı oranları
            ht_home_win=ht_home_odds,
            ht_draw=ht_draw_odds,
            ht_away_win=ht_away_odds,
            # Alt/üst oranları (sadece 2.5)
            over_2_5=over_2_5_odds,
            under_2_5=under_2_5_odds
        )
        
        # Model tahminleri (yeni alanlarla)
        true_probs = {
            # Maç sonucu
            'home_win': home_prob,
            'draw': draw_prob,
            'away_win': away_prob,
            # İlk yarı
            'ht_home_win': ht_home_prob,
            'ht_draw': ht_draw_prob,
            'ht_away_win': ht_away_prob,
            # Alt/üst (sadece 2.5)
            'over_2_5': over_2_5_prob,
            'under_2_5': 1 - over_2_5_prob,  # Alt = 1 - Üst
            'under_3_5': 1 - over_3_5_prob
        }
        
        # Karşılaştırma
        display_odds_comparison(true_probs, betting_odds)
        
        # Value bet ara
        detector = ValueBetDetector(min_value=min_value, min_ev=min_ev)
        value_bets = detector.find_value_bets(
            betting_odds=betting_odds,
            true_probabilities=true_probs,
            kelly_fraction=kelly_fraction
        )
        
        # Sonuçları göster
        display_value_bets_table(value_bets)
        
        # En iyi beti varsa Kelly hesapla
        if value_bets:
            st.markdown("---")
            display_kelly_calculator(bankroll, value_bets[0])


def render_multiple_bookmaker_analysis(bankroll):
    """Çoklu bahisçi arbitrage analizi"""
    
    st.markdown("### 🏦 Farklı Bahisçilerin Oranları")
    st.info("Farklı bahisçilerden en iyi oranları girin. Arbitrage fırsatı aranacak.")
    
    # Bahisçi sayısı
    num_bookmakers = st.number_input("Bahisçi Sayısı", min_value=2, max_value=5, value=3)
    
    # Oranları topla
    all_odds = {
        'home_win': [],
        'draw': [],
        'away_win': []
    }
    
    for i in range(num_bookmakers):
        st.markdown(f"#### 🏦 Bahisçi {i+1}")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            home = st.number_input(f"Ev Sahibi", min_value=1.01, max_value=50.0, value=2.0 + i*0.1, key=f"home_{i}")
            all_odds['home_win'].append(home)
        
        with col2:
            draw = st.number_input(f"Beraberlik", min_value=1.01, max_value=50.0, value=3.2 + i*0.1, key=f"draw_{i}")
            all_odds['draw'].append(draw)
        
        with col3:
            away = st.number_input(f"Deplasman", min_value=1.01, max_value=50.0, value=3.5 + i*0.1, key=f"away_{i}")
            all_odds['away_win'].append(away)
    
    if st.button("🔍 Arbitrage Ara", type="primary", use_container_width=True):
        # En iyi oranları bul
        best_odds_dict = {
            'home_win': max(all_odds['home_win']),
            'draw': max(all_odds['draw']),
            'away_win': max(all_odds['away_win'])
        }
        
        # BettingOdds oluştur
        best_odds = BettingOdds(**best_odds_dict)
        
        # Arbitrage analizi
        detector = ArbitrageDetector()
        arb_data = detector.detect_arbitrage(best_odds, total_stake=100.0)
        
        # Sonuç
        display_arbitrage_opportunity(arb_data)
        
        # En iyi oranlar tablosu
        st.markdown("---")
        st.markdown("### 📊 En İyi Oranlar")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("🏠 Ev Sahibi", f"{best_odds_dict['home_win']:.2f}",
                     help=f"En düşük: {min(all_odds['home_win']):.2f}")
        
        with col2:
            st.metric("🤝 Beraberlik", f"{best_odds_dict['draw']:.2f}",
                     help=f"En düşük: {min(all_odds['draw']):.2f}")
        
        with col3:
            st.metric("✈️ Deplasman", f"{best_odds_dict['away_win']:.2f}",
                     help=f"En düşük: {min(all_odds['away_win']):.2f}")


def render_value_bet_simulator(bankroll, kelly_fraction):
    """Value bet simülasyonu"""
    
    st.markdown("### 🎲 Value Bet Simulator")
    st.markdown("""
    Bu simülatör, value betting stratejisinin uzun vadede nasıl çalıştığını gösterir.
    Kelly Criterion kullanarak optimal stake yönetimi ile bankroll gelişimini simüle eder.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        num_bets = st.slider("Simüle Edilecek Bahis Sayısı", 10, 1000, 100, 10)
        win_rate = st.slider("Kazanma Oranı (%)", 30, 70, 55, 5) / 100
    
    with col2:
        avg_odds = st.slider("Ortalama Oran", 1.5, 5.0, 2.1, 0.1)
        avg_value = st.slider("Ortalama Value (%)", 1.0, 20.0, 5.0, 1.0)
    
    if st.button("▶️ Simülasyonu Başlat", type="primary", use_container_width=True):
        # Manager oluştur
        manager = BankrollManager(initial_bankroll=bankroll)
        
        import random
        
        # Simülasyon
        with st.spinner("Simülasyon çalışıyor..."):
            for i in range(num_bets):
                # Rastgele value bet oluştur
                true_prob = win_rate + random.uniform(-0.05, 0.05)
                true_prob = max(0.1, min(0.9, true_prob))  # Sınırla
                
                odds = avg_odds + random.uniform(-0.3, 0.3)
                odds = max(1.5, odds)
                
                # Kelly stake hesapla
                kelly = KellyCriterion(kelly_fraction=kelly_fraction)
                kelly_pct = kelly.calculate(
                    win_probability=true_prob,
                    odds=odds
                )
                
                stake = manager.calculate_stake(kelly_pct)
                
                # Sonuç belirle (win_rate'e göre)
                won = random.random() < win_rate
                
                # Kaydet
                manager.record_bet(
                    outcome=f"Bet {i+1}",
                    stake=stake,
                    odds=odds,
                    won=won
                )
        
        # Sonuçları göster
        st.success("✅ Simülasyon tamamlandı!")
        
        display_bankroll_tracker(manager)
        
        # Özet
        stats = manager.get_statistics()
        
        st.markdown("---")
        st.markdown("### 📊 Simülasyon Özeti")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Final Bankroll",
                f"{stats['current_bankroll']:.2f} TL",
                delta=f"{stats['total_profit']:.2f} TL"
            )
        
        with col2:
            st.metric(
                "ROI",
                f"{stats['roi']:.1f}%",
                delta=f"{stats['win_rate']:.1f}% kazanma oranı"
            )
        
        with col3:
            growth = ((stats['current_bankroll'] - bankroll) / bankroll) * 100
            st.metric(
                "Bankroll Büyümesi",
                f"{growth:+.1f}%",
                delta=f"{stats['wins']}/{stats['total_bets']} kazandı"
            )


def render_bankroll_tracker(bankroll):
    """Bankroll takip sayfası"""
    
    st.markdown("### 📈 Bankroll Tracker")
    st.info("Gerçek bahislerinizi buradan takip edebilirsiniz.")
    
    # Session state'te manager oluştur
    if 'bankroll_manager' not in st.session_state:
        st.session_state.bankroll_manager = BankrollManager(
            initial_bankroll=bankroll
        )
    
    manager = st.session_state.bankroll_manager
    
    # Yeni bahis ekle
    with st.expander("➕ Yeni Bahis Ekle"):
        col1, col2 = st.columns(2)
        
        with col1:
            bet_outcome = st.text_input("Bahis Açıklaması", "Örn: Barcelona - Real Madrid (Ev Sahibi)")
            bet_stake = st.number_input("Bahis Miktarı (TL)", min_value=1.0, value=10.0, step=1.0)
        
        with col2:
            bet_odds = st.number_input("Oran", min_value=1.01, max_value=50.0, value=2.0, step=0.05)
            bet_won = st.checkbox("Kazandı mı?")
        
        if st.button("💾 Bahsi Kaydet"):
            manager.record_bet(
                outcome=bet_outcome,
                stake=bet_stake,
                odds=bet_odds,
                won=bet_won
            )
            st.success("✅ Bahis kaydedildi!")
            st.rerun()
    
    # Geçmişi göster
    display_bankroll_tracker(manager)
    
    # Reset butonu
    if st.button("🔄 Geçmişi Temizle", type="secondary"):
        st.session_state.bankroll_manager = BankrollManager(
            initial_bankroll=bankroll
        )
        st.rerun()


# Test
if __name__ == "__main__":
    st.set_page_config(page_title="Value Bet Detector", page_icon="💎", layout="wide")
    render_betting_page()
