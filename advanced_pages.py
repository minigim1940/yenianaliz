# -*- coding: utf-8 -*-
"""
Advanced Analysis Pages
=======================
xG ve AI Chat sayfaları için fonksiyonlar
"""

import streamlit as st

# Modül import kontrolü
try:
    from advanced_analysis_display import display_xg_analysis, display_momentum_analysis
    from ai_chat_assistant import FootballChatAssistant, create_chat_widget
    ADVANCED_FEATURES_AVAILABLE = True
except ImportError as e:
    print(f"Gelişmiş özellikler yüklenemedi: {e}")
    ADVANCED_FEATURES_AVAILABLE = False


def display_xg_analysis_page():
    """xG Analizi sayfası"""
    st.title("⚽ xG (Expected Goals) Analizi")
    st.markdown("### Gelişmiş Beklenen Gol Hesaplama Sistemi")
    
    if not ADVANCED_FEATURES_AVAILABLE:
        st.error("⚠️ Gelişmiş analiz modülleri yüklenemedi. Lütfen gerekli dosyaları kontrol edin.")
        st.info("Eksik dosyalar: xg_calculator.py, advanced_analysis_display.py")
        return
    
    # Açıklama bölümü
    with st.expander("📖 xG Nedir? Nasıl Kullanılır?", expanded=False):
        st.markdown("""
        ### 🎯 Expected Goals (xG) Nedir?
        
        **xG (Expected Goals)**, bir şutun gol olma olasılığını 0 ile 1 arasında bir değerle ifade eden istatistiksel bir metriktir.
        
        #### 📊 Nasıl Hesaplanır?
        
        xG hesaplaması şu faktörlere dayanır:
        - **📍 Şut Pozisyonu**: Kaleye yakınlık, açı
        - **🎯 Şut Bölgesi**: Ceza sahası içi/dışı
        - **👟 Şut Türü**: Ayak, kafa, serbest vuruş
        - **🏠 Ev Sahibi Avantajı**: İstatistiksel performans farkı
        - **🛡️ Savunma Kalitesi**: Rakip defansın gücü
        
        #### 💡 Ne İşe Yarar?
        
        1. **Performans Analizi**: Takımın gerçek gollerini beklenen gollerle karşılaştırarak şansın etkisini görün
        2. **Şutör Değerlendirme**: Oyuncuların bitiricilik kalitesini ölçün (Gol > xG = İyi bitirici)
        3. **Taktik Analiz**: Hangi bölgelerden daha kaliteli pozisyon yaratıldığını görün
        4. **Tahmin**: Gelecek performansı tahmin etmek için kullanın (xG, golden daha tutarlıdır)
        
        #### 🔢 Örnek Değerler:
        
        - **0.01-0.10**: Çok zor şut (uzak mesafe, dar açı)
        - **0.10-0.30**: Orta zorlukta şut
        - **0.30-0.60**: İyi pozisyon
        - **0.60-1.00**: Büyük fırsat (penaltı ~0.76)
        
        #### 📈 Nasıl Kullanılır?
        
        1. Aşağıdaki demo ile farklı pozisyonları test edin
        2. Gerçek maç verilerini girerek takım performansını analiz edin
        3. xG değerlerini gerçek gollerle karşılaştırın
        4. Şutörlerin bitiricilik yüzdesini hesaplayın
        """)
    
    st.info("💡 **Not:** xG analizi için maç istatistiklerini manuel olarak girebilir veya gerçek maç verilerini kullanabilirsiniz.")
    
    # Demo fixture data
    demo_fixture = {
        'home_team': 'Galatasaray',
        'away_team': 'Fenerbahçe',
        'home_goals': 0,
        'away_goals': 0,
        'home_stats': {
            'shots_total': 15,
            'shots_on_target': 8,
            'shots_inside_box': 10,
            'shots_outside_box': 5,
            'is_home': True,
            'defense_rating': 70
        },
        'away_stats': {
            'shots_total': 12,
            'shots_on_target': 5,
            'shots_inside_box': 7,
            'shots_outside_box': 5,
            'defense_rating': 75
        }
    }
    
    # Kullanıcı girişi
    with st.expander("⚙️ Maç Ayarları", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            demo_fixture['home_team'] = st.text_input("Ev Sahibi Takım", value=demo_fixture['home_team'])
            demo_fixture['home_goals'] = st.number_input("Ev Sahibi Goller", min_value=0, max_value=20, value=0)
            demo_fixture['home_stats']['shots_total'] = st.number_input("Ev Sahibi Şutlar", min_value=0, max_value=50, value=15)
            demo_fixture['home_stats']['shots_on_target'] = st.number_input("Ev Sahibi İskala İçi", min_value=0, max_value=50, value=8)
            demo_fixture['home_stats']['shots_inside_box'] = st.number_input("Ev Sahibi Ceza Sahası İçi", min_value=0, max_value=50, value=10)
        
        with col2:
            demo_fixture['away_team'] = st.text_input("Deplasman Takım", value=demo_fixture['away_team'])
            demo_fixture['away_goals'] = st.number_input("Deplasman Goller", min_value=0, max_value=20, value=0)
            demo_fixture['away_stats']['shots_total'] = st.number_input("Deplasman Şutlar", min_value=0, max_value=50, value=12)
            demo_fixture['away_stats']['shots_on_target'] = st.number_input("Deplasman İskala İçi", min_value=0, max_value=50, value=5)
            demo_fixture['away_stats']['shots_inside_box'] = st.number_input("Deplasman Ceza Sahası İçi", min_value=0, max_value=50, value=7)
    
    # Analiz göster
    try:
        display_xg_analysis(demo_fixture)
    except Exception as e:
        st.error(f"xG analizi hatası: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


def display_ai_chat_page():
    """AI Sohbet Asistanı sayfası"""
    st.title("🤖 AI Futbol Asistanı")
    st.markdown("### Kural Tabanlı Futbol Sohbet Sistemi")
    
    if not ADVANCED_FEATURES_AVAILABLE:
        st.error("⚠️ AI asistan modülü yüklenemedi. Lütfen gerekli dosyaları kontrol edin.")
        st.info("Eksik dosyalar: ai_chat_assistant.py")
        return
    
    # Açıklama bölümü
    with st.expander("📖 AI Asistan Nedir? Nasıl Kullanılır?", expanded=False):
        st.markdown("""
        ### 🤖 AI Futbol Asistanı Nedir?
        
        **Kural tabanlı futbol analiz asistanı**, maç istatistiklerini anlayıp yorumlayan ve size futbol analizinde yardımcı olan bir sohbet botudur.
        
        #### 🎯 Ne İşe Yarar?
        
        1. **Maç Analizi**: Takım performansını, istatistikleri ve trend analizi
        2. **Tahmin Yardımı**: İstatistiklere dayalı maç sonucu tahminleri
        3. **Taktik Bilgisi**: Formasyon ve taktik önerileri
        4. **Oyuncu Karşılaştırma**: İstatistiklere dayalı oyuncu değerlendirmeleri
        5. **Form Analizi**: Takım ve oyuncu form durumu yorumları
        
        #### 💬 Nasıl Kullanılır?
        
        **Örnek Sorular:**
        - "Galatasaray'ın son 5 maçtaki performansı nasıl?"
        - "Barcelona - Real Madrid maçı için tahminin nedir?"
        - "4-3-3 formasyonu nasıl çalışır?"
        - "Messi vs Ronaldo istatistik karşılaştırması"
        - "Premier Lig'de en iyi defans hangisi?"
        
        #### 🔍 Anlayabildiği Konular:
        
        - ✅ Maç tahminleri ve analizleri
        - ✅ Takım performans değerlendirmeleri
        - ✅ Formasyon ve taktik açıklamaları
        - ✅ İstatistiksel karşılaştırmalar
        - ✅ Form ve trend analizleri
        - ✅ Lig ve turnuva bilgileri
        
        #### 🌐 Türkçe Destek:
        
        Asistan **tam Türkçe destek** sunar:
        - Türkçe karakterleri anlayabilir (ğ, ş, ı, ö, ü, ç)
        - Türk takım isimlerini tanır (Galatasaray, Fenerbahçe, Beşiktaş, vb.)
        - Türkçe yanıtlar verir
        
        #### ⚡ Özellikler:
        
        - 🚀 **API Anahtarı Gerektirmez**: Tamamen kural tabanlı
        - 💾 **Sohbet Geçmişi**: Konuşma akışını takip eder
        - 🎯 **Bağlamsal Yanıtlar**: Önceki soruları hatırlar
        - 🔄 **Gerçek Zamanlı**: Anında yanıt verir
        """)
    
    st.info("💡 **Not:** Bu asistan kural tabanlı çalışır ve API anahtarı gerektirmez.")
    
    # AI Asistan oluştur (sadece yerel/kural tabanlı)
    if 'ai_assistant' not in st.session_state:
        st.session_state.ai_assistant = FootballChatAssistant(api_key=None, provider='openai')
    
    # Chat interface
    st.markdown("---")
    
    try:
        create_chat_widget(st.session_state.ai_assistant)
    except Exception as e:
        st.error(f"AI asistan hatası: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
    
    # Bilgilendirme
    with st.expander("ℹ️ AI Asistan Hakkında"):
        st.markdown("""
        ### 🤖 AI Futbol Asistanı Özellikleri:
        
        **Yetenekler:**
        - ⚽ Takım ve oyuncu bilgileri
        - 📊 İstatistik sorguları
        - 🎯 Maç tahminleri
        - 📖 Futbol terimleri açıklamaları
        - 💡 Strateji önerileri
        
        **Örnek Sorular:**
        - "Galatasaray hakkında bilgi ver"
        - "xG nedir ve nasıl hesaplanır?"
        - "Premier League hakkında bilgi"
        - "Momentum nedir?"
        
        **Not:** Bu versiyon kural tabanlı çalışır ve yerel veritabanını kullanır.
        Gelişmiş AI özellikleri için API entegrasyonu eklenebilir.
        """)
