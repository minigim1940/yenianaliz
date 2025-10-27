# -*- coding: utf-8 -*-
"""
Enhanced Analysis Display Module
=================================
xG ve Momentum analizlerini görselleştirme
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Any
import pandas as pd
from xg_calculator import xGCalculator, LivexGTracker
from momentum_tracker import MomentumTracker, MomentumVisualizer


def display_xg_analysis(fixture_data: Dict, api_key: str = None):
    """
    xG Analizi gösterimi
    
    Args:
        fixture_data: Maç verileri
        api_key: API anahtarı (canlı veri için)
    """
    st.subheader("⚽ Expected Goals (xG) Analizi")
    
    # xG Calculator
    calc = xGCalculator()
    
    # Tab'lar
    tab1, tab2, tab3 = st.tabs(["📊 xG Özeti", "🎯 Şut Analizi", "📈 xG Timeline"])
    
    with tab1:
        display_xg_summary(fixture_data, calc)
    
    with tab2:
        display_shot_analysis(fixture_data, calc)
    
    with tab3:
        display_xg_timeline(fixture_data)


def display_xg_summary(fixture_data: Dict, calc: xGCalculator):
    """xG özet gösterimi"""
    
    # Takım isimleri
    home_team = fixture_data.get('home_team', 'Ev Sahibi')
    away_team = fixture_data.get('away_team', 'Deplasman')
    
    # Tahmin edilen xG hesapla (istatistiklerden)
    home_stats = fixture_data.get('home_stats', {})
    away_stats = fixture_data.get('away_stats', {})
    
    home_xg_data = calc.calculate_team_xg(home_stats, away_stats)
    away_xg_data = calc.calculate_team_xg(away_stats, home_stats)
    
    home_xg = home_xg_data['estimated_xg']
    away_xg = away_xg_data['estimated_xg']
    
    # Gerçek skorlar (varsa)
    home_goals = fixture_data.get('home_goals', 0)
    away_goals = fixture_data.get('away_goals', 0)
    
    # Ana metrikler
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label=f"🏠 {home_team} xG",
            value=f"{home_xg:.2f}",
            delta=f"{home_goals - home_xg:.2f}" if home_goals > 0 else None
        )
    
    with col2:
        st.metric(
            label="⚖️ xG Farkı",
            value=f"{abs(home_xg - away_xg):.2f}",
            delta="Ev Sahibi" if home_xg > away_xg else "Deplasman"
        )
    
    with col3:
        st.metric(
            label=f"✈️ {away_team} xG",
            value=f"{away_xg:.2f}",
            delta=f"{away_goals - away_xg:.2f}" if away_goals > 0 else None
        )
    
    # xG Bar Chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name=home_team,
        x=['Expected Goals'],
        y=[home_xg],
        marker_color='#3498db',
        text=[f"{home_xg:.2f}"],
        textposition='auto',
    ))
    
    fig.add_trace(go.Bar(
        name=away_team,
        x=['Expected Goals'],
        y=[away_xg],
        marker_color='#e74c3c',
        text=[f"{away_xg:.2f}"],
        textposition='auto',
    ))
    
    if home_goals > 0 or away_goals > 0:
        fig.add_trace(go.Bar(
            name='Gerçek Goller',
            x=['Actual Goals'],
            y=[home_goals],
            marker_color='#2ecc71',
            text=[f"{home_goals}"],
            textposition='auto',
        ))
        
        fig.add_trace(go.Bar(
            x=['Actual Goals'],
            y=[away_goals],
            marker_color='#f39c12',
            text=[f"{away_goals}"],
            textposition='auto',
            showlegend=False
        ))
    
    fig.update_layout(
        title="Expected Goals vs Actual Goals",
        barmode='group',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Performans analizi
    if home_goals > 0 or away_goals > 0:
        st.markdown("---")
        st.markdown("### 🎯 Bitiricilik Performansı")
        
        col1, col2 = st.columns(2)
        
        with col1:
            home_comp = calc.compare_xg_vs_goals(home_xg, home_goals)
            st.markdown(f"**{home_team}**")
            st.markdown(f"- Performans: **{home_comp['performance']}**")
            st.markdown(f"- Verimlilik: **{home_comp['efficiency']}%**")
            st.markdown(f"- Değerlendirme: {home_comp['luck']}")
        
        with col2:
            away_comp = calc.compare_xg_vs_goals(away_xg, away_goals)
            st.markdown(f"**{away_team}**")
            st.markdown(f"- Performans: **{away_comp['performance']}**")
            st.markdown(f"- Verimlilik: **{away_comp['efficiency']}%**")
            st.markdown(f"- Değerlendirme: {away_comp['luck']}")


def display_shot_analysis(fixture_data: Dict, calc: xGCalculator):
    """Şut bazlı analiz"""
    st.markdown("### 🎯 Şut Kalitesi Analizi")
    
    # Örnek şutlar (gerçek API'den gelecek)
    shots_data = fixture_data.get('shots', [])
    
    if not shots_data:
        st.info("Şut verileri henüz mevcut değil")
        
        # Demo şutlar göster
        st.markdown("#### 📍 Örnek xG Hesaplamaları")
        
        demo_shots = [
            {
                'name': 'Ceza Sahası İçi (Merkez)',
                'params': {'distance': 10, 'angle': 10, 'situation': 'open_play', 'defender_count': 1}
            },
            {
                'name': '1v1 Pozisyon',
                'params': {'distance': 8, 'angle': 5, 'situation': 'one_on_one', 'defender_count': 0, 'goalkeeper_position': 'bad'}
            },
            {
                'name': 'Penaltı',
                'params': {'distance': 11, 'angle': 0, 'situation': 'penalty', 'defender_count': 0}
            },
            {
                'name': 'Uzak Mesafe',
                'params': {'distance': 28, 'angle': 20, 'situation': 'open_play', 'defender_count': 3}
            },
            {
                'name': 'Korner Sonrası Kafa',
                'params': {'distance': 9, 'angle': 25, 'situation': 'corner', 'is_header': True, 'defender_count': 2}
            },
        ]
        
        for shot in demo_shots:
            result = calc.calculate_shot_xg(**shot['params'])
            
            with st.expander(f"{shot['name']} - xG: {result['xg_value']:.3f}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Faktörler:**")
                    st.write(result['factors'])
                
                with col2:
                    st.markdown("**Çarpanlar:**")
                    st.write(result['multipliers'])
    else:
        # Gerçek şut analizi
        for shot in shots_data:
            display_shot_card(shot, calc)


def display_shot_card(shot: Dict, calc: xGCalculator):
    """Tek şut kartı"""
    xg_result = calc.calculate_shot_xg(**shot['params'])
    
    with st.container():
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown(f"**{shot.get('player', 'Oyuncu')}** - {shot.get('minute', 0)}'")
            st.progress(xg_result['xg_value'])
        
        with col2:
            st.metric("xG", f"{xg_result['xg_value']:.3f}")
        
        with col3:
            is_goal = shot.get('is_goal', False)
            st.markdown("⚽ **GOL**" if is_goal else "❌ Kaçtı")


def display_xg_timeline(fixture_data: Dict):
    """xG zaman çizelgesi"""
    st.markdown("### 📈 xG Timeline")
    
    # Örnek timeline verisi
    timeline_data = fixture_data.get('xg_timeline', [])
    
    if not timeline_data:
        st.info("Timeline verisi henüz mevcut değil")
        
        # Demo timeline
        demo_timeline = [
            {'minute': 5, 'home_xg': 0.15, 'away_xg': 0},
            {'minute': 12, 'home_xg': 0.35, 'away_xg': 0.08},
            {'minute': 18, 'home_xg': 0.35, 'away_xg': 0.28},
            {'minute': 25, 'home_xg': 0.82, 'away_xg': 0.28},
            {'minute': 35, 'home_xg': 0.82, 'away_xg': 0.55},
            {'minute': 42, 'home_xg': 1.15, 'away_xg': 0.55},
            {'minute': 50, 'home_xg': 1.15, 'away_xg': 0.92},
            {'minute': 67, 'home_xg': 1.58, 'away_xg': 0.92},
            {'minute': 78, 'home_xg': 1.58, 'away_xg': 1.23},
            {'minute': 90, 'home_xg': 1.85, 'away_xg': 1.45},
        ]
        timeline_data = demo_timeline
    
    # Timeline grafiği
    fig = go.Figure()
    
    minutes = [t['minute'] for t in timeline_data]
    home_xg = [t['home_xg'] for t in timeline_data]
    away_xg = [t['away_xg'] for t in timeline_data]
    
    fig.add_trace(go.Scatter(
        x=minutes,
        y=home_xg,
        name='Ev Sahibi xG',
        mode='lines+markers',
        line=dict(color='#3498db', width=3),
        fill='tozeroy'
    ))
    
    fig.add_trace(go.Scatter(
        x=minutes,
        y=away_xg,
        name='Deplasman xG',
        mode='lines+markers',
        line=dict(color='#e74c3c', width=3),
        fill='tozeroy'
    ))
    
    fig.update_layout(
        title="Kümülatif xG Gelişimi",
        xaxis_title="Dakika",
        yaxis_title="Kümülatif xG",
        hovermode='x unified',
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)


def display_momentum_analysis(fixture_data: Dict):
    """
    Momentum analizi gösterimi
    
    Args:
        fixture_data: Maç verileri
    """
    st.subheader("⚡ Canlı Momentum Analizi")
    
    # Momentum Tracker
    tracker = MomentumTracker(window_size=10)
    
    # Maç olaylarını yükle (gerçek API'den gelecek)
    events = fixture_data.get('events', [])
    
    if events:
        for event in events:
            tracker.add_event(
                minute=event['minute'],
                team=event['team'],
                event_type=event['type'],
                details=event.get('details')
            )
    else:
        # Demo events
        demo_events = [
            {'minute': 5, 'team': 'home', 'type': 'shot_on_target'},
            {'minute': 8, 'team': 'home', 'type': 'corner'},
            {'minute': 12, 'team': 'away', 'type': 'shot_on_target'},
            {'minute': 15, 'team': 'home', 'type': 'goal'},
            {'minute': 20, 'team': 'away', 'type': 'big_chance_created'},
            {'minute': 23, 'team': 'away', 'type': 'shot_on_target'},
            {'minute': 28, 'team': 'away', 'type': 'goal'},
            {'minute': 35, 'team': 'home', 'type': 'corner'},
            {'minute': 40, 'team': 'home', 'type': 'shot_on_target'},
            {'minute': 45, 'team': 'away', 'type': 'yellow_card'},
        ]
        
        for event in demo_events:
            tracker.add_event(**event)
    
    # Tab'lar
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Mevcut Durum",
        "📈 Momentum Timeline",
        "🔥 Kritik Anlar",
        "📋 Detaylı Rapor"
    ])
    
    with tab1:
        display_current_momentum(tracker)
    
    with tab2:
        display_momentum_timeline(tracker)
    
    with tab3:
        display_critical_moments(tracker)
    
    with tab4:
        display_momentum_report(tracker)


def display_current_momentum(tracker: MomentumTracker):
    """Mevcut momentum durumu"""
    current = tracker.get_current_momentum()
    pressure = tracker.get_pressure_index()
    next_goal = tracker.predict_next_goal()
    
    # Momentum bar
    viz = MomentumVisualizer()
    st.markdown(viz.get_momentum_bar_html(current['momentum']), unsafe_allow_html=True)
    
    # Metrikler
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Baskın Takım",
            current['dominant_team'].upper(),
            viz.get_strength_emoji(current['strength'])
        )
    
    with col2:
        st.metric(
            "Trend",
            current['trend'].replace('_', ' ').title(),
            viz.get_trend_emoji(current['trend'])
        )
    
    with col3:
        st.metric(
            "Ev Sahibi Baskı",
            f"{pressure['home']}%"
        )
    
    with col4:
        st.metric(
            "Deplasman Baskı",
            f"{pressure['away']}%"
        )
    
    # Sonraki gol tahmini
    st.markdown("---")
    st.markdown("### 🎯 Sonraki Gol Tahmini")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            "Ev Sahibi Olasılığı",
            f"{next_goal['home_probability']}%"
        )
        st.progress(next_goal['home_probability'] / 100)
    
    with col2:
        st.metric(
            "Deplasman Olasılığı",
            f"{next_goal['away_probability']}%"
        )
        st.progress(next_goal['away_probability'] / 100)
    
    st.info(f"**En Olası:** {next_goal['likely_scorer'].upper()} - Güven: {next_goal['confidence'].upper()}")


def display_momentum_timeline(tracker: MomentumTracker):
    """Momentum timeline grafiği"""
    timeline = tracker.get_momentum_timeline()
    
    if not timeline:
        st.info("Henüz momentum verisi yok")
        return
    
    # DataFrame oluştur
    df = pd.DataFrame(timeline)
    
    # Grafik
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['minute'],
        y=df['momentum'],
        mode='lines+markers',
        name='Momentum',
        line=dict(color='#3498db', width=3),
        fill='tozeroy',
        fillcolor='rgba(52, 152, 219, 0.3)'
    ))
    
    # 0 çizgisi
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    
    # Momentum bölgeleri
    fig.add_hrect(y0=50, y1=100, fillcolor="green", opacity=0.1, annotation_text="Ev Güçlü")
    fig.add_hrect(y0=20, y1=50, fillcolor="lightgreen", opacity=0.1, annotation_text="Ev Üstün")
    fig.add_hrect(y0=-20, y1=20, fillcolor="yellow", opacity=0.1, annotation_text="Dengeli")
    fig.add_hrect(y0=-50, y1=-20, fillcolor="orange", opacity=0.1, annotation_text="Deplasman Üstün")
    fig.add_hrect(y0=-100, y1=-50, fillcolor="red", opacity=0.1, annotation_text="Deplasman Güçlü")
    
    fig.update_layout(
        title="Momentum Gelişimi",
        xaxis_title="Dakika",
        yaxis_title="Momentum Skoru",
        hovermode='x unified',
        height=500,
        yaxis=dict(range=[-100, 100])
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Momentum değişimleri
    shifts = tracker.detect_momentum_shifts(threshold=30)
    
    if shifts:
        st.markdown("### 🔄 Önemli Momentum Değişimleri")
        
        for shift in shifts:
            with st.expander(f"⏱️ {shift['minute']}' - {shift['direction'].upper()} Takımına Geçiş"):
                st.markdown(f"**Değişim:** {shift['from']:.1f} → {shift['to']:.1f} ({shift['change']:+.1f})")
                if shift['trigger_events']:
                    st.markdown("**Tetikleyen Olaylar:**")
                    for event in shift['trigger_events']:
                        st.markdown(f"- {event['minute']}': {event['type']} ({event['team']})")


def display_critical_moments(tracker: MomentumTracker):
    """Kritik anlar listesi"""
    critical = tracker.get_critical_moments()
    
    if not critical:
        st.info("Henüz kritik an tespit edilmedi")
        return
    
    st.markdown("### 🔥 Maçın Kritik Anları")
    
    # Önem derecesine göre renk
    importance_colors = {
        'very_high': '🔴',
        'high': '🟠',
        'medium': '🟡',
        'low': '🟢'
    }
    
    for moment in critical:
        emoji = importance_colors.get(moment['importance'], '⚪')
        
        st.markdown(f"""
        <div style="padding: 10px; margin: 5px 0; border-left: 4px solid #3498db; background: #f8f9fa;">
            <strong>{emoji} {moment['minute']}'</strong> - {moment['description']}
            <br><small>Önem: {moment['importance']}</small>
        </div>
        """, unsafe_allow_html=True)


def display_momentum_report(tracker: MomentumTracker):
    """Detaylı momentum raporu"""
    report = tracker.get_match_report()
    
    st.markdown("### 📋 Kapsamlı Momentum Raporu")
    
    # Maç fazı
    phase_names = {
        'early': '🌅 Erken Dakikalar',
        'settling': '⚖️ Dengeye Gelme',
        'first_half_end': '🕐 İlk Yarı Sonu',
        'second_half_start': '🔄 İkinci Yarı Başı',
        'mid_second_half': '⚡ İkinci Yarı Ortası',
        'crucial': '🔥 Kritik Dakikalar',
        'final_push': '🎯 Son Baskı'
    }
    
    st.info(f"**Maç Fazı:** {phase_names.get(report['match_phase'], 'Bilinmiyor')}")
    
    # İstatistikler
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 Genel İstatistikler")
        st.write(f"- Toplam Olay: **{report['total_events']}**")
        st.write(f"- Momentum Değişimi: **{report['momentum_shifts']}**")
        st.write(f"- Kritik An: **{len(report['critical_moments'])}**")
    
    with col2:
        st.markdown("#### 🎲 Olay Dağılımı")
        if report['event_breakdown']:
            event_df = pd.DataFrame(
                list(report['event_breakdown'].items()),
                columns=['Olay', 'Sayı']
            ).sort_values('Sayı', ascending=False).head(5)
            st.dataframe(event_df, hide_index=True)


# Ana entegrasyon fonksiyonu
def display_advanced_analysis_tab(fixture_data: Dict):
    """
    Gelişmiş analiz sekmesi
    
    Args:
        fixture_data: Maç verileri
    """
    st.title("🚀 Gelişmiş Analiz Sistemi")
    
    analysis_type = st.selectbox(
        "Analiz Türü Seçin:",
        ["⚽ xG (Expected Goals) Analizi", "⚡ Momentum Analizi", "📊 Kombine Analiz"]
    )
    
    if analysis_type == "⚽ xG (Expected Goals) Analizi":
        display_xg_analysis(fixture_data)
    elif analysis_type == "⚡ Momentum Analizi":
        display_momentum_analysis(fixture_data)
    else:
        # Kombine
        col1, col2 = st.columns(2)
        with col1:
            display_xg_analysis(fixture_data)
        with col2:
            display_momentum_analysis(fixture_data)


if __name__ == "__main__":
    # Demo
    demo_fixture = {
        'home_team': 'Galatasaray',
        'away_team': 'Fenerbahçe',
        'home_goals': 2,
        'away_goals': 1,
        'home_stats': {
            'shots_total': 15,
            'shots_on_target': 8,
            'shots_inside_box': 10,
            'shots_outside_box': 5,
            'is_home': True
        },
        'away_stats': {
            'shots_total': 12,
            'shots_on_target': 5,
            'shots_inside_box': 7,
            'shots_outside_box': 5,
            'defense_rating': 65
        }
    }
    
    display_advanced_analysis_tab(demo_fixture)
