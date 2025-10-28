"""
Value Bet Detector Görselleştirme Modülü
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Optional


def display_value_bets_table(value_bets: List[Dict]):
    """Value betleri tablo olarak göster"""
    if not value_bets:
        st.info("💡 Value bet bulunamadı. Bahisçi oranları model tahminlerine çok yakın.")
        return
    
    st.markdown(f"### 💎 Bulunan Value Betler ({len(value_bets)})")
    
    # DataFrame oluştur
    df_data = []
    for vb in value_bets:
        # Rating emoji
        ev = vb['expected_value']
        if ev >= 15:
            rating = "⭐⭐⭐"
        elif ev >= 10:
            rating = "⭐⭐"
        elif ev >= 5:
            rating = "⭐"
        else:
            rating = "💡"
        
        df_data.append({
            'Rating': rating,
            'Sonuç': vb['outcome'],
            'Oran': f"{vb['odds']:.2f}",
            'Gerçek %': f"{vb['true_probability']*100:.1f}%",
            'İmplied %': f"{vb['implied_probability']*100:.1f}%",
            'EV %': f"{vb['expected_value']:.2f}%",
            'Value %': f"{vb['value_percentage']:.2f}%",
            'Kelly %': f"{vb['kelly_stake']:.2f}%",
            'Risk': vb['risk_level']
        })
    
    df = pd.DataFrame(df_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # En iyi value bet detay
    best_bet = value_bets[0]
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### 🏆 En İyi Value Bet")
        st.success(f"""
        **{best_bet['outcome']}** @ {best_bet['odds']:.2f}
        
        📊 **Analiz:**
        - Expected Value: **{best_bet['expected_value']:.2f}%**
        - Value Yüzdesi: **{best_bet['value_percentage']:.2f}%**
        - Gerçek Olasılık: {best_bet['true_probability']*100:.1f}%
        - İmplied Olasılık: {best_bet['implied_probability']*100:.1f}%
        
        💰 **Öneri:**
        {best_bet['recommendation']}
        
        ⚠️ **Risk Seviyesi:** {best_bet['risk_level']}
        """)
    
    with col2:
        # Value visualization
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=best_bet['expected_value'],
            title={'text': "Expected Value (%)"},
            gauge={
                'axis': {'range': [0, 30]},
                'bar': {'color': "darkgreen"},
                'steps': [
                    {'range': [0, 5], 'color': "lightgray"},
                    {'range': [5, 10], 'color': "lightyellow"},
                    {'range': [10, 15], 'color': "lightgreen"},
                    {'range': [15, 30], 'color': "green"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 5
                }
            }
        ))
        
        fig.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(fig, use_container_width=True)


def display_odds_comparison(true_probs: Dict[str, float], betting_odds):
    """Gerçek olasılık vs Bahisçi oranları karşılaştırma"""
    st.markdown("### 📊 Olasılık Karşılaştırması")
    
    # Tabs for different betting types
    tab1, tab2, tab3 = st.tabs(["🏆 Maç Sonucu", "🕐 İlk Yarı", "⚽ Alt/Üst"])
    
    with tab1:
        # Ana maç sonucu
        outcomes = ['Ev Sahibi', 'Beraberlik', 'Deplasman']
        true_percentages = [
            true_probs.get('home_win', 0) * 100,
            true_probs.get('draw', 0) * 100,
            true_probs.get('away_win', 0) * 100
        ]
        
        implied_probs = betting_odds.get_implied_probabilities()
        implied_percentages = [
            implied_probs['home_win'] * 100,
            implied_probs['draw'] * 100,
            implied_probs['away_win'] * 100
        ]
        
        _create_comparison_chart("Maç Sonucu - Model vs Bahisçi", outcomes, true_percentages, implied_percentages)
        
        # Margin bilgisi
        _display_margin_info(betting_odds, implied_percentages, true_percentages)
    
    with tab2:
        # İlk yarı karşılaştırması
        if betting_odds.ht_home_win > 1.0:  # İlk yarı oranları varsa
            ht_outcomes = ['1Y - Ev Sahibi', '1Y - Beraberlik', '1Y - Deplasman']
            ht_true_percentages = [
                true_probs.get('ht_home_win', 0) * 100,
                true_probs.get('ht_draw', 0) * 100,
                true_probs.get('ht_away_win', 0) * 100
            ]
            
            ht_implied_percentages = [
                (1/betting_odds.ht_home_win) * 100 if betting_odds.ht_home_win > 0 else 0,
                (1/betting_odds.ht_draw) * 100 if betting_odds.ht_draw > 0 else 0,
                (1/betting_odds.ht_away_win) * 100 if betting_odds.ht_away_win > 0 else 0
            ]
            
            _create_comparison_chart("İlk Yarı - Model vs Bahisçi", ht_outcomes, ht_true_percentages, ht_implied_percentages)
        else:
            st.info("İlk yarı oranları girilmemiş")
    
    with tab3:
        # Alt/Üst karşılaştırması
        if betting_odds.over_2_5 > 1.0:
            ou_outcomes = ['2.5 Üst', '2.5 Alt', '1.5 Üst', '1.5 Alt', '3.5 Üst', '3.5 Alt']
            ou_true_percentages = [
                true_probs.get('over_2_5', 0) * 100,
                true_probs.get('under_2_5', 0) * 100,
                true_probs.get('over_1_5', 0) * 100,
                true_probs.get('under_1_5', 0) * 100,
                true_probs.get('over_3_5', 0) * 100,
                true_probs.get('under_3_5', 0) * 100
            ]
            
            ou_implied_percentages = [
                (1/betting_odds.over_2_5) * 100 if betting_odds.over_2_5 > 0 else 0,
                (1/betting_odds.under_2_5) * 100 if betting_odds.under_2_5 > 0 else 0,
                (1/betting_odds.over_1_5) * 100 if betting_odds.over_1_5 > 0 else 0,
                (1/betting_odds.under_1_5) * 100 if betting_odds.under_1_5 > 0 else 0,
                (1/betting_odds.over_3_5) * 100 if betting_odds.over_3_5 > 0 else 0,
                (1/betting_odds.under_3_5) * 100 if betting_odds.under_3_5 > 0 else 0
            ]
            
            _create_comparison_chart("Alt/Üst - Model vs Bahisçi", ou_outcomes, ou_true_percentages, ou_implied_percentages)
        else:
            st.info("Alt/Üst oranları girilmemiş")


def _create_comparison_chart(title: str, outcomes: List[str], true_percentages: List[float], implied_percentages: List[float]):
    """Karşılaştırma grafiği oluştur"""
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Model Tahmini',
        x=outcomes,
        y=true_percentages,
        marker_color='rgb(55, 83, 109)',
        text=[f'{p:.1f}%' for p in true_percentages],
        textposition='auto'
    ))
    
    fig.add_trace(go.Bar(
        name='Bahisçi (Implied)',
        x=outcomes,
        y=implied_percentages,
        marker_color='rgb(26, 118, 255)',
        text=[f'{p:.1f}%' for p in implied_percentages],
        textposition='auto'
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title='',
        yaxis_title='Olasılık (%)',
        barmode='group',
        height=400,
        yaxis=dict(range=[0, max(max(true_percentages), max(implied_percentages)) * 1.1])
    )
    
    st.plotly_chart(fig, use_container_width=True)


def _display_margin_info(betting_odds, implied_percentages: List[float], true_percentages: List[float]):
    """Margin bilgilerini göster"""
    margin = betting_odds.get_margin()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Bahisçi Marjı", f"{margin:.2f}%", 
                 help="Bahisçinin kazancı (düşük = daha iyi)")
    
    with col2:
        total_implied = sum(implied_percentages)
        st.metric("Toplam Implied", f"{total_implied:.1f}%",
                 help="100%'den yüksekse bahisçi avantajlı")
    
    with col3:
        total_true = sum(true_percentages)
        st.metric("Model Toplam", f"{total_true:.1f}%",
                 help="Genelde ~100% olmalı")


def display_kelly_calculator(bankroll: float, value_bet: Dict):
    """Kelly Criterion hesaplayıcı ve gösterici"""
    st.markdown("### 💰 Kelly Criterion Hesaplayıcı")
    
    kelly_percentage = value_bet['kelly_stake']
    stake_amount = bankroll * (kelly_percentage / 100)
    
    # Farklı Kelly varyasyonları
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### Full Kelly")
        full_kelly = kelly_percentage / 0.25  # Varsayılan quarter kelly
        full_stake = bankroll * (full_kelly / 100)
        st.warning(f"""
        **%{full_kelly:.2f}** of bankroll
        
        **{full_stake:.2f} TL**
        
        ⚠️ Yüksek risk!
        """)
    
    with col2:
        st.markdown("#### Quarter Kelly (Önerilen)")
        st.success(f"""
        **%{kelly_percentage:.2f}** of bankroll
        
        **{stake_amount:.2f} TL**
        
        ✅ Dengeli risk
        """)
    
    with col3:
        st.markdown("#### Conservative")
        conservative = kelly_percentage * 0.5
        conservative_stake = bankroll * (conservative / 100)
        st.info(f"""
        **%{conservative:.2f}** of bankroll
        
        **{conservative_stake:.2f} TL**
        
        🛡️ Güvenli
        """)
    
    # Potansiyel kazanç
    st.markdown("#### 📈 Potansiyel Sonuçlar")
    
    odds = value_bet['odds']
    win_amount = stake_amount * (odds - 1)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.success(f"""
        **✅ Kazanırsa:**
        - Kazanç: +{win_amount:.2f} TL
        - Yeni Bankroll: {bankroll + win_amount:.2f} TL
        - ROI: {(win_amount/stake_amount)*100:.1f}%
        """)
    
    with col2:
        st.error(f"""
        **❌ Kaybederse:**
        - Kayıp: -{stake_amount:.2f} TL
        - Yeni Bankroll: {bankroll - stake_amount:.2f} TL
        - ROI: -100%
        """)


def display_arbitrage_opportunity(arb_data: Optional[Dict]):
    """Arbitrage fırsatını göster"""
    st.markdown("### 🔒 Arbitrage (Kesin Kazanç) Analizi")
    
    if not arb_data or not arb_data.get('is_arbitrage'):
        st.info("💡 Arbitrage fırsatı bulunamadı. Bu normaldir - bahisçiler genelde oranları koordine eder.")
        return
    
    st.success(f"🎉 **Arbitrage Fırsatı Bulundu!** Garanti kazanç: %{arb_data['profit_percentage']:.2f}")
    
    # Stake dağılımı
    st.markdown("#### 💵 Optimal Bahis Dağılımı (100 TL için)")
    
    stakes = arb_data['stakes']
    best_odds = arb_data['best_odds']
    
    col1, col2, col3 = st.columns(3)
    
    outcomes = [
        ('Ev Sahibi', 'home_win', col1),
        ('Beraberlik', 'draw', col2),
        ('Deplasman', 'away_win', col3)
    ]
    
    for outcome_name, key, col in outcomes:
        with col:
            stake = stakes[key]
            odds = best_odds[key]
            return_amount = stake * odds
            
            st.info(f"""
            **{outcome_name}**
            
            Bahis: {stake:.2f} TL
            Oran: {odds:.2f}
            Dönüş: {return_amount:.2f} TL
            """)
    
    # Grafik
    fig = go.Figure(data=[
        go.Bar(
            x=['Ev Sahibi', 'Beraberlik', 'Deplasman'],
            y=[stakes['home_win'], stakes['draw'], stakes['away_win']],
            marker_color=['#4CAF50', '#FFC107', '#F44336'],
            text=[f'{s:.2f} TL' for s in [stakes['home_win'], stakes['draw'], stakes['away_win']]],
            textposition='auto'
        )
    ])
    
    fig.update_layout(
        title='Bahis Dağılımı',
        xaxis_title='',
        yaxis_title='Bahis Miktarı (TL)',
        height=350
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.warning("""
    ⚠️ **Arbitrage Uyarıları:**
    - Farklı bahisçilerde hesap gerekir
    - Bahis limitleri olabilir
    - Oranlar hızlı değişebilir
    - Hesaplar kapatılabilir
    """)


def display_bankroll_tracker(manager):
    """Bankroll geçmişini göster"""
    if not manager.bet_history:
        st.info("Henüz bahis kaydı yok")
        return
    
    st.markdown("### 📊 Bankroll Geçmişi")
    
    # İstatistikler
    stats = manager.get_statistics()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Toplam Bahis", stats['total_bets'])
    
    with col2:
        st.metric("Kazanma Oranı", f"{stats['win_rate']:.1f}%",
                 delta=f"{stats['wins']}/{stats['total_bets']}")
    
    with col3:
        profit_color = "normal" if stats['total_profit'] >= 0 else "inverse"
        st.metric("Toplam Kar/Zarar", f"{stats['total_profit']:.2f} TL",
                 delta=f"ROI: {stats['roi']:.1f}%")
    
    with col4:
        st.metric("Güncel Bankroll", f"{stats['current_bankroll']:.2f} TL")
    
    # Bankroll grafiği
    bankroll_history = [manager.initial_bankroll] + [bet['bankroll_after'] for bet in manager.bet_history]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        y=bankroll_history,
        mode='lines+markers',
        name='Bankroll',
        line=dict(color='green' if stats['total_profit'] >= 0 else 'red', width=3),
        fill='tozeroy'
    ))
    
    fig.update_layout(
        title='Bankroll Gelişimi',
        xaxis_title='Bahis Sayısı',
        yaxis_title='Bankroll (TL)',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)


# Test
if __name__ == "__main__":
    print("✅ Betting görselleştirme modülü hazır")
