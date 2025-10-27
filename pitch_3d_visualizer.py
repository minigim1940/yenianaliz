"""
3D Saha Görselleştirme Modülü
Plotly ile interaktif 3D futbol sahası ve pas ağları
"""

import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from typing import List, Dict, Tuple, Optional
import pandas as pd


class Pitch3DVisualizer:
    """3D Futbol Sahası Görselleştirici"""
    
    def __init__(self, pitch_length: int = 105, pitch_width: int = 68):
        """
        Args:
            pitch_length: Saha uzunluğu (metre)
            pitch_width: Saha genişliği (metre)
        """
        self.pitch_length = pitch_length
        self.pitch_width = pitch_width
        self.pitch_color = '#195905'
        self.line_color = 'white'
        
    def create_pitch_surface(self) -> go.Surface:
        """Saha zemini oluştur"""
        x = np.linspace(0, self.pitch_length, 50)
        y = np.linspace(0, self.pitch_width, 30)
        X, Y = np.meshgrid(x, y)
        Z = np.zeros_like(X)  # Düz zemin
        
        surface = go.Surface(
            x=X, y=Y, z=Z,
            colorscale=[[0, self.pitch_color], [1, self.pitch_color]],
            showscale=False,
            opacity=0.9,
            name='Saha'
        )
        
        return surface
    
    def create_pitch_lines(self) -> List[go.Scatter3d]:
        """Saha çizgilerini oluştur"""
        lines = []
        z_height = 0.1  # Çizgileri biraz yükselt
        
        # Dış çizgiler
        outer_lines = [
            ([0, self.pitch_length], [0, 0], [z_height, z_height]),  # Alt
            ([0, self.pitch_length], [self.pitch_width, self.pitch_width], [z_height, z_height]),  # Üst
            ([0, 0], [0, self.pitch_width], [z_height, z_height]),  # Sol
            ([self.pitch_length, self.pitch_length], [0, self.pitch_width], [z_height, z_height])  # Sağ
        ]
        
        for x, y, z in outer_lines:
            lines.append(go.Scatter3d(
                x=x, y=y, z=z,
                mode='lines',
                line=dict(color=self.line_color, width=4),
                showlegend=False,
                hoverinfo='skip'
            ))
        
        # Orta saha çizgisi
        lines.append(go.Scatter3d(
            x=[self.pitch_length/2, self.pitch_length/2],
            y=[0, self.pitch_width],
            z=[z_height, z_height],
            mode='lines',
            line=dict(color=self.line_color, width=4),
            showlegend=False,
            hoverinfo='skip'
        ))
        
        # Orta saha dairesi
        theta = np.linspace(0, 2*np.pi, 50)
        center_circle_x = self.pitch_length/2 + 9.15 * np.cos(theta)
        center_circle_y = self.pitch_width/2 + 9.15 * np.sin(theta)
        center_circle_z = np.full_like(theta, z_height)
        
        lines.append(go.Scatter3d(
            x=center_circle_x, y=center_circle_y, z=center_circle_z,
            mode='lines',
            line=dict(color=self.line_color, width=3),
            showlegend=False,
            hoverinfo='skip'
        ))
        
        # Ceza sahaları
        penalty_areas = [
            # Sol ceza sahası
            ([0, 16.5], [(self.pitch_width-40.32)/2, (self.pitch_width-40.32)/2]),
            ([16.5, 16.5], [(self.pitch_width-40.32)/2, (self.pitch_width+40.32)/2]),
            ([16.5, 0], [(self.pitch_width+40.32)/2, (self.pitch_width+40.32)/2]),
            # Sağ ceza sahası
            ([self.pitch_length, self.pitch_length-16.5], [(self.pitch_width-40.32)/2, (self.pitch_width-40.32)/2]),
            ([self.pitch_length-16.5, self.pitch_length-16.5], [(self.pitch_width-40.32)/2, (self.pitch_width+40.32)/2]),
            ([self.pitch_length-16.5, self.pitch_length], [(self.pitch_width+40.32)/2, (self.pitch_width+40.32)/2])
        ]
        
        for x, y in penalty_areas:
            lines.append(go.Scatter3d(
                x=x, y=y, z=[z_height, z_height],
                mode='lines',
                line=dict(color=self.line_color, width=3),
                showlegend=False,
                hoverinfo='skip'
            ))
        
        return lines
    
    def create_pass_network(self, 
                           passes: List[Dict],
                           player_positions: Dict[str, Tuple[float, float]],
                           team_color: str = '#FF6B6B') -> List:
        """
        Pas ağı oluştur
        
        Args:
            passes: [{'from': 'Player1', 'to': 'Player2', 'count': 5}, ...]
            player_positions: {'Player1': (x, y), 'Player2': (x, y), ...}
            team_color: Takım rengi
        """
        traces = []
        
        # Pasları çiz
        for pass_data in passes:
            from_player = pass_data.get('from')
            to_player = pass_data.get('to')
            count = pass_data.get('count', 1)
            
            if from_player in player_positions and to_player in player_positions:
                from_pos = player_positions[from_player]
                to_pos = player_positions[to_player]
                
                # Pas çizgisi kalınlığı pas sayısına bağlı
                line_width = min(count * 0.5 + 1, 8)
                
                # 3D eğri oluştur (ark şeklinde)
                x_coords = [from_pos[0], (from_pos[0] + to_pos[0])/2, to_pos[0]]
                y_coords = [from_pos[1], (from_pos[1] + to_pos[1])/2, to_pos[1]]
                z_coords = [0.2, count * 0.3 + 1, 0.2]  # Ortada yükselt
                
                traces.append(go.Scatter3d(
                    x=x_coords, y=y_coords, z=z_coords,
                    mode='lines',
                    line=dict(color=team_color, width=line_width),
                    opacity=0.7,
                    showlegend=False,
                    hovertext=f"{from_player} → {to_player}<br>{count} pas",
                    hoverinfo='text'
                ))
        
        # Oyuncu pozisyonlarını çiz
        player_names = list(player_positions.keys())
        player_x = [player_positions[p][0] for p in player_names]
        player_y = [player_positions[p][1] for p in player_names]
        player_z = [0.5] * len(player_names)
        
        traces.append(go.Scatter3d(
            x=player_x, y=player_y, z=player_z,
            mode='markers+text',
            marker=dict(
                size=10,
                color=team_color,
                line=dict(color='white', width=2),
                symbol='circle'
            ),
            text=player_names,
            textposition='top center',
            textfont=dict(size=10, color='white'),
            showlegend=False,
            hovertext=player_names,
            hoverinfo='text'
        ))
        
        return traces
    
    def create_attack_zones(self, 
                           attack_data: List[Tuple[float, float, int]],
                           team_color: str = '#4ECDC4') -> go.Scatter3d:
        """
        Hücum bölgeleri oluştur
        
        Args:
            attack_data: [(x, y, intensity), ...] intensity: 1-10
            team_color: Renk
        """
        x_coords = [d[0] for d in attack_data]
        y_coords = [d[1] for d in attack_data]
        intensities = [d[2] for d in attack_data]
        z_coords = [i * 0.5 for i in intensities]  # Yoğunluk = yükseklik
        
        trace = go.Scatter3d(
            x=x_coords, y=y_coords, z=z_coords,
            mode='markers',
            marker=dict(
                size=intensities,
                color=intensities,
                colorscale='YlOrRd',
                showscale=True,
                colorbar=dict(title='Yoğunluk'),
                line=dict(color='white', width=1)
            ),
            text=[f"Yoğunluk: {i}" for i in intensities],
            hoverinfo='text',
            name='Hücum Bölgeleri'
        )
        
        return trace
    
    def create_shot_map_3d(self, 
                          shots: List[Dict],
                          team_color: str = '#FFD93D') -> List:
        """
        3D şut haritası
        
        Args:
            shots: [{'x': 90, 'y': 30, 'xG': 0.3, 'goal': True}, ...]
        """
        traces = []
        
        goals = [s for s in shots if s.get('goal', False)]
        misses = [s for s in shots if not s.get('goal', False)]
        
        # Goller
        if goals:
            traces.append(go.Scatter3d(
                x=[s['x'] for s in goals],
                y=[s['y'] for s in goals],
                z=[s.get('xG', 0.5) * 10 for s in goals],  # xG * 10 = yükseklik
                mode='markers',
                marker=dict(
                    size=[s.get('xG', 0.5) * 20 for s in goals],
                    color='green',
                    symbol='diamond',
                    line=dict(color='white', width=2)
                ),
                text=[f"⚽ GOL<br>xG: {s.get('xG', 0):.2f}" for s in goals],
                hoverinfo='text',
                name='Goller'
            ))
        
        # Kaçanlar
        if misses:
            traces.append(go.Scatter3d(
                x=[s['x'] for s in misses],
                y=[s['y'] for s in misses],
                z=[s.get('xG', 0.5) * 10 for s in misses],
                mode='markers',
                marker=dict(
                    size=[s.get('xG', 0.5) * 20 for s in misses],
                    color='red',
                    symbol='x',
                    line=dict(color='white', width=1)
                ),
                text=[f"❌ Kaçan<br>xG: {s.get('xG', 0):.2f}" for s in misses],
                hoverinfo='text',
                name='Kaçan Şutlar'
            ))
        
        return traces
    
    def create_full_visualization(self,
                                 passes: Optional[List[Dict]] = None,
                                 player_positions: Optional[Dict] = None,
                                 attack_zones: Optional[List[Tuple]] = None,
                                 shots: Optional[List[Dict]] = None,
                                 title: str = "3D Saha Analizi") -> go.Figure:
        """
        Tüm elementleri birleştir
        """
        fig = go.Figure()
        
        # Saha zemini
        fig.add_trace(self.create_pitch_surface())
        
        # Saha çizgileri
        for line in self.create_pitch_lines():
            fig.add_trace(line)
        
        # Pas ağı
        if passes and player_positions:
            for trace in self.create_pass_network(passes, player_positions):
                fig.add_trace(trace)
        
        # Hücum bölgeleri
        if attack_zones:
            fig.add_trace(self.create_attack_zones(attack_zones))
        
        # Şut haritası
        if shots:
            for trace in self.create_shot_map_3d(shots):
                fig.add_trace(trace)
        
        # Layout
        fig.update_layout(
            title=dict(
                text=title,
                font=dict(size=24, color='white'),
                x=0.5,
                xanchor='center'
            ),
            scene=dict(
                xaxis=dict(
                    title='Uzunluk (m)',
                    backgroundcolor='rgb(30, 30, 30)',
                    gridcolor='gray',
                    showbackground=True,
                    range=[0, self.pitch_length]
                ),
                yaxis=dict(
                    title='Genişlik (m)',
                    backgroundcolor='rgb(30, 30, 30)',
                    gridcolor='gray',
                    showbackground=True,
                    range=[0, self.pitch_width]
                ),
                zaxis=dict(
                    title='Yükseklik',
                    backgroundcolor='rgb(30, 30, 30)',
                    gridcolor='gray',
                    showbackground=True,
                    range=[0, 10]
                ),
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.2),
                    center=dict(x=0, y=0, z=-0.1)
                ),
                aspectmode='manual',
                aspectratio=dict(x=2, y=1.3, z=0.3)
            ),
            paper_bgcolor='rgb(20, 20, 20)',
            plot_bgcolor='rgb(20, 20, 20)',
            font=dict(color='white'),
            showlegend=True,
            legend=dict(
                x=0.02,
                y=0.98,
                bgcolor='rgba(0,0,0,0.5)',
                bordercolor='white',
                borderwidth=1
            ),
            height=700
        )
        
        return fig
    
    def generate_mock_pass_network(self, num_players: int = 11) -> Tuple[List[Dict], Dict]:
        """Mock pas ağı verisi oluştur"""
        import random
        
        # Oyuncu isimleri
        player_names = [f"Oyuncu {i+1}" for i in range(num_players)]
        
        # Pozisyonlar (4-3-3 dizilimi)
        positions = {}
        
        # Kaleci
        positions[player_names[0]] = (10, self.pitch_width/2)
        
        # Defans (4)
        for i in range(1, 5):
            positions[player_names[i]] = (25, 10 + i * 15)
        
        # Orta saha (3)
        for i in range(5, 8):
            positions[player_names[i]] = (50, 15 + (i-5) * 20)
        
        # Forvet (3)
        for i in range(8, 11):
            positions[player_names[i]] = (80, 15 + (i-8) * 20)
        
        # Paslar (rastgele)
        passes = []
        for _ in range(20):
            from_player = random.choice(player_names)
            to_player = random.choice([p for p in player_names if p != from_player])
            count = random.randint(1, 10)
            passes.append({'from': from_player, 'to': to_player, 'count': count})
        
        return passes, positions
    
    def generate_mock_attack_zones(self, num_zones: int = 30) -> List[Tuple]:
        """Mock hücum bölgeleri"""
        import random
        
        zones = []
        for _ in range(num_zones):
            x = random.uniform(self.pitch_length * 0.6, self.pitch_length * 0.95)
            y = random.uniform(5, self.pitch_width - 5)
            intensity = random.randint(3, 10)
            zones.append((x, y, intensity))
        
        return zones
    
    def generate_mock_shots(self, num_shots: int = 15) -> List[Dict]:
        """Mock şut verisi"""
        import random
        
        shots = []
        for _ in range(num_shots):
            x = random.uniform(self.pitch_length * 0.7, self.pitch_length * 0.95)
            y = random.uniform(15, self.pitch_width - 15)
            xG = random.uniform(0.05, 0.8)
            goal = random.random() < xG  # xG'ye göre gol olma ihtimali
            
            shots.append({'x': x, 'y': y, 'xG': xG, 'goal': goal})
        
        return shots
