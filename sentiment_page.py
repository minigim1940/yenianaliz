"""
Sosyal Medya Sentiment Analizi Streamlit Sayfası
"""

import streamlit as st
from sentiment_analyzer import TurkishSentimentAnalyzer, SocialMediaMockData, SentimentScore
from sentiment_display import (display_sentiment_gauge, display_sentiment_distribution,
                               display_sentiment_timeline, display_top_posts,
                               display_word_cloud_data, display_source_comparison,
                               display_sentiment_summary)


def display_sentiment_page():
    """Sentiment analizi ana sayfası"""
    
    st.markdown("""
    <h1 style='text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
               -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
               background-clip: text; font-size: 2.5em; margin: 10px 0;'>
        📱 Sosyal Medya Sentiment Analizi
    </h1>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Açıklama bölümü
    with st.expander("📖 Sentiment Analizi Nedir? Nasıl Kullanılır?", expanded=False):
        st.markdown("""
        ### 📱 Sosyal Medya Sentiment Analizi Nedir?
        
        **Sentiment Analizi**, sosyal medyada (Twitter, Reddit) takım ve oyuncular hakkında yazılan 
        yorumların **duygusal tonunu** (pozitif/negatif/nötr) analiz eden yapay zeka tekniğidir.
        
        #### 🎯 Ne İşe Yarar?
        
        1. **Taraftar Duygusu**: Taraftarların takıma/oyuncuya bakış açısı
        2. **Trend Takibi**: Zaman içinde duygu değişimi
        3. **Kriz Tespiti**: Ani negatif artışlar (sakatlık, yenilgi, vb.)
        4. **Performans İlişkisi**: Sosyal medya duygusu ile maç performansı korelasyonu
        5. **Transfer Değerlendirmesi**: Yeni transfere taraftar tepkisi
        
        #### 📊 Nasıl Çalışır?
        
        **Türkçe Kural Tabanlı Analiz:**
        1. 📝 Sosyal medya postları toplanır
        2. 🔍 Pozitif/Negatif kelimeler tespit edilir
        3. 😊 Emoji sentiment'i hesaplanır
        4. 📈 Genel duygu skoru (-1 ile +1 arası) çıkarılır
        5. 📊 Görselleştirmeler oluşturulur
        
        #### 💡 Nasıl Kullanılır?
        
        **TAB 1: Takım Analizi** ⚽
        1. Takım adını girin (Galatasaray, Fenerbahçe, vb.)
        2. "Analizi Başlat" butonuna tıklayın
        3. Son 48 saatin postları analiz edilir
        4. Genel duygu, trend, popüler postlar görülür
        
        **TAB 2: Oyuncu Analizi** 👤
        1. Oyuncu adını girin (Messi, Ronaldo, vb.)
        2. Oyuncu hakkındaki yorumlar analiz edilir
        3. Performans algısı ölçülür
        
        **TAB 3: Karşılaştırma** 🆚
        1. İki takım/oyuncu seçin
        2. Sentiment skorlarını karşılaştırın
        3. Hangisi daha popüler/sevilmiş görün
        
        **TAB 4: Canlı Demo** 🎲
        1. Kendi cümlenizi yazın
        2. Anında sentiment analizi görün
        3. Türkçe kelime ve emoji etkisini test edin
        
        #### 📈 Sentiment Skorları
        
        | Skor | Etiket | Emoji | Anlamı |
        |------|--------|-------|--------|
        | **+0.5 ile +1.0** | Çok Pozitif | 🟢😊 | Mükemmel duygu |
        | **+0.1 ile +0.5** | Pozitif | 🟢🙂 | İyi duygu |
        | **-0.1 ile +0.1** | Nötr | 🟡😐 | Tarafsız |
        | **-0.5 ile -0.1** | Negatif | 🔴😕 | Kötü duygu |
        | **-1.0 ile -0.5** | Çok Negatif | 🔴😢 | Çok kötü duygu |
        
        #### 🔍 Analiz Göstergeleri
        
        **Gauge (İbre):**
        - 0-100 arası sentiment skoru
        - 50 = Nötr (referans)
        - 50+ = Pozitif bölge
        - 50- = Negatif bölge
        
        **Dağılım Grafiği:**
        - Yeşil: Pozitif yüzde
        - Kırmızı: Negatif yüzde
        - Gri: Nötr yüzde
        
        **Zaman Çizgisi:**
        - Sentiment'in zaman içinde değişimi
        - Ani düşüş/yükseliş trendleri
        - Kritik olayların etkisi
        
        #### ⚠️ Önemli Notlar
        
        1. **Gerçek/Mock Veri**: API anahtarı varsa gerçek Twitter/Reddit verileri, yoksa demo data
        2. **Kural Tabanlı**: NLP model değil, kelime sözlüğü bazlı
        3. **Türkçe Optimized**: Türkçe kelime ve emoji destekli
        4. **API Opsiyonel**: Twitter/Reddit API anahtarı opsiyonel
        5. **Rate Limiting**: Ücretsiz tier: Twitter 1500/ay, Reddit sınırsız
        
        #### 🔑 API Kurulumu (Opsiyonel)
        
        **Twitter API (Ücretsiz):**
        1. developer.twitter.com'a kaydolun
        2. App oluşturun
        3. Bearer Token alın
        4. Streamlit secrets'a ekleyin: `TWITTER_BEARER_TOKEN`
        
        **Reddit API (Ücretsiz):**
        1. reddit.com/prefs/apps'a gidin
        2. "Create App" tıklayın
        3. Client ID ve Secret alın
        4. Streamlit secrets'a ekleyin: `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`
        
        **Not:** API olmadan da çalışır, mock data kullanılır.
        
        #### 🚀 Gelişmiş Özellikler
        
        - **Emoji Analizi**: 😊😢😡 gibi emojilerin sentiment etkisi
        - **Türkçe Normalizasyon**: ğ, ş, ı, ö, ü, ç desteği
        - **Olumsuzluk Tespiti**: "değil", "yok" gibi kelimelerle anlam değişimi
        - **Güçlendirici Kelimeler**: "çok", "aşırı" gibi intensifier'lar
        - **Kaynak Karşılaştırma**: Twitter vs Reddit sentiment farkı
        
        #### 📊 Pratik Kullanım Örnekleri
        
        **Örnek 1: Transfer Değerlendirmesi**
        - Yeni transfer duyurusu sonrası sentiment
        - Pozitif %70+ = İyi karşılanmış transfer
        - Negatif %50+ = Taraftar tepkili
        
        **Örnek 2: Maç Sonrası Analiz**
        - Galibiyet sonrası sentiment: +0.8 (Çok pozitif)
        - Yenilgi sonrası sentiment: -0.6 (Çok negatif)
        - Beraberlik: ~0.0 (Nötr)
        
        **Örnek 3: Kriz Yönetimi**
        - Ani sentiment düşüşü tespit
        - Neden: Sakatlık haberi, tartışmalı karar
        - Yönetim tepkisi: Açıklama, röportaj
        """)
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "⚽ Takım Analizi",
        "👤 Oyuncu Analizi",
        "🆚 Karşılaştırma",
        "🎲 Canlı Demo"
    ])
    
    # TAB 1: Takım Analizi
    with tab1:
        render_team_sentiment_analysis()
    
    # TAB 2: Oyuncu Analizi
    with tab2:
        render_player_sentiment_analysis()
    
    # TAB 3: Karşılaştırma
    with tab3:
        render_comparison_analysis()
    
    # TAB 4: Canlı Demo
    with tab4:
        render_live_demo()


def render_team_sentiment_analysis():
    """Takım sentiment analizi"""
    
    st.markdown("### ⚽ Takım Sentiment Analizi")
    st.info("💡 Takım adını girin ve son 48 saatin sosyal medya analizini görün")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        team_name = st.text_input(
            "Takım Adı",
            value="Galatasaray",
            placeholder="Örn: Galatasaray, Barcelona, Real Madrid"
        )
    
    with col2:
        post_count = st.number_input(
            "Post Sayısı",
            min_value=10,
            max_value=200,
            value=50,
            step=10
        )
    
    # API durumu göster
    from social_media_api import create_social_aggregator
    
    aggregator = create_social_aggregator()
    api_status = aggregator.get_api_status()
    
    if api_status['any_available']:
        sources = []
        if api_status['twitter']:
            sources.append("🐦 Twitter")
        if api_status['reddit']:
            sources.append("🤖 Reddit")
        st.success(f"✅ API Aktif: {', '.join(sources)}")
    else:
        st.info("ℹ️ API anahtarı yok, demo data kullanılacak (Ayarlar için expander'a bakın)")
    
    if st.button("🔍 Analizi Başlat", type="primary", use_container_width=True):
        with st.spinner(f"{team_name} için sosyal medya verileri analiz ediliyor..."):
            
            # Gerçek API veya mock data
            if api_status['any_available']:
                st.info(f"📡 Gerçek sosyal medya verisi çekiliyor...")
                posts = aggregator.fetch_all(team_name, max_per_source=post_count // 2)
            else:
                st.info(f"🎲 Demo data kullanılıyor...")
                from sentiment_analyzer import SocialMediaMockData
                posts = SocialMediaMockData.generate_team_posts(team_name, post_count)
            
            # Sentiment analizi yap
            analyzer = TurkishSentimentAnalyzer()
            for post in posts:
                post.sentiment = analyzer.analyze(post.text)
            
            # Genel sentiment
            overall_sentiment = analyzer.get_aggregate_sentiment([p.text for p in posts])
            
            # Özet
            st.markdown("---")
            st.markdown(f"## 📊 {team_name} Sentiment Raporu")
            display_sentiment_summary(overall_sentiment, len(posts))
            
            st.markdown("---")
            
            # Göstergeler
            col1, col2 = st.columns(2)
            
            with col1:
                display_sentiment_gauge(overall_sentiment, f"{team_name} Genel Duygu")
            
            with col2:
                display_sentiment_distribution(overall_sentiment)
            
            # Zaman çizgisi
            st.markdown("---")
            display_sentiment_timeline(posts)
            
            # Kelime bulutu
            st.markdown("---")
            display_word_cloud_data(posts)
            
            # Popüler postlar
            st.markdown("---")
            
            post_filter = st.radio(
                "Post Filtresi",
                options=['all', 'positive', 'negative'],
                format_func=lambda x: {
                    'all': '📱 Tümü',
                    'positive': '🟢 Pozitif',
                    'negative': '🔴 Negatif'
                }[x],
                horizontal=True
            )
            
            display_top_posts(posts, count=5, filter_type=post_filter)


def render_player_sentiment_analysis():
    """Oyuncu sentiment analizi"""
    
    st.markdown("### 👤 Oyuncu Sentiment Analizi")
    st.info("💡 Oyuncu adını girin ve performans algısını görün")
    
    player_name = st.text_input(
        "Oyuncu Adı",
        value="Messi",
        placeholder="Örn: Messi, Ronaldo, Haaland"
    )
    
    # API durumu
    from social_media_api import create_social_aggregator
    aggregator = create_social_aggregator()
    api_status = aggregator.get_api_status()
    
    if st.button("🔍 Oyuncu Analizi", type="primary", use_container_width=True):
        with st.spinner(f"{player_name} analiz ediliyor..."):
            
            # Gerçek API veya mock
            if api_status['any_available']:
                st.info(f"📡 Gerçek sosyal medya verisi çekiliyor...")
                posts = aggregator.fetch_all(player_name, max_per_source=15)
            else:
                st.info(f"🎲 Demo data kullanılıyor...")
                from sentiment_analyzer import SocialMediaMockData
                posts = SocialMediaMockData.generate_player_posts(player_name, 30)
            
            # Sentiment
            analyzer = TurkishSentimentAnalyzer()
            for post in posts:
                post.sentiment = analyzer.analyze(post.text)
            
            overall_sentiment = analyzer.get_aggregate_sentiment([p.text for p in posts])
            
            # Sonuçlar
            st.markdown("---")
            display_sentiment_summary(overall_sentiment, len(posts))
            
            col1, col2 = st.columns(2)
            
            with col1:
                display_sentiment_gauge(overall_sentiment, f"{player_name}")
            
            with col2:
                display_sentiment_distribution(overall_sentiment)
            
            st.markdown("---")
            display_top_posts(posts, count=5)


def render_comparison_analysis():
    """Karşılaştırmalı analiz"""
    
    st.markdown("### 🆚 Takım/Oyuncu Karşılaştırma")
    
    col1, col2 = st.columns(2)
    
    with col1:
        entity1 = st.text_input("Takım/Oyuncu 1", value="Galatasaray")
    
    with col2:
        entity2 = st.text_input("Takım/Oyuncu 2", value="Fenerbahçe")
    
    if st.button("🆚 Karşılaştır", type="primary", use_container_width=True):
        from social_media_api import create_social_aggregator
        
        aggregator = create_social_aggregator()
        api_status = aggregator.get_api_status()
        analyzer = TurkishSentimentAnalyzer()
        
        with st.spinner(f"Karşılaştırma yapılıyor..."):
            # Entity 1
            if api_status['any_available']:
                st.info(f"📡 {entity1} verileri çekiliyor...")
                posts1 = aggregator.fetch_all(entity1, max_per_source=25)
            else:
                from sentiment_analyzer import SocialMediaMockData
                posts1 = SocialMediaMockData.generate_team_posts(entity1, 50)
            
            for p in posts1:
                p.sentiment = analyzer.analyze(p.text)
            sentiment1 = analyzer.get_aggregate_sentiment([p.text for p in posts1])
            
            # Entity 2
            if api_status['any_available']:
                st.info(f"📡 {entity2} verileri çekiliyor...")
                posts2 = aggregator.fetch_all(entity2, max_per_source=25)
            else:
                from sentiment_analyzer import SocialMediaMockData
                posts2 = SocialMediaMockData.generate_team_posts(entity2, 50)
        for p in posts2:
            p.sentiment = analyzer.analyze(p.text)
        sentiment2 = analyzer.get_aggregate_sentiment([p.text for p in posts2])
        
        # Karşılaştırma
        st.markdown("---")
        st.markdown("## 📊 Karşılaştırma Sonuçları")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"### {entity1}")
            display_sentiment_gauge(sentiment1, entity1)
            st.markdown(f"""
            - **Compound:** {sentiment1.compound:.2f}
            - **Pozitif:** %{sentiment1.positive*100:.1f}
            - **Negatif:** %{sentiment1.negative*100:.1f}
            """)
        
        with col2:
            st.markdown(f"### {entity2}")
            display_sentiment_gauge(sentiment2, entity2)
            st.markdown(f"""
            - **Compound:** {sentiment2.compound:.2f}
            - **Pozitif:** %{sentiment2.positive*100:.1f}
            - **Negatif:** %{sentiment2.negative*100:.1f}
            """)
        
        # Kazanan
        st.markdown("---")
        if sentiment1.compound > sentiment2.compound:
            diff = sentiment1.compound - sentiment2.compound
            st.success(f"🏆 **{entity1}** daha pozitif! (+{diff:.2f} fark)")
        elif sentiment2.compound > sentiment1.compound:
            diff = sentiment2.compound - sentiment1.compound
            st.success(f"🏆 **{entity2}** daha pozitif! (+{diff:.2f} fark)")
        else:
            st.info("🤝 İki taraf da eşit sentiment'e sahip!")


def render_live_demo():
    """Canlı sentiment demo"""
    
    st.markdown("### 🎲 Canlı Sentiment Demo")
    st.info("💡 Kendi cümlenizi yazın ve anında sentiment analizi görün!")
    
    # Örnek cümleler
    examples = [
        "Galatasaray harika oynuyor! 🔥",
        "Fenerbahçe çok kötü bir performans sergiledi 😢",
        "Beşiktaş bugün maç var",
        "Messi efsane bir gol attı! Muhteşem! ⚽❤️",
        "Ronaldo penaltı kaçırdı. Hayal kırıklığı 💔",
        "Haaland süper bir oyuncu! 💪",
        "Kötü hakem kararları maçı bozdu 😡"
    ]
    
    selected_example = st.selectbox(
        "Örnek Cümle Seç (veya aşağıya kendinizi yazın)",
        options=["Kendin yaz..."] + examples
    )
    
    if selected_example != "Kendin yaz...":
        default_text = selected_example
    else:
        default_text = ""
    
    user_text = st.text_area(
        "Cümlenizi Yazın",
        value=default_text,
        placeholder="Örn: Barcelona harika bir takım! 😊",
        height=100
    )
    
    if user_text and user_text.strip():
        analyzer = TurkishSentimentAnalyzer()
        sentiment = analyzer.analyze(user_text)
        
        st.markdown("---")
        st.markdown("### 📊 Analiz Sonucu")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Sentiment", sentiment.get_sentiment_label())
            st.markdown(f"<h1 style='text-align: center;'>{sentiment.get_emoji()}</h1>", 
                       unsafe_allow_html=True)
        
        with col2:
            gauge_value = (sentiment.compound + 1) * 50
            st.metric("Compound Score", f"{sentiment.compound:.2f}")
            st.metric("Gauge Value", f"{gauge_value:.1f}/100")
        
        with col3:
            st.metric("Pozitif", f"%{sentiment.positive*100:.1f}")
            st.metric("Negatif", f"%{sentiment.negative*100:.1f}")
            st.metric("Nötr", f"%{sentiment.neutral*100:.1f}")
        
        # Görsel
        col1, col2 = st.columns(2)
        
        with col1:
            display_sentiment_gauge(sentiment, "Cümle Sentiment'i")
        
        with col2:
            display_sentiment_distribution(sentiment)


# Test
if __name__ == "__main__":
    st.set_page_config(page_title="Sentiment Analizi", page_icon="📱", layout="wide")
    display_sentiment_page()
