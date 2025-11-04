# -*- coding: utf-8 -*-
"""
Advanced Metrics Display Module
================================
Yeni advanced metrics'leri Streamlit'te göster
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, Optional, List
import pandas as pd

try:
    from advanced_metrics_manager import AdvancedMetricsManager
    ADVANCED_METRICS_AVAILABLE = True
except ImportError:
    ADVANCED_METRICS_AVAILABLE = False
    AdvancedMetricsManager = None


def display_advanced_metrics_dashboard(
    home_team_analysis: Dict,
    away_team_analysis: Dict,
    match_prediction: Dict
):
    """
    Ana advanced metrics dashboard
    
    Args:
        home_team_analysis: Ev sahibi takım advanced analizi
        away_team_analysis: Deplasman takımı advanced analizi
        match_prediction: Maç tahmini
    """
    
    st.markdown("## 🔬 Gelişmiş Metrik Analizi")
    st.markdown("*Dünya standartlarında modern futbol analitiği*")
    
    # Overall Ratings Comparison
    st.markdown("---")
    _display_overall_ratings(home_team_analysis, away_team_analysis)
    
    # Detailed Metrics Tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Genel Bakış",
        "⚡ Form & Momentum",
        "🎯 xG Analysis",
        "🔥 Pressing & PPDA",
        "📈 Progressive Play",
        "🎨 Chance Creation"
    ])
    
    with tab1:
        _display_overview_tab(home_team_analysis, away_team_analysis, match_prediction)
    
    with tab2:
        _display_form_momentum_tab(home_team_analysis, away_team_analysis)
    
    with tab3:
        _display_xg_tab(home_team_analysis, away_team_analysis)
    
    with tab4:
        _display_pressing_tab(home_team_analysis, away_team_analysis)
    
    with tab5:
        _display_progressive_tab(home_team_analysis, away_team_analysis)
    
    with tab6:
        _display_chance_creation_tab(home_team_analysis, away_team_analysis)


def _display_overall_ratings(home_analysis: Dict, away_analysis: Dict):
    """Overall rating karşılaştırması"""
    
    st.markdown("### 🏆 Genel Değerlendirme")
    
    col1, col2, col3 = st.columns([2, 1, 2])
    
    home_rating = home_analysis.get('overall_rating', 50)
    away_rating = away_analysis.get('overall_rating', 50)
    
    with col1:
        st.markdown("#### 🏠 Ev Sahibi")
        _display_rating_gauge(home_rating, "home")
        
        # Strengths
        st.markdown("**💪 Güçlü Yönler:**")
        for strength in home_analysis.get('strengths', [])[:3]:
            st.markdown(f"• {strength}")
    
    with col2:
        # VS indicator
        st.markdown("<br><br>", unsafe_allow_html=True)
        rating_diff = home_rating - away_rating
        if abs(rating_diff) < 5:
            st.markdown("### 🟡 DENGELI")
        elif rating_diff > 5:
            st.markdown("### 🟢 EV ÖNE")
        else:
            st.markdown("### 🔵 DEP ÖNE")
        
        st.metric("Fark", f"{abs(rating_diff):.1f} puan")
    
    with col3:
        st.markdown("#### ✈️ Deplasman")
        _display_rating_gauge(away_rating, "away")
        
        # Strengths
        st.markdown("**💪 Güçlü Yönler:**")
        for strength in away_analysis.get('strengths', [])[:3]:
            st.markdown(f"• {strength}")


def _display_rating_gauge(rating: float, team_type: str):
    """Rating gauge chart"""
    
    # Color based on rating
    if rating >= 75:
        color = "green"
    elif rating >= 60:
        color = "lightgreen"
    elif rating >= 50:
        color = "orange"
    else:
        color = "red"
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = rating,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Rating"},
        delta = {'reference': 50},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': color},
            'steps': [
                {'range': [0, 40], 'color': "lightgray"},
                {'range': [40, 60], 'color': "gray"},
                {'range': [60, 100], 'color': "lightgray"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 70
            }
        }
    ))
    
    fig.update_layout(height=200, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig, use_container_width=True)


def _display_overview_tab(home: Dict, away: Dict, prediction: Dict):
    """Genel bakış tab"""
    
    st.markdown("### 📊 Maç Tahmini")
    
    # Prediction probabilities
    pred = prediction['match_prediction']
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("🏠 Ev Sahibi Kazanır", f"%{pred['home_win']:.1f}")
    with col2:
        st.metric("🤝 Beraberlik", f"%{pred['draw']:.1f}")
    with col3:
        st.metric("✈️ Deplasman Kazanır", f"%{pred['away_win']:.1f}")
    
    # Probability bar chart
    fig = go.Figure(data=[
        go.Bar(
            x=['Ev Sahibi', 'Beraberlik', 'Deplasman'],
            y=[pred['home_win'], pred['draw'], pred['away_win']],
            marker_color=['#1f77b4', '#808080', '#ff7f0e'],
            text=[f"%{pred['home_win']:.1f}", f"%{pred['draw']:.1f}", f"%{pred['away_win']:.1f}"],
            textposition='auto',
        )
    ])
    
    fig.update_layout(
        title="Maç Sonucu Olasılıkları",
        yaxis_title="Olasılık (%)",
        showlegend=False,
        height=300
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Most likely outcome
    most_likely = pred['most_likely']
    outcome_text = {
        'home': '🏠 Ev Sahibi Kazanır',
        'draw': '🤝 Beraberlik',
        'away': '✈️ Deplasman Kazanır'
    }
    
    st.success(f"**En Olası Sonuç:** {outcome_text.get(most_likely, 'Belirsiz')}")
    
    # SWOT Comparison
    st.markdown("---")
    st.markdown("### 📋 SWOT Analizi")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🏠 Ev Sahibi")
        
        st.markdown("**💪 Güçlü Yönler:**")
        for s in home.get('strengths', []):
            st.markdown(f"• {s}")
        
        st.markdown("**⚠️ Zayıf Yönler:**")
        for w in home.get('weaknesses', []):
            st.markdown(f"• {w}")
    
    with col2:
        st.markdown("#### ✈️ Deplasman")
        
        st.markdown("**💪 Güçlü Yönler:**")
        for s in away.get('strengths', []):
            st.markdown(f"• {s}")
        
        st.markdown("**⚠️ Zayıf Yönler:**")
        for w in away.get('weaknesses', []):
            st.markdown(f"• {w}")


def _display_form_momentum_tab(home: Dict, away: Dict):
    """Form ve momentum tab"""
    
    st.markdown("### ⚡ Form Analizi")
    
    col1, col2 = st.columns(2)
    
    # Home team form
    with col1:
        st.markdown("#### 🏠 Ev Sahibi")
        
        if home.get('form_analysis'):
            form = home['form_analysis']
            
            st.metric("Form Skoru", f"{form.get('form_score', 0):.1f}/100")
            st.metric("Form String", form.get('form_string', 'N/A'))
            
            # Form breakdown
            if form.get('breakdown'):
                breakdown = form['breakdown']
                
                fig = go.Figure(data=[
                    go.Bar(
                        x=['Sonuç', 'Rakip Gücü', 'Gol Farkı', 'Trend'],
                        y=[
                            breakdown.get('result_score', 0),
                            breakdown.get('opponent_score', 0),
                            breakdown.get('goal_diff_score', 0),
                            breakdown.get('trend_score', 0)
                        ],
                        marker_color='lightblue'
                    )
                ])
                
                fig.update_layout(
                    title="Form Faktörleri",
                    yaxis_title="Skor",
                    height=250
                )
                
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Form analizi mevcut değil")
        
        # Home advantage
        if home.get('home_advantage'):
            ha = home['home_advantage']
            st.markdown("---")
            st.markdown("**🏟️ Ev Sahibi Avantajı**")
            st.metric("Çarpan", f"{ha.get('home_advantage', 1.0):.2f}x")
            
            if ha.get('breakdown'):
                breakdown = ha['breakdown']
                st.caption(f"Lig Bazı: {breakdown.get('league_base', 1.0):.2f}")
                st.caption(f"Stadyum: {breakdown.get('stadium_factor', 1.0):.2f}")
    
    # Away team form
    with col2:
        st.markdown("#### ✈️ Deplasman")
        
        if away.get('form_analysis'):
            form = away['form_analysis']
            
            st.metric("Form Skoru", f"{form.get('form_score', 0):.1f}/100")
            st.metric("Form String", form.get('form_string', 'N/A'))
            
            # Form breakdown
            if form.get('breakdown'):
                breakdown = form['breakdown']
                
                fig = go.Figure(data=[
                    go.Bar(
                        x=['Sonuç', 'Rakip Gücü', 'Gol Farkı', 'Trend'],
                        y=[
                            breakdown.get('result_score', 0),
                            breakdown.get('opponent_score', 0),
                            breakdown.get('goal_diff_score', 0),
                            breakdown.get('trend_score', 0)
                        ],
                        marker_color='lightcoral'
                    )
                ])
                
                fig.update_layout(
                    title="Form Faktörleri",
                    yaxis_title="Skor",
                    height=250
                )
                
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Form analizi mevcut değil")


def _display_xg_tab(home: Dict, away: Dict):
    """xG analizi tab"""
    
    st.markdown("### 🎯 Expected Goals (xG) Analizi")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🏠 Ev Sahibi")
        if home.get('expected_goals'):
            xg_data = home['expected_goals']
            
            st.metric("xG (Beklenen Gol)", f"{xg_data.get('team_xG', 0):.2f}")
            st.metric("xGA (Beklenen Yenilen)", f"{xg_data.get('opponent_xG', 0):.2f}")
            
            # xG prediction
            if xg_data.get('prediction'):
                pred = xg_data['prediction']
                st.markdown("**Olasılıklar:**")
                st.caption(f"Over 2.5: %{pred.get('over_2_5', 0):.1f}")
                st.caption(f"BTTS: %{pred.get('btts', 0):.1f}")
        else:
            st.info("xG verisi mevcut değil")
    
    with col2:
        st.markdown("#### ✈️ Deplasman")
        if away.get('expected_goals'):
            xg_data = away['expected_goals']
            
            st.metric("xG (Beklenen Gol)", f"{xg_data.get('team_xG', 0):.2f}")
            st.metric("xGA (Beklenen Yenilen)", f"{xg_data.get('opponent_xG', 0):.2f}")
            
            # xG prediction
            if xg_data.get('prediction'):
                pred = xg_data['prediction']
                st.markdown("**Olasılıklar:**")
                st.caption(f"Over 2.5: %{pred.get('over_2_5', 0):.1f}")
                st.caption(f"BTTS: %{pred.get('btts', 0):.1f}")
        else:
            st.info("xG verisi mevcut değil")
    
    # xG Comparison Chart
    if home.get('expected_goals') and away.get('expected_goals'):
        st.markdown("---")
        st.markdown("#### 📊 xG Karşılaştırma")
        
        fig = go.Figure(data=[
            go.Bar(
                name='Ev Sahibi',
                x=['xG', 'xGA'],
                y=[home['expected_goals'].get('team_xG', 0), home['expected_goals'].get('opponent_xG', 0)],
                marker_color='lightblue'
            ),
            go.Bar(
                name='Deplasman',
                x=['xG', 'xGA'],
                y=[away['expected_goals'].get('team_xG', 0), away['expected_goals'].get('opponent_xG', 0)],
                marker_color='lightcoral'
            )
        ])
        
        fig.update_layout(
            barmode='group',
            height=300,
            yaxis_title='Beklenen Gol'
        )
        
        st.plotly_chart(fig, use_container_width=True)


def _display_pressing_tab(home: Dict, away: Dict):
    """Pressing ve PPDA tab"""
    
    st.markdown("### 🔥 Pressing & PPDA Analizi")
    st.caption("PPDA (Passes Allowed Per Defensive Action) - Düşük değer = Yoğun pressing")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🏠 Ev Sahibi")
        if home.get('pressing'):
            press = home['pressing']
            
            ppda = press.get('ppda', 0)
            st.metric("PPDA", f"{ppda:.2f}")
            
            # PPDA category
            if ppda < 8.0:
                st.success("🔥 Çok Yoğun Pressing (Elite)")
            elif ppda < 10.0:
                st.info("💪 Yoğun Pressing")
            elif ppda < 13.0:
                st.warning("⚖️ Orta Seviye")
            else:
                st.error("😴 Düşük Pressing")
            
            st.metric("Pressing Skoru", f"{press.get('pressing_score', 0):.1f}/100")
        else:
            st.info("Pressing verisi mevcut değil")
    
    with col2:
        st.markdown("#### ✈️ Deplasman")
        if away.get('pressing'):
            press = away['pressing']
            
            ppda = press.get('ppda', 0)
            st.metric("PPDA", f"{ppda:.2f}")
            
            # PPDA category
            if ppda < 8.0:
                st.success("🔥 Çok Yoğun Pressing (Elite)")
            elif ppda < 10.0:
                st.info("💪 Yoğun Pressing")
            elif ppda < 13.0:
                st.warning("⚖️ Orta Seviye")
            else:
                st.error("😴 Düşük Pressing")
            
            st.metric("Pressing Skoru", f"{press.get('pressing_score', 0):.1f}/100")
        else:
            st.info("Pressing verisi mevcut değil")
    
    # PPDA Comparison
    if home.get('pressing') and away.get('pressing'):
        st.markdown("---")
        st.markdown("#### 📊 PPDA Karşılaştırma")
        
        home_ppda = home['pressing'].get('ppda', 12)
        away_ppda = away['pressing'].get('ppda', 12)
        
        fig = go.Figure(data=[
            go.Bar(
                x=['Ev Sahibi', 'Deplasman'],
                y=[home_ppda, away_ppda],
                marker_color=['lightblue', 'lightcoral'],
                text=[f"{home_ppda:.2f}", f"{away_ppda:.2f}"],
                textposition='auto',
            )
        ])
        
        # Add benchmark lines
        fig.add_hline(y=8.0, line_dash="dash", line_color="green", annotation_text="Elite (8.0)")
        fig.add_hline(y=13.0, line_dash="dash", line_color="red", annotation_text="Average (13.0)")
        
        fig.update_layout(
            yaxis_title="PPDA (düşük = iyi)",
            height=300,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)


def _display_progressive_tab(home: Dict, away: Dict):
    """Progressive play tab"""
    
    st.markdown("### 📈 İleri Oyun Kalitesi")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🏠 Ev Sahibi")
        if home.get('progressive'):
            prog = home['progressive']
            
            if prog.get('progressive_passing'):
                pp = prog['progressive_passing']
                st.metric("Progressive Quality", f"{pp.get('quality_score', 0):.1f}/100")
                st.metric("Progressive Passes", f"{pp.get('progressive_passes', 0):.1f}")
            
            if prog.get('field_tilt'):
                ft = prog['field_tilt']
                tilt_score = ft.get('score', 0)
                st.metric("Field Tilt", f"{tilt_score:.1f}")
                
                if tilt_score > 20:
                    st.success("⚡ Rakip yarı sahada dominant")
                elif tilt_score < -20:
                    st.error("🛡️ Kendi sahasında oyun")
                else:
                    st.info("⚖️ Dengeli")
        else:
            st.info("Progressive play verisi mevcut değil")
    
    with col2:
        st.markdown("#### ✈️ Deplasman")
        if away.get('progressive'):
            prog = away['progressive']
            
            if prog.get('progressive_passing'):
                pp = prog['progressive_passing']
                st.metric("Progressive Quality", f"{pp.get('quality_score', 0):.1f}/100")
                st.metric("Progressive Passes", f"{pp.get('progressive_passes', 0):.1f}")
            
            if prog.get('field_tilt'):
                ft = prog['field_tilt']
                tilt_score = ft.get('score', 0)
                st.metric("Field Tilt", f"{tilt_score:.1f}")
                
                if tilt_score > 20:
                    st.success("⚡ Rakip yarı sahada dominant")
                elif tilt_score < -20:
                    st.error("🛡️ Kendi sahasında oyun")
                else:
                    st.info("⚖️ Dengeli")
        else:
            st.info("Progressive play verisi mevcut değil")


def _display_chance_creation_tab(home: Dict, away: Dict):
    """Şans yaratma tab"""
    
    st.markdown("### 🎨 Şans Yaratma Kalitesi (xA)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🏠 Ev Sahibi")
        if home.get('chance_creation'):
            cc = home['chance_creation']
            
            st.metric("xA (Expected Assists)", f"{cc.get('team_xa', 0):.2f}")
            st.metric("Playmaker Score", f"{cc.get('playmaker_score', 0):.1f}/100")
            st.metric("Chance Quality", f"{cc.get('chance_quality', 0):.1f}/100")
        else:
            st.info("Chance creation verisi mevcut değil")
    
    with col2:
        st.markdown("#### ✈️ Deplasman")
        if away.get('chance_creation'):
            cc = away['chance_creation']
            
            st.metric("xA (Expected Assists)", f"{cc.get('team_xa', 0):.2f}")
            st.metric("Playmaker Score", f"{cc.get('playmaker_score', 0):.1f}/100")
            st.metric("Chance Quality", f"{cc.get('chance_quality', 0):.1f}/100")
        else:
            st.info("Chance creation verisi mevcut değil")
    
    # Comparison
    if home.get('chance_creation') and away.get('chance_creation'):
        st.markdown("---")
        st.markdown("#### 📊 Şans Yaratma Karşılaştırma")
        
        fig = go.Figure(data=[
            go.Bar(
                name='Ev Sahibi',
                x=['xA', 'Playmaker', 'Kalite'],
                y=[
                    home['chance_creation'].get('team_xa', 0),
                    home['chance_creation'].get('playmaker_score', 0) / 20,  # Scale to match xA
                    home['chance_creation'].get('chance_quality', 0) / 20
                ],
                marker_color='lightblue'
            ),
            go.Bar(
                name='Deplasman',
                x=['xA', 'Playmaker', 'Kalite'],
                y=[
                    away['chance_creation'].get('team_xa', 0),
                    away['chance_creation'].get('playmaker_score', 0) / 20,
                    away['chance_creation'].get('chance_quality', 0) / 20
                ],
                marker_color='lightcoral'
            )
        ])
        
        fig.update_layout(
            barmode='group',
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)


# Quick integration function for existing app
def show_advanced_metrics_if_available(
    api_key: str,
    base_url: str,
    home_team_id: int,
    away_team_id: int,
    home_team_name: str,
    away_team_name: str,
    league_id: int,
    season: int,
    home_stats: Optional[Dict] = None,
    away_stats: Optional[Dict] = None
):
    """
    Mevcut app.py'den kolayca çağrılabilir wrapper fonksiyon
    
    Usage in app.py:
        from advanced_metrics_display import show_advanced_metrics_if_available
        
        show_advanced_metrics_if_available(
            api_key=API_KEY,
            base_url=BASE_URL,
            home_team_id=645,
            away_team_id=610,
            home_team_name="Galatasaray",
            away_team_name="Fenerbahçe",
            league_id=203,
            season=2024
        )
    """
    
    if not ADVANCED_METRICS_AVAILABLE:
        st.warning("⚠️ Advanced Metrics modülleri yüklü değil")
        return
    
    try:
        from enhanced_match_analysis import get_enhanced_match_analysis
        
        with st.spinner("🔬 Gelişmiş metrikler hesaplanıyor..."):
            # Get enhanced analysis
            analysis = get_enhanced_match_analysis(
                api_key=api_key,
                base_url=base_url,
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                home_team_name=home_team_name,
                away_team_name=away_team_name,
                league_id=league_id,
                season=season
            )
            
            if analysis.get('advanced_analysis'):
                adv = analysis['advanced_analysis']
                
                # Display dashboard
                display_advanced_metrics_dashboard(
                    home_team_analysis=adv['home_team'],
                    away_team_analysis=adv['away_team'],
                    match_prediction=adv['prediction']
                )
            else:
                st.error("❌ Advanced analysis oluşturulamadı")
    
    except Exception as e:
        st.error(f"❌ Advanced metrics gösterilirken hata: {e}")
        import traceback
        with st.expander("🔍 Hata Detayı"):
            st.code(traceback.format_exc())


# ==================== PHASE 3.4 - NEW ANALYZER DISPLAYS ====================

def display_new_analyzers_dashboard(
    api_key: str,
    base_url: str,
    home_team_id: int,
    away_team_id: int,
    home_team_name: str,
    away_team_name: str,
    fixture_id: Optional[int] = None,
    league_id: Optional[int] = None,
    season: Optional[int] = None
):
    """
    Phase 3.3'te oluşturulan yeni analyzer'lar için dashboard
    
    Args:
        fixture_id: Maç ID'si (isteğe bağlı - gerçek maç verisi için)
        league_id: Lig ID'si
        season: Sezon
    """
    
    st.markdown("## 📊 Detaylı Performans Analizi")
    st.markdown("*Shot Analysis, Passing Network, Defensive Stats*")
    st.markdown("---")
    
    # Import analyzers
    try:
        from shot_analyzer import ShotAnalyzer
        from passing_analyzer import PassingAnalyzer
        from defensive_analyzer import DefensiveAnalyzer
        from api_utils import (
            get_fixture_statistics,
            get_fixture_events,
            get_team_top_scorers,
            get_team_top_assists
        )
        
        shot_analyzer = ShotAnalyzer()
        passing_analyzer = PassingAnalyzer()
        defensive_analyzer = DefensiveAnalyzer()
        
    except ImportError as e:
        st.error(f"⚠️ Analyzer modülleri yüklenemedi: {e}")
        return
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎯 Shot Analysis",
        "⚽ Passing Network", 
        "🛡️ Defensive Stats",
        "⭐ Key Players"
    ])
    
    with tab1:
        _display_shot_analysis_tab(
            api_key, base_url, fixture_id,
            home_team_name, away_team_name,
            shot_analyzer
        )
    
    with tab2:
        _display_passing_network_tab(
            api_key, base_url, fixture_id,
            home_team_name, away_team_name,
            passing_analyzer
        )
    
    with tab3:
        _display_defensive_stats_tab(
            api_key, base_url, fixture_id,
            home_team_name, away_team_name,
            defensive_analyzer
        )
    
    with tab4:
        _display_key_players_tab(
            api_key, base_url, 
            home_team_id, away_team_id,
            home_team_name, away_team_name,
            league_id, season
        )


def _display_shot_analysis_tab(
    api_key: str,
    base_url: str,
    fixture_id: Optional[int],
    home_team_name: str,
    away_team_name: str,
    shot_analyzer
):
    """Shot Analysis tab"""
    
    st.markdown("### 🎯 Shot Quality & xG Analysis")
    
    if not fixture_id:
        st.info("ℹ️ Maç seçildiğinde gerçek shot verileri gösterilecek")
        
        # Mock data for demonstration
        st.markdown("**Demo Verisi (Örnek Maç)**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"#### 🏠 {home_team_name}")
            
            # Mock shot data
            home_shots = {
                'total_shots': 15,
                'shots_on_target': 7,
                'shot_accuracy': 46.7,
                'xg_total': 1.85,
                'xg_per_shot': 0.123,
                'shot_quality': 'medium',
                'conversion_rate': 13.3,
                'inside_box': 10,
                'outside_box': 5
            }
            
            _render_shot_metrics(home_shots)
        
        with col2:
            st.markdown(f"#### ✈️ {away_team_name}")
            
            # Mock shot data
            away_shots = {
                'total_shots': 12,
                'shots_on_target': 5,
                'shot_accuracy': 41.7,
                'xg_total': 1.35,
                'xg_per_shot': 0.113,
                'shot_quality': 'low',
                'conversion_rate': 8.3,
                'inside_box': 7,
                'outside_box': 5
            }
            
            _render_shot_metrics(away_shots)
        
        # Comparison
        st.markdown("---")
        st.markdown("### 📊 Shot Comparison")
        
        comparison = shot_analyzer.compare_teams_shooting(home_shots, away_shots)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Shot Dominance", comparison['shot_dominance'].upper())
        with col2:
            st.metric("Quality Winner", comparison['quality_winner'].upper())
        with col3:
            st.metric("Home Advantage", comparison['home_advantage'])
        
        # Insights
        if comparison['key_insights']:
            st.markdown("**💡 Key Insights:**")
            for insight in comparison['key_insights']:
                st.markdown(f"• {insight}")
    
    else:  # fixture_id mevcut - gerçek veriyi kullan
        from api_utils import get_fixture_statistics_detailed, get_fixture_events
        
        with st.spinner("📥 Gerçek maç verisi yükleniyor..."):
            stats_data, stats_error = get_fixture_statistics_detailed(api_key, base_url, fixture_id, skip_limit=True)
            events_data, events_error = get_fixture_events(api_key, base_url, fixture_id, skip_limit=True)
            
            if stats_error or not stats_data:
                st.error(f"❌ İstatistik verisi yüklenemedi: {stats_error}")
                return
            
            # Parse team statistics
            # API returns: {'response': [{'team': {...}, 'statistics': [...]}, {'team': {...}, 'statistics': [...]}]}
            teams_stats = stats_data.get('response', [])
            
            if len(teams_stats) < 2:
                st.warning("⚠️ İki takım verisi bulunamadı")
                return
            
            # Determine home/away teams
            team1_stats = teams_stats[0]
            team2_stats = teams_stats[1]
            
            # Create stats dict for each team
            team1_dict = {'statistics': team1_stats.get('statistics', [])}
            team2_dict = {'statistics': team2_stats.get('statistics', [])}
            
            # Analyze shots
            home_shot_analysis = shot_analyzer.analyze_match_shots(
                match_events=events_data.get('response', []) if events_data else [],
                match_stats=team1_dict
            )
            
            away_shot_analysis = shot_analyzer.analyze_match_shots(
                match_events=events_data.get('response', []) if events_data else [],
                match_stats=team2_dict
            )
            
            # Display results
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"#### 🏠 {team1_stats.get('team', {}).get('name', home_team_name)}")
                _render_shot_metrics(home_shot_analysis)
            
            with col2:
                st.markdown(f"#### ✈️ {team2_stats.get('team', {}).get('name', away_team_name)}")
                _render_shot_metrics(away_shot_analysis)
            
            # Comparison
            st.markdown("---")
            st.markdown("### 📊 Shot Comparison")
            
            comparison = shot_analyzer.compare_teams_shooting(home_shot_analysis, away_shot_analysis)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Shot Dominance", comparison['shot_dominance'].upper())
            with col2:
                st.metric("Quality Winner", comparison['quality_winner'].upper())
            with col3:
                home_adv = comparison.get('home_advantage', 'N/A')
                st.metric("Home Advantage", home_adv if isinstance(home_adv, str) else f"{home_adv:.1f}%")
            
            # Insights
            if comparison.get('key_insights'):
                st.markdown("**💡 Key Insights:**")
                for insight in comparison['key_insights']:
                    st.markdown(f"• {insight}")
            
            # Recommendations
            st.markdown("---")
            st.markdown("### 💡 Tactical Recommendations")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**🏠 Home Team:**")
                home_recs = shot_analyzer.get_shooting_recommendations(home_shot_analysis)
                for rec in home_recs:
                    st.markdown(f"• {rec}")
            
            with col2:
                st.markdown("**✈️ Away Team:**")
                away_recs = shot_analyzer.get_shooting_recommendations(away_shot_analysis)
                for rec in away_recs:
                    st.markdown(f"• {rec}")


def _render_shot_metrics(shot_data: Dict):
    """Render shot metrics"""
    
    # Key metrics
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Shots", shot_data['total_shots'])
        st.metric("On Target", f"{shot_data['shots_on_target']} ({shot_data['shot_accuracy']:.1f}%)")
    
    with col2:
        st.metric("Expected Goals (xG)", f"{shot_data['xg_total']:.2f}")
        st.metric("xG per Shot", f"{shot_data['xg_per_shot']:.3f}")
    
    # Shot quality indicator
    quality = shot_data['shot_quality']
    quality_color = {
        'high': '🟢',
        'medium': '🟡',
        'low': '🔴'
    }.get(quality.lower(), '⚪')
    
    st.markdown(f"**Shot Quality:** {quality_color} {quality.upper()}")
    
    # Shot location breakdown
    st.markdown("**Shot Locations:**")
    st.progress(shot_data['inside_box'] / shot_data['total_shots'])
    st.caption(f"Inside Box: {shot_data['inside_box']} | Outside: {shot_data['outside_box']}")


def _display_passing_network_tab(
    api_key: str,
    base_url: str,
    fixture_id: Optional[int],
    home_team_name: str,
    away_team_name: str,
    passing_analyzer
):
    """Passing Network tab"""
    
    st.markdown("### ⚽ Passing & Build-up Analysis")
    
    if not fixture_id:
        st.info("ℹ️ Maç seçildiğinde gerçek passing verileri gösterilecek")
        
        # Mock data
        st.markdown("**Demo Verisi (Örnek Maç)**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"#### 🏠 {home_team_name}")
            
            home_passing = {
                'total_passes': 485,
                'accurate_passes': 412,
                'pass_accuracy': 84.9,
                'possession_pct': 58.0,
                'key_passes': 12,
                'progressive_passes_est': 58,
                'passing_quality': 'excellent',
                'creativity_score': 78.5,
                'build_up_quality': 'high'
            }
            
            _render_passing_metrics(home_passing)
        
        with col2:
            st.markdown(f"#### ✈️ {away_team_name}")
            
            away_passing = {
                'total_passes': 358,
                'accurate_passes': 285,
                'pass_accuracy': 79.6,
                'possession_pct': 42.0,
                'key_passes': 8,
                'progressive_passes_est': 43,
                'passing_quality': 'good',
                'creativity_score': 62.3,
                'build_up_quality': 'medium'
            }
            
            _render_passing_metrics(away_passing)
        
        # Comparison
        st.markdown("---")
        st.markdown("### 📊 Passing Comparison")
        
        comparison = passing_analyzer.compare_passing_styles(home_passing, away_passing)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Possession Winner", comparison['possession_winner'].upper())
        with col2:
            st.metric("Accuracy Winner", comparison['accuracy_winner'].upper())
        with col3:
            st.metric("Dominance", comparison['passing_dominance'].upper())
        
        st.info(f"**Style:** {comparison['style_difference']}")
        
        if comparison['key_insights']:
            st.markdown("**💡 Key Insights:**")
            for insight in comparison['key_insights']:
                st.markdown(f"• {insight}")
    
    else:
        # Real match data
        from api_utils import get_fixture_statistics_detailed
        
        with st.spinner("📥 Gerçek passing verisi yükleniyor..."):
            stats_data, error = get_fixture_statistics_detailed(api_key, base_url, fixture_id, skip_limit=True)
            
            if error or not stats_data:
                st.error(f"❌ İstatistik verisi yüklenemedi: {error}")
                return
            
            teams_stats = stats_data.get('response', [])
            
            if len(teams_stats) < 2:
                st.warning("⚠️ İki takım verisi bulunamadı")
                return
            
            team1_stats = teams_stats[0]
            team2_stats = teams_stats[1]
            
            team1_dict = {'statistics': team1_stats.get('statistics', [])}
            team2_dict = {'statistics': team2_stats.get('statistics', [])}
            
            # Analyze passing
            home_passing = passing_analyzer.analyze_passing_performance(match_stats=team1_dict)
            away_passing = passing_analyzer.analyze_passing_performance(match_stats=team2_dict)
            
            # Display results
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"#### 🏠 {team1_stats.get('team', {}).get('name', home_team_name)}")
                _render_passing_metrics(home_passing)
            
            with col2:
                st.markdown(f"#### ✈️ {team2_stats.get('team', {}).get('name', away_team_name)}")
                _render_passing_metrics(away_passing)
            
            # Comparison
            st.markdown("---")
            st.markdown("### 📊 Passing Comparison")
            
            comparison = passing_analyzer.compare_passing_styles(home_passing, away_passing)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Possession Winner", comparison['possession_winner'].upper())
            with col2:
                st.metric("Accuracy Winner", comparison['accuracy_winner'].upper())
            with col3:
                st.metric("Dominance", comparison['passing_dominance'].upper())
            
            st.info(f"**Style:** {comparison['style_difference']}")
            
            if comparison.get('key_insights'):
                st.markdown("**💡 Key Insights:**")
                for insight in comparison['key_insights']:
                    st.markdown(f"• {insight}")
            
            # Recommendations
            st.markdown("---")
            st.markdown("### 💡 Tactical Recommendations")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**🏠 Home Team:**")
                home_recs = passing_analyzer.get_passing_recommendations(home_passing)
                for rec in home_recs:
                    st.markdown(f"• {rec}")
            
            with col2:
                st.markdown("**✈️ Away Team:**")
                away_recs = passing_analyzer.get_passing_recommendations(away_passing)
                for rec in away_recs:
                    st.markdown(f"• {rec}")


def _render_passing_metrics(passing_data: Dict):
    """Render passing metrics"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Passes", passing_data['total_passes'])
        st.metric("Pass Accuracy", f"{passing_data['pass_accuracy']:.1f}%")
        st.metric("Possession", f"{passing_data['possession_pct']:.1f}%")
    
    with col2:
        st.metric("Key Passes", passing_data['key_passes'])
        st.metric("Progressive Passes", passing_data['progressive_passes_est'])
        st.metric("Creativity Score", f"{passing_data['creativity_score']:.1f}/100")
    
    # Quality indicators
    quality = passing_data['passing_quality']
    quality_color = {
        'excellent': '🟢',
        'good': '🟡',
        'average': '🟠',
        'poor': '🔴'
    }.get(quality, '⚪')
    
    build_up = passing_data['build_up_quality']
    build_color = {
        'high': '🟢',
        'medium': '🟡',
        'low': '🔴'
    }.get(build_up, '⚪')
    
    st.markdown(f"**Passing Quality:** {quality_color} {quality.upper()}")
    st.markdown(f"**Build-up Quality:** {build_color} {build_up.upper()}")


def _display_defensive_stats_tab(
    api_key: str,
    base_url: str,
    fixture_id: Optional[int],
    home_team_name: str,
    away_team_name: str,
    defensive_analyzer
):
    """Defensive Stats tab"""
    
    st.markdown("### 🛡️ Defensive Performance Analysis")
    
    if not fixture_id:
        st.info("ℹ️ Maç seçildiğinde gerçek defensive verileri gösterilecek")
        
        # Mock data
        st.markdown("**Demo Verisi (Örnek Maç)**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"#### 🏠 {home_team_name}")
            
            home_defense = {
                'tackles': 19,
                'interceptions': 13,
                'blocks': 6,
                'clearances': 28,
                'defensive_actions': 66,
                'duel_success_rate': 57.8,
                'goals_conceded': 1,
                'defensive_quality': 'excellent',
                'defensive_rating': 78.5,
                'vulnerability_score': 21.5,
                'defensive_style': 'balanced',
                'fouls': 11,
                'yellow_cards': 2
            }
            
            _render_defensive_metrics(home_defense)
        
        with col2:
            st.markdown(f"#### ✈️ {away_team_name}")
            
            away_defense = {
                'tackles': 16,
                'interceptions': 9,
                'blocks': 4,
                'clearances': 22,
                'defensive_actions': 51,
                'duel_success_rate': 51.2,
                'goals_conceded': 2,
                'defensive_quality': 'good',
                'defensive_rating': 65.3,
                'vulnerability_score': 34.7,
                'defensive_style': 'aggressive',
                'fouls': 15,
                'yellow_cards': 3
            }
            
            _render_defensive_metrics(away_defense)
        
        # Comparison
        st.markdown("---")
        st.markdown("### 📊 Defensive Comparison")
        
        comparison = defensive_analyzer.compare_defenses(home_defense, away_defense)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Defensive Winner", comparison['defensive_winner'].upper())
            st.metric("Vulnerability", comparison['vulnerability_comparison'])
        
        with col2:
            st.metric("Expected Goals (Home)", comparison['expected_goals_conceded']['home'])
            st.metric("Expected Goals (Away)", comparison['expected_goals_conceded']['away'])
        
        if comparison['key_insights']:
            st.markdown("**💡 Key Insights:**")
            for insight in comparison['key_insights']:
                st.markdown(f"• {insight}")
    
    else:
        # Real match data
        from api_utils import get_fixture_statistics_detailed
        from fixture_goals_helper import get_fixture_details_with_goals
        
        with st.spinner("📥 Gerçek defensive verisi yükleniyor..."):
            # Get stats AND goals
            stats_data, goals_data, error = get_fixture_details_with_goals(
                api_key, base_url, fixture_id, skip_limit=True
            )
            
            if error or not stats_data:
                st.error(f"❌ İstatistik verisi yüklenemedi: {error}")
                return
            
            teams_stats = stats_data.get('response', [])
            
            if len(teams_stats) < 2:
                st.warning("⚠️ İki takım verisi bulunamadı")
                return
            
            team1_stats = teams_stats[0]
            team2_stats = teams_stats[1]
            
            team1_dict = {'statistics': team1_stats.get('statistics', [])}
            team2_dict = {'statistics': team2_stats.get('statistics', [])}
            
            # Get goals conceded from ACTUAL match score
            team1_goals_conceded = goals_data['away_goals'] if goals_data else 0  # Home concedes away goals
            team2_goals_conceded = goals_data['home_goals'] if goals_data else 0  # Away concedes home goals
            
            # Analyze defense
            home_defense = defensive_analyzer.analyze_defensive_performance(
                match_stats=team1_dict,
                goals_conceded=team1_goals_conceded
            )
            
            away_defense = defensive_analyzer.analyze_defensive_performance(
                match_stats=team2_dict,
                goals_conceded=team2_goals_conceded
            )
            
            # Display results
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"#### 🏠 {team1_stats.get('team', {}).get('name', home_team_name)}")
                _render_defensive_metrics(home_defense)
            
            with col2:
                st.markdown(f"#### ✈️ {team2_stats.get('team', {}).get('name', away_team_name)}")
                _render_defensive_metrics(away_defense)
            
            # Comparison
            st.markdown("---")
            st.markdown("### 📊 Defensive Comparison")
            
            comparison = defensive_analyzer.compare_defenses(home_defense, away_defense)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Defensive Winner", comparison['defensive_winner'].upper())
                st.metric("Vulnerability", comparison['vulnerability_comparison'])
            
            with col2:
                st.metric("Expected Goals (Home)", comparison['expected_goals_conceded']['home'])
                st.metric("Expected Goals (Away)", comparison['expected_goals_conceded']['away'])
            
            if comparison.get('key_insights'):
                st.markdown("**💡 Key Insights:**")
                for insight in comparison['key_insights']:
                    st.markdown(f"• {insight}")
            
            # Recommendations
            st.markdown("---")
            st.markdown("### 💡 Tactical Recommendations")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**🏠 Home Team:**")
                home_recs = defensive_analyzer.get_defensive_recommendations(home_defense)
                for rec in home_recs:
                    st.markdown(f"• {rec}")
            
            with col2:
                st.markdown("**✈️ Away Team:**")
                away_recs = defensive_analyzer.get_defensive_recommendations(away_defense)
                for rec in away_recs:
                    st.markdown(f"• {rec}")


def _render_defensive_metrics(defense_data: Dict):
    """Render defensive metrics"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Tackles", defense_data['tackles'])
        st.metric("Interceptions", defense_data['interceptions'])
        st.metric("Blocks", defense_data['blocks'])
        st.metric("Clearances", defense_data['clearances'])
    
    with col2:
        st.metric("Total Actions", defense_data['defensive_actions'])
        st.metric("Duel Success", f"{defense_data['duel_success_rate']:.1f}%")
        st.metric("Defensive Rating", f"{defense_data['defensive_rating']:.1f}/100")
        st.metric("Vulnerability", f"{defense_data['vulnerability_score']:.1f}/100")
    
    # Style and quality
    quality = defense_data['defensive_quality']
    quality_color = {
        'excellent': '🟢',
        'good': '🟡',
        'average': '🟠',
        'poor': '🔴'
    }.get(quality, '⚪')
    
    style = defense_data['defensive_style']
    
    st.markdown(f"**Defensive Quality:** {quality_color} {quality.upper()}")
    st.markdown(f"**Defensive Style:** {style.upper()}")
    st.caption(f"Fouls: {defense_data['fouls']} | Yellow Cards: {defense_data['yellow_cards']}")


def _display_key_players_tab(
    api_key: str,
    base_url: str,
    home_team_id: int,
    away_team_id: int,
    home_team_name: str,
    away_team_name: str,
    league_id: Optional[int],
    season: Optional[int]
):
    """Key Players tab"""
    
    st.markdown("### ⭐ Top Performers & Key Players")
    
    if not league_id or not season:
        st.warning("⚠️ Lig ve sezon bilgisi gerekli")
        return
    
    from api_utils import get_team_top_scorers, get_team_top_assists
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"#### 🏠 {home_team_name}")
        
        with st.spinner("📥 Top scorers yükleniyor..."):
            scorers, error = get_team_top_scorers(
                api_key, base_url, home_team_id, league_id, season, limit=5, skip_limit=True
            )
            
            if scorers:
                st.markdown("**⚽ Top Scorers:**")
                for i, player in enumerate(scorers[:5], 1):
                    player_info = player.get('player', {})
                    stats = player.get('statistics', [{}])[0]
                    goals = stats.get('goals', {}).get('total', 0)
                    st.markdown(f"{i}. {player_info.get('name', 'Unknown')} - **{goals} goals**")
            else:
                st.info("Golcü bilgisi bulunamadı")
        
        with st.spinner("📥 Top assists yükleniyor..."):
            assisters, error = get_team_top_assists(
                api_key, base_url, home_team_id, league_id, season, limit=5, skip_limit=True
            )
            
            if assisters:
                st.markdown("**🎯 Top Assists:**")
                for i, player in enumerate(assisters[:5], 1):
                    player_info = player.get('player', {})
                    stats = player.get('statistics', [{}])[0]
                    assists = stats.get('goals', {}).get('assists', 0)
                    st.markdown(f"{i}. {player_info.get('name', 'Unknown')} - **{assists} assists**")
            else:
                st.info("Asist bilgisi bulunamadı")
    
    with col2:
        st.markdown(f"#### ✈️ {away_team_name}")
        
        with st.spinner("📥 Top scorers yükleniyor..."):
            scorers, error = get_team_top_scorers(
                api_key, base_url, away_team_id, league_id, season, limit=5, skip_limit=True
            )
            
            if scorers:
                st.markdown("**⚽ Top Scorers:**")
                for i, player in enumerate(scorers[:5], 1):
                    player_info = player.get('player', {})
                    stats = player.get('statistics', [{}])[0]
                    goals = stats.get('goals', {}).get('total', 0)
                    st.markdown(f"{i}. {player_info.get('name', 'Unknown')} - **{goals} goals**")
            else:
                st.info("Golcü bilgisi bulunamadı")
        
        with st.spinner("📥 Top assists yükleniyor..."):
            assisters, error = get_team_top_assists(
                api_key, base_url, away_team_id, league_id, season, limit=5, skip_limit=True
            )
            
            if assisters:
                st.markdown("**🎯 Top Assists:**")
                for i, player in enumerate(assisters[:5], 1):
                    player_info = player.get('player', {})
                    stats = player.get('statistics', [{}])[0]
                    assists = stats.get('goals', {}).get('assists', 0)
                    st.markdown(f"{i}. {player_info.get('name', 'Unknown')} - **{assists} assists**")
            else:
                st.info("Asist bilgisi bulunamadı")
