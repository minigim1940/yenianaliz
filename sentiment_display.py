"""
Sentiment Analizi Görselleştirme Modülü
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from typing import List
from sentiment_analyzer import SocialPost, SentimentScore
from datetime import datetime


def display_sentiment_gauge(sentiment: SentimentScore, title: str = "Genel Duygu"):
    """Sentiment gauge göster"""
    
    # Compound score'u 0-100 arası çevir
    gauge_value = (sentiment.compound + 1) * 50
    
    # Renk belirle
    if sentiment.compound >= 0.5:
        color = "green"
    elif sentiment.compound >= 0.1:
        color = "lightgreen"
    elif sentiment.compound <= -0.5:
        color = "red"
    elif sentiment.compound <= -0.1:
        color = "orange"
    else:
        color = "gray"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=gauge_value,
        title={'text': f"{title}<br>{sentiment.get_emoji()}"},
        delta={'reference': 50, 'increasing': {'color': 'green'}, 'decreasing': {'color': 'red'}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1},
            'bar': {'color': color},
            'steps': [
                {'range': [0, 20], 'color': 'darkred'},
                {'range': [20, 40], 'color': 'lightcoral'},
                {'range': [40, 60], 'color': 'lightgray'},
                {'range': [60, 80], 'color': 'lightgreen'},
                {'range': [80, 100], 'color': 'darkgreen'}
            ],
            'threshold': {
                'line': {'color': 'black', 'width': 4},
                'thickness': 0.75,
                'value': 50
            }
        }
    ))
    
    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=60, b=20),
        font=dict(size=14)
    )
    
    st.plotly_chart(fig, use_container_width=True)


def display_sentiment_distribution(sentiment: SentimentScore):
    """Sentiment dağılımı pie chart"""
    
    labels = ['Pozitif', 'Negatif', 'Nötr']
    values = [sentiment.positive, sentiment.negative, sentiment.neutral]
    colors = ['#28a745', '#dc3545', '#6c757d']
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker=dict(colors=colors),
        hole=0.4,
        textinfo='label+percent',
        textfont=dict(size=14)
    )])
    
    fig.update_layout(
        title='Duygu Dağılımı',
        height=350,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
    )
    
    st.plotly_chart(fig, use_container_width=True)


def display_sentiment_timeline(posts: List[SocialPost]):
    """Zaman içinde sentiment değişimi"""
    
    if not posts:
        st.info("Gösterilecek post yok")
        return
    
    # Postları zamana göre sırala
    sorted_posts = sorted(posts, key=lambda p: p.timestamp)
    
    # DataFrame oluştur
    df = pd.DataFrame([{
        'timestamp': p.timestamp,
        'compound': p.sentiment.compound if p.sentiment else 0,
        'text': p.text[:50] + '...' if len(p.text) > 50 else p.text
    } for p in sorted_posts if p.sentiment])
    
    if df.empty:
        st.info("Sentiment verisi yok")
        return
    
    # Grafik
    fig = go.Figure()
    
    # Sentiment çizgisi
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['compound'],
        mode='lines+markers',
        name='Sentiment',
        line=dict(color='blue', width=2),
        marker=dict(size=6),
        hovertemplate='<b>%{x}</b><br>Sentiment: %{y:.2f}<extra></extra>'
    ))
    
    # Pozitif/Negatif bölgeleri
    fig.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="Nötr")
    fig.add_hrect(y0=0, y1=1, fillcolor="green", opacity=0.1, line_width=0)
    fig.add_hrect(y0=-1, y1=0, fillcolor="red", opacity=0.1, line_width=0)
    
    fig.update_layout(
        title='Zaman İçinde Duygu Değişimi',
        xaxis_title='Zaman',
        yaxis_title='Sentiment Skoru',
        yaxis=dict(range=[-1, 1]),
        height=400,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)


def display_top_posts(posts: List[SocialPost], count: int = 10, filter_type: str = 'all'):
    """En popüler postları göster"""
    
    st.markdown(f"### 📱 En Popüler Postlar ({filter_type.capitalize()})")
    
    # Filtrele
    if filter_type == 'positive':
        filtered = [p for p in posts if p.sentiment and p.sentiment.compound > 0.3]
    elif filter_type == 'negative':
        filtered = [p for p in posts if p.sentiment and p.sentiment.compound < -0.3]
    else:
        filtered = posts
    
    # Engagement'a göre sırala
    sorted_posts = sorted(filtered, key=lambda p: p.calculate_engagement_score(), reverse=True)[:count]
    
    if not sorted_posts:
        st.info(f"{filter_type.capitalize()} post bulunamadı")
        return
    
    # Göster
    for i, post in enumerate(sorted_posts, 1):
        sentiment_emoji = post.sentiment.get_emoji() if post.sentiment else "🟡😐"
        sentiment_label = post.sentiment.get_sentiment_label() if post.sentiment else "Nötr"
        
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.markdown(f"""
            **#{i}** {sentiment_emoji} *{sentiment_label}*
            
            {post.text}
            
            <small>👤 {post.author} | 📅 {post.timestamp.strftime('%d.%m.%Y %H:%M')} | 📍 {post.source}</small>
            """, unsafe_allow_html=True)
        
        with col2:
            st.metric("❤️ Beğeni", post.likes)
            st.metric("🔄 Retweet", post.retweets)
        
        st.markdown("---")


def display_word_cloud_data(posts: List[SocialPost], sentiment_filter: str = 'all'):
    """Kelime bulutu verileri (görselleştirme için kelime sıklığı)"""
    
    from collections import Counter
    import re
    
    # Filtrele
    if sentiment_filter == 'positive':
        filtered = [p for p in posts if p.sentiment and p.sentiment.compound > 0.1]
    elif sentiment_filter == 'negative':
        filtered = [p for p in posts if p.sentiment and p.sentiment.compound < -0.1]
    else:
        filtered = posts
    
    # Tüm kelimeleri topla
    all_words = []
    stopwords = {'bir', 'bu', 've', 'de', 'da', 'mi', 'mı', 'için', 'ile', 'ama', 'fakat', 
                'ancak', 'ki', 'ne', 'o', 'şu', 'çok', 'daha', 'en', 'gibi', 'kadar'}
    
    for post in filtered:
        # Temizle
        clean_text = re.sub(r'[^\w\s]', '', post.text.lower())
        words = [w for w in clean_text.split() if len(w) > 2 and w not in stopwords]
        all_words.extend(words)
    
    # Sıklık hesapla
    word_freq = Counter(all_words)
    top_words = word_freq.most_common(20)
    
    if not top_words:
        st.info("Kelime bulutu için yeterli veri yok")
        return
    
    # Bar chart göster
    df = pd.DataFrame(top_words, columns=['Kelime', 'Sıklık'])
    
    fig = px.bar(
        df,
        x='Sıklık',
        y='Kelime',
        orientation='h',
        title=f'En Çok Kullanılan Kelimeler ({sentiment_filter.capitalize()})',
        color='Sıklık',
        color_continuous_scale='Blues'
    )
    
    fig.update_layout(
        height=500,
        yaxis={'categoryorder': 'total ascending'}
    )
    
    st.plotly_chart(fig, use_container_width=True)


def display_source_comparison(posts: List[SocialPost]):
    """Kaynak bazlı sentiment karşılaştırma"""
    
    # Kaynaklara göre grupla
    source_data = {}
    
    for post in posts:
        if not post.sentiment:
            continue
        
        if post.source not in source_data:
            source_data[post.source] = []
        
        source_data[post.source].append(post.sentiment.compound)
    
    if not source_data:
        st.info("Kaynak karşılaştırma için veri yok")
        return
    
    # DataFrame oluştur
    data = []
    for source, scores in source_data.items():
        data.append({
            'Kaynak': source.capitalize(),
            'Ortalama Sentiment': sum(scores) / len(scores),
            'Post Sayısı': len(scores)
        })
    
    df = pd.DataFrame(data)
    
    # Grafik
    fig = px.bar(
        df,
        x='Kaynak',
        y='Ortalama Sentiment',
        color='Ortalama Sentiment',
        color_continuous_scale=['red', 'yellow', 'green'],
        title='Kaynak Bazlı Ortalama Sentiment',
        text='Post Sayısı',
        range_color=[-1, 1]
    )
    
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    
    fig.update_layout(height=400)
    
    st.plotly_chart(fig, use_container_width=True)


def display_sentiment_summary(sentiment: SentimentScore, total_posts: int):
    """Özet metrikler"""
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Toplam Post",
            total_posts,
            help="Analiz edilen toplam post sayısı"
        )
    
    with col2:
        sentiment_label = sentiment.get_sentiment_label()
        emoji = sentiment.get_emoji()
        st.metric(
            "Genel Duygu",
            f"{sentiment_label} {emoji}",
            f"{sentiment.compound:.2f}",
            delta_color="normal" if sentiment.compound > 0 else "inverse"
        )
    
    with col3:
        st.metric(
            "Pozitif Oran",
            f"%{sentiment.positive*100:.1f}",
            help="Pozitif duygu yüzdesi"
        )
    
    with col4:
        st.metric(
            "Negatif Oran",
            f"%{sentiment.negative*100:.1f}",
            help="Negatif duygu yüzdesi"
        )


# Test
if __name__ == "__main__":
    print("✅ Sentiment display modülü hazır!")
