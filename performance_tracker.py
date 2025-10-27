"""
Performans Tracking Dashboard Modülü
Takım ve oyuncu performansını zamanla takip eder
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple


class PerformanceTracker:
    """Takım ve oyuncu performans takipçisi"""
    
    def __init__(self):
        self.colors = {
            'primary': '#667eea',
            'secondary': '#764ba2',
            'success': '#06d6a0',
            'danger': '#ef476f',
            'warning': '#ffd166',
            'info': '#118ab2'
        }
    
    def create_form_chart(self, 
                         team_name: str,
                         matches: List[Dict],
                         window_size: int = 5) -> go.Figure:
        """
        Takım formu grafiği (son N maç ortalaması)
        
        Args:
            team_name: Takım adı
            matches: [{'date': '2024-10-01', 'result': 'W', 'goals_for': 3, 'goals_against': 1}, ...]
            window_size: Form pencere boyutu
        """
        df = pd.DataFrame(matches)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Puan hesapla (G=3, B=1, M=0)
        df['points'] = df['result'].map({'W': 3, 'D': 1, 'L': 0})
        
        # Rolling average
        df['form'] = df['points'].rolling(window=window_size, min_periods=1).mean()
        df['goals_avg'] = df['goals_for'].rolling(window=window_size, min_periods=1).mean()
        df['conceded_avg'] = df['goals_against'].rolling(window=window_size, min_periods=1).mean()
        
        # Grafik oluştur
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Form Trendi (Puan Ortalaması)', 'Gol İstatistikleri'),
            vertical_spacing=0.15,
            row_heights=[0.6, 0.4]
        )
        
        # Form trendi
        fig.add_trace(
            go.Scatter(
                x=df['date'],
                y=df['form'],
                mode='lines+markers',
                name='Form (Avg)',
                line=dict(color=self.colors['primary'], width=3),
                fill='tozeroy',
                fillcolor='rgba(102, 126, 234, 0.2)',
                marker=dict(size=8)
            ),
            row=1, col=1
        )
        
        # İdeal form çizgisi
        fig.add_hline(
            y=2.0, line_dash="dash", line_color="green",
            annotation_text="İyi Form (2.0)", row=1, col=1
        )
        fig.add_hline(
            y=1.0, line_dash="dash", line_color="orange",
            annotation_text="Orta Form (1.0)", row=1, col=1
        )
        
        # Gol istatistikleri
        fig.add_trace(
            go.Scatter(
                x=df['date'],
                y=df['goals_avg'],
                mode='lines+markers',
                name='Atılan Gol (Avg)',
                line=dict(color=self.colors['success'], width=2),
                marker=dict(size=6)
            ),
            row=2, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=df['date'],
                y=df['conceded_avg'],
                mode='lines+markers',
                name='Yenilen Gol (Avg)',
                line=dict(color=self.colors['danger'], width=2),
                marker=dict(size=6)
            ),
            row=2, col=1
        )
        
        # Layout
        fig.update_xaxes(title_text="Tarih", row=2, col=1)
        fig.update_yaxes(title_text="Form Skoru", row=1, col=1, range=[0, 3])
        fig.update_yaxes(title_text="Gol Ortalaması", row=2, col=1)
        
        fig.update_layout(
            title=f"📈 {team_name} - Performans Trendi",
            height=600,
            showlegend=True,
            hovermode='x unified',
            template='plotly_dark'
        )
        
        return fig
    
    def create_comparison_chart(self,
                                team_stats: Dict[str, Dict]) -> go.Figure:
        """
        Takımlar arası karşılaştırma
        
        Args:
            team_stats: {'Team A': {'goals': 45, 'xG': 42, ...}, ...}
        """
        teams = list(team_stats.keys())
        categories = ['Goller', 'xG', 'Şutlar', 'Isabetli Şut', 'Pas %', 'Tehlikeli Atak']
        
        fig = go.Figure()
        
        for team in teams:
            stats = team_stats[team]
            values = [
                stats.get('goals', 0),
                stats.get('xG', 0),
                stats.get('shots', 0),
                stats.get('shots_on_target', 0),
                stats.get('pass_accuracy', 0),
                stats.get('dangerous_attacks', 0)
            ]
            
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                name=team,
                opacity=0.7
            ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, max([max(team_stats[t].values()) for t in teams]) * 1.1]
                )
            ),
            title="🔄 Takım Karşılaştırması (Radar)",
            showlegend=True,
            template='plotly_dark',
            height=500
        )
        
        return fig
    
    def create_player_progression(self,
                                 player_name: str,
                                 stats_over_time: List[Dict]) -> go.Figure:
        """
        Oyuncu gelişim grafiği
        
        Args:
            stats_over_time: [{'date': '2024-10', 'goals': 5, 'assists': 3, ...}, ...]
        """
        df = pd.DataFrame(stats_over_time)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Gol Trendi', 'Asist Trendi', 'Şut İsabeti %', 'Pas Başarısı %'),
            specs=[[{'secondary_y': False}, {'secondary_y': False}],
                   [{'secondary_y': False}, {'secondary_y': False}]]
        )
        
        # Goller
        fig.add_trace(
            go.Bar(x=df['date'], y=df['goals'], name='Goller',
                   marker_color=self.colors['success']),
            row=1, col=1
        )
        
        # Asistler
        fig.add_trace(
            go.Bar(x=df['date'], y=df['assists'], name='Asistler',
                   marker_color=self.colors['info']),
            row=1, col=2
        )
        
        # Şut isabeti
        fig.add_trace(
            go.Scatter(x=df['date'], y=df['shot_accuracy'], name='Şut %',
                      mode='lines+markers', line=dict(color=self.colors['warning'], width=2)),
            row=2, col=1
        )
        
        # Pas başarısı
        fig.add_trace(
            go.Scatter(x=df['date'], y=df['pass_accuracy'], name='Pas %',
                      mode='lines+markers', line=dict(color=self.colors['primary'], width=2)),
            row=2, col=2
        )
        
        fig.update_layout(
            title=f"👤 {player_name} - Performans Gelişimi",
            height=600,
            showlegend=False,
            template='plotly_dark'
        )
        
        return fig
    
    def create_streak_visualization(self,
                                   team_name: str,
                                   results: List[str]) -> go.Figure:
        """
        Seri (streak) görselleştirmesi
        
        Args:
            results: ['W', 'W', 'L', 'D', 'W', ...] son 20 maç
        """
        # Renk kodları
        color_map = {'W': self.colors['success'], 
                    'D': self.colors['warning'], 
                    'L': self.colors['danger']}
        
        colors = [color_map[r] for r in results]
        
        fig = go.Figure(data=[
            go.Bar(
                x=list(range(1, len(results) + 1)),
                y=[1] * len(results),
                marker_color=colors,
                text=results,
                textposition='inside',
                textfont=dict(size=14, color='white'),
                hovertext=[f"Maç {i+1}: {r}" for i, r in enumerate(results)],
                hoverinfo='text'
            )
        ])
        
        fig.update_layout(
            title=f"🎯 {team_name} - Son {len(results)} Maç Serisi",
            xaxis_title="Maç Sırası (Eski → Yeni)",
            yaxis_visible=False,
            height=200,
            showlegend=False,
            template='plotly_dark'
        )
        
        return fig
    
    def calculate_momentum_score(self, 
                                recent_results: List[str],
                                weights: Optional[List[float]] = None) -> float:
        """
        Momentum skoru hesapla (son maçlar daha ağırlıklı)
        
        Args:
            recent_results: ['W', 'L', 'D', ...]
            weights: Son maça daha fazla ağırlık
        """
        if not weights:
            # Exponential weights (son maç en ağırlıklı)
            weights = [2**i for i in range(len(recent_results))]
            weights = [w / sum(weights) for w in weights]  # Normalize
        
        points_map = {'W': 3, 'D': 1, 'L': 0}
        weighted_sum = sum(points_map[r] * w for r, w in zip(recent_results, weights))
        
        return weighted_sum * 100 / 3  # 0-100 skalasına normalize
    
    def create_momentum_gauge(self,
                             team_name: str,
                             momentum_score: float) -> go.Figure:
        """Momentum göstergesi (gauge chart)"""
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=momentum_score,
            title={'text': f"{team_name} Momentum"},
            delta={'reference': 50, 'increasing': {'color': self.colors['success']}},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': self.colors['primary']},
                'steps': [
                    {'range': [0, 30], 'color': self.colors['danger']},
                    {'range': [30, 70], 'color': self.colors['warning']},
                    {'range': [70, 100], 'color': self.colors['success']}
                ],
                'threshold': {
                    'line': {'color': "white", 'width': 4},
                    'thickness': 0.75,
                    'value': momentum_score
                }
            }
        ))
        
        fig.update_layout(
            height=300,
            template='plotly_dark'
        )
        
        return fig
    
    def generate_mock_team_data(self, 
                               team_name: str,
                               num_matches: int = 20) -> List[Dict]:
        """Mock takım verisi oluştur"""
        import random
        
        matches = []
        base_date = datetime.now() - timedelta(days=num_matches * 7)
        
        for i in range(num_matches):
            result = random.choice(['W', 'W', 'D', 'L'])  # Daha fazla galibiyet
            goals_for = random.randint(0, 4) if result == 'W' else random.randint(0, 2)
            goals_against = random.randint(0, 1) if result == 'W' else random.randint(1, 3)
            
            matches.append({
                'date': (base_date + timedelta(days=i*7)).strftime('%Y-%m-%d'),
                'result': result,
                'goals_for': goals_for,
                'goals_against': goals_against
            })
        
        return matches
    
    def generate_mock_player_stats(self,
                                  player_name: str,
                                  num_months: int = 6) -> List[Dict]:
        """Mock oyuncu verisi"""
        import random
        
        stats = []
        base_date = datetime.now() - timedelta(days=num_months * 30)
        
        for i in range(num_months):
            stats.append({
                'date': (base_date + timedelta(days=i*30)).strftime('%Y-%m'),
                'goals': random.randint(0, 8),
                'assists': random.randint(0, 6),
                'shot_accuracy': random.uniform(40, 85),
                'pass_accuracy': random.uniform(70, 95)
            })
        
        return stats
    
    def generate_mock_team_comparison(self) -> Dict[str, Dict]:
        """Mock karşılaştırma verisi"""
        import random
        
        teams = ['Galatasaray', 'Fenerbahçe', 'Beşiktaş', 'Trabzonspor']
        
        team_stats = {}
        for team in teams:
            team_stats[team] = {
                'goals': random.randint(35, 65),
                'xG': random.uniform(30, 60),
                'shots': random.randint(250, 400),
                'shots_on_target': random.randint(100, 180),
                'pass_accuracy': random.uniform(75, 88),
                'dangerous_attacks': random.randint(180, 280)
            }
        
        return team_stats
