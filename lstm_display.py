"""
LSTM Model Görselleştirme ve Analiz Fonksiyonları
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Optional


def display_lstm_prediction(prediction: Dict, home_team: str, away_team: str):
    """
    LSTM tahmin sonuçlarını görselleştirir
    
    Args:
        prediction: predict_match_with_lstm() sonucu
        home_team: Ev sahibi takım adı
        away_team: Deplasman takımı adı
    """
    st.markdown("### 🧠 LSTM Derin Öğrenme Tahmini")
    
    # Ana tahmin kartı
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        # Tahmin sonucu
        pred_map = {
            'home_win': f"🏆 {home_team} Kazanır",
            'away_win': f"🏆 {away_team} Kazanır",
            'draw': "🤝 Beraberlik"
        }
        
        result_text = pred_map.get(prediction['prediction'], 'Bilinmiyor')
        
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 20px; border-radius: 10px; text-align: center;'>
            <h2 style='color: white; margin: 0;'>{result_text}</h2>
            <p style='color: #e0e0e0; margin: 5px 0;'>Güven: {prediction['confidence']:.1f}%</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.metric(
            "Metod",
            prediction.get('method', 'LSTM'),
            help="Kullanılan tahmin algoritması"
        )
    
    with col3:
        # Trend göstergesi
        home_trend = prediction.get('home_team_trend', 'stable')
        away_trend = prediction.get('away_team_trend', 'stable')
        
        trend_icons = {
            'improving': '📈',
            'declining': '📉',
            'stable': '➡️'
        }
        
        st.metric(
            "Formlar",
            f"{trend_icons.get(home_trend, '➡️')} vs {trend_icons.get(away_trend, '➡️')}",
            help=f"{home_team}: {home_trend} | {away_team}: {away_trend}"
        )
    
    st.markdown("---")
    
    # Olasılık grafiği
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Olasılık çubuk grafiği
        fig = go.Figure()
        
        categories = [f'{home_team}\nKazanır', 'Beraberlik', f'{away_team}\nKazanır']
        probabilities = [
            prediction['home_win_probability'] * 100,
            prediction['draw_probability'] * 100,
            prediction['away_win_probability'] * 100
        ]
        colors = ['#4CAF50', '#FFC107', '#F44336']
        
        fig.add_trace(go.Bar(
            x=categories,
            y=probabilities,
            marker=dict(
                color=colors,
                line=dict(color='white', width=2)
            ),
            text=[f'{p:.1f}%' for p in probabilities],
            textposition='auto',
            textfont=dict(size=16, color='white', family='Arial Black'),
            hovertemplate='<b>%{x}</b><br>Olasılık: %{y:.1f}%<extra></extra>'
        ))
        
        fig.update_layout(
            title='Maç Sonucu Olasılıkları',
            xaxis_title='',
            yaxis_title='Olasılık (%)',
            yaxis=dict(range=[0, 100]),
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white')
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Olasılık pasta grafiği
        fig_pie = go.Figure(data=[go.Pie(
            labels=categories,
            values=probabilities,
            marker=dict(colors=colors),
            textinfo='label+percent',
            textposition='inside',
            hole=0.4
        )])
        
        fig_pie.update_layout(
            title='Dağılım',
            height=400,
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white')
        )
        
        st.plotly_chart(fig_pie, use_container_width=True)


def display_team_form_analysis(team_form: Dict, team_name: str):
    """
    Takım form analizi görselleştirmesi
    
    Args:
        team_form: LSTM model çıktısı (home_team_form veya away_team_form)
        team_name: Takım adı
    """
    st.markdown(f"#### 📊 {team_name} Form Analizi")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Kazanma",
            f"{team_form.get('win_probability', 0)*100:.1f}%",
            delta=None,
            help="Genel kazanma olasılığı"
        )
    
    with col2:
        st.metric(
            "Beraberlik",
            f"{team_form.get('draw_probability', 0)*100:.1f}%",
            delta=None
        )
    
    with col3:
        st.metric(
            "Kaybetme",
            f"{team_form.get('loss_probability', 0)*100:.1f}%",
            delta=None
        )
    
    with col4:
        trend = team_form.get('trend', 'stable')
        trend_text = {
            'improving': '📈 Yükseliş',
            'declining': '📉 Düşüş',
            'stable': '➡️ Sabit'
        }
        
        st.metric(
            "Trend",
            trend_text.get(trend, 'Bilinmiyor'),
            delta=None,
            help="Form trendi"
        )


def display_lstm_comparison(lstm_prediction: Dict, traditional_prediction: Dict,
                           home_team: str, away_team: str):
    """
    LSTM ve geleneksel model karşılaştırması
    
    Args:
        lstm_prediction: LSTM tahmin sonuçları
        traditional_prediction: Geleneksel model tahmin sonuçları
        home_team: Ev sahibi
        away_team: Deplasman
    """
    st.markdown("### 📊 Model Karşılaştırması: LSTM vs Geleneksel")
    
    # Karşılaştırma tablosu
    comparison_data = {
        'Metrik': ['Ev Sahibi Kazanır', 'Beraberlik', 'Deplasman Kazanır', 'Güven Skoru'],
        'LSTM Model': [
            f"{lstm_prediction.get('home_win_probability', 0)*100:.1f}%",
            f"{lstm_prediction.get('draw_probability', 0)*100:.1f}%",
            f"{lstm_prediction.get('away_win_probability', 0)*100:.1f}%",
            f"{lstm_prediction.get('confidence', 0):.1f}%"
        ],
        'Geleneksel Model': [
            f"{traditional_prediction.get('home_win_probability', 0)*100:.1f}%",
            f"{traditional_prediction.get('draw_probability', 0)*100:.1f}%",
            f"{traditional_prediction.get('away_win_probability', 0)*100:.1f}%",
            f"{traditional_prediction.get('confidence', 0):.1f}%"
        ]
    }
    
    df = pd.DataFrame(comparison_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Görsel karşılaştırma
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('LSTM Tahmini', 'Geleneksel Tahmin'),
        specs=[[{'type': 'bar'}, {'type': 'bar'}]]
    )
    
    categories = [home_team, 'Beraberlik', away_team]
    
    # LSTM
    lstm_probs = [
        lstm_prediction.get('home_win_probability', 0) * 100,
        lstm_prediction.get('draw_probability', 0) * 100,
        lstm_prediction.get('away_win_probability', 0) * 100
    ]
    
    # Geleneksel
    trad_probs = [
        traditional_prediction.get('home_win_probability', 0) * 100,
        traditional_prediction.get('draw_probability', 0) * 100,
        traditional_prediction.get('away_win_probability', 0) * 100
    ]
    
    colors = ['#4CAF50', '#FFC107', '#F44336']
    
    fig.add_trace(
        go.Bar(x=categories, y=lstm_probs, marker=dict(color=colors),
               text=[f'{p:.1f}%' for p in lstm_probs], textposition='auto'),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Bar(x=categories, y=trad_probs, marker=dict(color=colors),
               text=[f'{p:.1f}%' for p in trad_probs], textposition='auto'),
        row=1, col=2
    )
    
    fig.update_yaxes(title_text="Olasılık (%)", range=[0, 100], row=1, col=1)
    fig.update_yaxes(title_text="Olasılık (%)", range=[0, 100], row=1, col=2)
    
    fig.update_layout(
        height=400,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    st.plotly_chart(fig, use_container_width=True)


def display_training_history(history: Dict):
    """
    Model eğitim geçmişini görselleştirir
    
    Args:
        history: Keras model.fit() history
    """
    st.markdown("### 📈 Model Eğitim Performansı")
    
    if not history or 'loss' not in history:
        st.info("Eğitim geçmişi bulunamadı")
        return
    
    # Metrikler
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Son Loss", f"{history.get('final_loss', 0):.4f}")
    
    with col2:
        st.metric("Son Accuracy", f"{history.get('final_accuracy', 0)*100:.2f}%")
    
    with col3:
        st.metric("Val Loss", f"{history.get('final_val_loss', 0):.4f}")
    
    with col4:
        st.metric("Val Accuracy", f"{history.get('final_val_accuracy', 0)*100:.2f}%")
    
    # Grafik (eğer detaylı history varsa)
    if 'history' in history:
        hist = history['history']
        
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Loss', 'Accuracy')
        )
        
        epochs = list(range(1, len(hist['loss']) + 1))
        
        # Loss
        fig.add_trace(
            go.Scatter(x=epochs, y=hist['loss'], name='Train Loss', mode='lines+markers'),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=epochs, y=hist['val_loss'], name='Val Loss', mode='lines+markers'),
            row=1, col=1
        )
        
        # Accuracy
        fig.add_trace(
            go.Scatter(x=epochs, y=hist['accuracy'], name='Train Acc', mode='lines+markers'),
            row=1, col=2
        )
        fig.add_trace(
            go.Scatter(x=epochs, y=hist['val_accuracy'], name='Val Acc', mode='lines+markers'),
            row=1, col=2
        )
        
        fig.update_xaxes(title_text="Epoch", row=1, col=1)
        fig.update_xaxes(title_text="Epoch", row=1, col=2)
        fig.update_yaxes(title_text="Loss", row=1, col=1)
        fig.update_yaxes(title_text="Accuracy", row=1, col=2)
        
        fig.update_layout(height=400, showlegend=True)
        
        st.plotly_chart(fig, use_container_width=True)


# Test
if __name__ == "__main__":
    print("✅ LSTM Görselleştirme modülü hazır")
