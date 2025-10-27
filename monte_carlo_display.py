"""
Poisson & Monte Carlo Simülasyon Görselleştirme Modülü
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional


def display_probability_matrix(prob_matrix: np.ndarray, max_display: int = 6):
    """
    Olasılık matrisini ısı haritası olarak göster
    
    Args:
        prob_matrix: Olasılık matrisi
        max_display: Gösterilecek maksimum gol sayısı
    """
    st.markdown("### 🎯 Skor Olasılık Matrisi")
    
    # Matrisi küçült
    display_matrix = prob_matrix[:max_display+1, :max_display+1]
    
    # Yüzdeye çevir
    display_matrix_pct = display_matrix * 100
    
    # Isı haritası
    fig = go.Figure(data=go.Heatmap(
        z=display_matrix_pct,
        x=[str(i) for i in range(max_display+1)],
        y=[str(i) for i in range(max_display+1)],
        colorscale='RdYlGn',
        text=display_matrix_pct,
        texttemplate='%{text:.2f}%',
        textfont={"size": 10},
        colorbar=dict(title="Olasılık (%)"),
        hoverongaps=False,
        hovertemplate='Ev Sahibi: %{y}<br>Deplasman: %{x}<br>Olasılık: %{z:.2f}%<extra></extra>'
    ))
    
    fig.update_layout(
        title='Maç Skoru Olasılık Matrisi',
        xaxis_title='Deplasman Gol Sayısı',
        yaxis_title='Ev Sahibi Gol Sayısı',
        height=500,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # En olası skorlar
    st.markdown("#### 🏅 En Yüksek Olasılıklı Skorlar")
    
    # Flatten ve sırala
    scores_flat = []
    for i in range(max_display+1):
        for j in range(max_display+1):
            scores_flat.append({
                'Skor': f"{i}-{j}",
                'Olasılık': display_matrix_pct[i, j]
            })
    
    scores_df = pd.DataFrame(scores_flat)
    scores_df = scores_df.sort_values('Olasılık', ascending=False).head(10)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # En olası skoru kaydet (formatlamadan önce)
        top_score_info = scores_df.iloc[0].copy()
        top_prob_value = top_score_info['Olasılık']
        
        # Format olasılık sütunu (görüntüleme için)
        scores_df_display = scores_df.copy()
        scores_df_display['Olasılık'] = scores_df_display['Olasılık'].apply(lambda x: f"{x:.2f}%")
        st.dataframe(
            scores_df_display,
            use_container_width=True,
            hide_index=True
        )
    
    with col2:
        # En olası skor kartı
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 20px; border-radius: 10px; text-align: center;'>
            <h2 style='color: white; margin: 0;'>{top_score_info['Skor']}</h2>
            <p style='color: #e0e0e0; margin: 5px 0;'>En Olası Skor</p>
            <h3 style='color: white; margin: 0;'>{top_prob_value:.2f}%</h3>
        </div>
        """, unsafe_allow_html=True)


def display_match_outcome_probabilities(poisson_results: Dict, mc_results: Optional[Dict] = None,
                                        home_team: str = "Ev Sahibi", away_team: str = "Deplasman"):
    """
    Maç sonucu olasılıklarını görselleştir
    """
    st.markdown("### 📊 Maç Sonucu Olasılıkları")
    
    # Kartlar
    col1, col2, col3 = st.columns(3)
    
    with col1:
        home_win_prob = poisson_results['home_win'] * 100
        st.metric(
            f"🏆 {home_team} Kazanır",
            f"{home_win_prob:.1f}%",
            delta=None,
            help="Poisson dağılımına göre kazanma olasılığı"
        )
        
        if mc_results:
            mc_prob = mc_results['probabilities']['home_win'] * 100
            st.caption(f"Monte Carlo: {mc_prob:.1f}%")
    
    with col2:
        draw_prob = poisson_results['draw'] * 100
        st.metric(
            "🤝 Beraberlik",
            f"{draw_prob:.1f}%",
            delta=None
        )
        
        if mc_results:
            mc_prob = mc_results['probabilities']['draw'] * 100
            st.caption(f"Monte Carlo: {mc_prob:.1f}%")
    
    with col3:
        away_win_prob = poisson_results['away_win'] * 100
        st.metric(
            f"🏆 {away_team} Kazanır",
            f"{away_win_prob:.1f}%",
            delta=None
        )
        
        if mc_results:
            mc_prob = mc_results['probabilities']['away_win'] * 100
            st.caption(f"Monte Carlo: {mc_prob:.1f}%")
    
    # Bar grafiği
    categories = [f'{home_team} Kazanır', 'Beraberlik', f'{away_team} Kazanır']
    poisson_probs = [
        poisson_results['home_win'] * 100,
        poisson_results['draw'] * 100,
        poisson_results['away_win'] * 100
    ]
    
    fig = go.Figure()
    
    # Poisson
    fig.add_trace(go.Bar(
        name='Poisson',
        x=categories,
        y=poisson_probs,
        marker_color=['#4CAF50', '#FFC107', '#F44336'],
        text=[f'{p:.1f}%' for p in poisson_probs],
        textposition='auto',
        textfont=dict(size=14, color='white')
    ))
    
    # Monte Carlo (varsa)
    if mc_results:
        mc_probs = [
            mc_results['probabilities']['home_win'] * 100,
            mc_results['probabilities']['draw'] * 100,
            mc_results['probabilities']['away_win'] * 100
        ]
        
        fig.add_trace(go.Bar(
            name='Monte Carlo',
            x=categories,
            y=mc_probs,
            marker_color=['#66BB6A', '#FFCA28', '#EF5350'],
            text=[f'{p:.1f}%' for p in mc_probs],
            textposition='auto',
            textfont=dict(size=14, color='white'),
            opacity=0.7
        ))
    
    fig.update_layout(
        title='Maç Sonucu Olasılıkları Karşılaştırması',
        xaxis_title='',
        yaxis_title='Olasılık (%)',
        yaxis=dict(range=[0, 100]),
        barmode='group',
        height=400,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=True if mc_results else False
    )
    
    st.plotly_chart(fig, use_container_width=True)


def display_over_under_analysis(poisson_results: Dict, mc_results: Optional[Dict] = None):
    """Over/Under analizi"""
    st.markdown("### 🎯 Over/Under Analizi")
    
    thresholds = [0.5, 1.5, 2.5, 3.5, 4.5]
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Grafik
        over_probs_poisson = [poisson_results['over_under'][f'over_{t}'] * 100 for t in thresholds]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=[f'Over {t}' for t in thresholds],
            y=over_probs_poisson,
            mode='lines+markers',
            name='Poisson',
            line=dict(color='#4CAF50', width=3),
            marker=dict(size=10),
            text=[f'{p:.1f}%' for p in over_probs_poisson],
            textposition='top center'
        ))
        
        if mc_results:
            over_probs_mc = [mc_results['over_under'][f'over_{t}'] * 100 for t in thresholds]
            fig.add_trace(go.Scatter(
                x=[f'Over {t}' for t in thresholds],
                y=over_probs_mc,
                mode='lines+markers',
                name='Monte Carlo',
                line=dict(color='#2196F3', width=3, dash='dash'),
                marker=dict(size=10),
                text=[f'{p:.1f}%' for p in over_probs_mc],
                textposition='bottom center'
            ))
        
        fig.update_layout(
            title='Over Olasılıkları',
            xaxis_title='Eşik Değer',
            yaxis_title='Olasılık (%)',
            yaxis=dict(range=[0, 100]),
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            showlegend=True if mc_results else False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # En popüler over/under
        st.markdown("#### 💡 Önerilen Bahisler")
        
        for threshold in [2.5, 3.5]:
            over_prob = poisson_results['over_under'][f'over_{threshold}'] * 100
            under_prob = poisson_results['over_under'][f'under_{threshold}'] * 100
            
            if over_prob > 55:
                st.success(f"✅ **Over {threshold}** - {over_prob:.1f}%")
            elif under_prob > 55:
                st.info(f"🔽 **Under {threshold}** - {under_prob:.1f}%")
            else:
                st.warning(f"⚠️ **Over/Under {threshold}** - Belirsiz")


def display_btts_analysis(poisson_results: Dict, mc_results: Optional[Dict] = None):
    """Karşılıklı Gol (BTTS) analizi"""
    st.markdown("### ⚽ Karşılıklı Gol (BTTS) Analizi")
    
    col1, col2 = st.columns(2)
    
    with col1:
        btts_yes = poisson_results['btts_yes'] * 100
        btts_no = poisson_results['btts_no'] * 100
        
        # Pie chart
        fig = go.Figure(data=[go.Pie(
            labels=['BTTS VAR', 'BTTS YOK'],
            values=[btts_yes, btts_no],
            marker=dict(colors=['#4CAF50', '#F44336']),
            textinfo='label+percent',
            textposition='inside',
            hole=0.4,
            textfont=dict(size=16, color='white')
        )])
        
        fig.update_layout(
            title='Poisson - BTTS Dağılımı',
            height=350,
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if mc_results:
            mc_btts_yes = mc_results['btts_yes'] * 100
            mc_btts_no = mc_results['btts_no'] * 100
            
            fig = go.Figure(data=[go.Pie(
                labels=['BTTS VAR', 'BTTS YOK'],
                values=[mc_btts_yes, mc_btts_no],
                marker=dict(colors=['#66BB6A', '#EF5350']),
                textinfo='label+percent',
                textposition='inside',
                hole=0.4,
                textfont=dict(size=16, color='white')
            )])
            
            fig.update_layout(
                title='Monte Carlo - BTTS Dağılımı',
                height=350,
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # Öneri
    if btts_yes > 60:
        st.success(f"✅ **Tavsiye:** BTTS VAR - {btts_yes:.1f}% olasılık")
    elif btts_no > 60:
        st.info(f"🔽 **Tavsiye:** BTTS YOK - {btts_no:.1f}% olasılık")
    else:
        st.warning("⚠️ BTTS için belirsizlik var, diğer faktörleri değerlendirin")


def display_monte_carlo_distribution(mc_results: Dict):
    """Monte Carlo simülasyon dağılımı"""
    st.markdown("### 🎲 Monte Carlo Simülasyon Dağılımı")
    
    # Skor dağılımı
    scores = [f"{h}-{a}" for h, a in mc_results['score_distribution'][:20]]
    counts = [count for _, count in mc_results['score_distribution'][:20]]
    percentages = [(count / mc_results['total_simulations']) * 100 for _, count in mc_results['score_distribution'][:20]]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=scores,
        y=percentages,
        marker=dict(
            color=percentages,
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="Oran (%)")
        ),
        text=[f'{p:.1f}%' for p in percentages],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Olasılık: %{y:.2f}%<br>Sayı: %{customdata}<extra></extra>',
        customdata=counts
    ))
    
    fig.update_layout(
        title=f'En Sık Görülen 20 Skor ({mc_results["total_simulations"]:,} Simülasyon)',
        xaxis_title='Skor',
        yaxis_title='Görülme Oranı (%)',
        height=500,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # İstatistikler
    st.markdown("#### 📈 Simülasyon İstatistikleri")
    
    col1, col2, col3, col4 = st.columns(4)
    
    stats = mc_results['statistics']
    
    with col1:
        st.metric("Ortalama Ev Sahibi Gol", f"{stats['avg_home_goals']:.2f}")
    
    with col2:
        st.metric("Ortalama Deplasman Gol", f"{stats['avg_away_goals']:.2f}")
    
    with col3:
        st.metric("Medyan Ev Sahibi Gol", f"{stats['median_home_goals']:.0f}")
    
    with col4:
        st.metric("Medyan Deplasman Gol", f"{stats['median_away_goals']:.0f}")


# Test
if __name__ == "__main__":
    print("✅ Monte Carlo görselleştirme modülü hazır")
