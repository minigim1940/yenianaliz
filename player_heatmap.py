"""
Oyuncu Isı Haritası Modülü
Oyuncu pozisyon verileri ile saha üzerinde ısı haritası oluşturur
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import LinearSegmentedColormap
import seaborn as sns
from typing import List, Dict, Tuple, Optional
import io

class PlayerHeatmap:
    """Oyuncu isı haritası oluşturucu"""
    
    def __init__(self, pitch_length: int = 105, pitch_width: int = 68):
        """
        Args:
            pitch_length: Saha uzunluğu (metre, standart: 105)
            pitch_width: Saha genişliği (metre, standart: 68)
        """
        self.pitch_length = pitch_length
        self.pitch_width = pitch_width
        
    def create_pitch(self, ax=None, pitch_color='#195905', line_color='white'):
        """Futbol sahası çiz"""
        if ax is None:
            fig, ax = plt.subplots(figsize=(12, 8))
        else:
            fig = ax.figure
            
        ax.set_facecolor(pitch_color)
        
        # Saha çizgileri
        ax.plot([0, 0], [0, self.pitch_width], color=line_color, linewidth=2)
        ax.plot([0, self.pitch_length], [self.pitch_width, self.pitch_width], color=line_color, linewidth=2)
        ax.plot([self.pitch_length, self.pitch_length], [self.pitch_width, 0], color=line_color, linewidth=2)
        ax.plot([self.pitch_length, 0], [0, 0], color=line_color, linewidth=2)
        ax.plot([self.pitch_length/2, self.pitch_length/2], [0, self.pitch_width], color=line_color, linewidth=2)
        
        # Orta saha dairesi
        center_circle = plt.Circle((self.pitch_length/2, self.pitch_width/2), 9.15, 
                                   color=line_color, fill=False, linewidth=2)
        ax.add_patch(center_circle)
        
        # Orta nokta
        center_spot = plt.Circle((self.pitch_length/2, self.pitch_width/2), 0.5, 
                                color=line_color)
        ax.add_patch(center_spot)
        
        # Sol ceza sahası
        left_penalty = patches.Rectangle((0, (self.pitch_width-40.32)/2), 16.5, 40.32,
                                        linewidth=2, edgecolor=line_color, facecolor='none')
        ax.add_patch(left_penalty)
        
        # Sağ ceza sahası
        right_penalty = patches.Rectangle((self.pitch_length-16.5, (self.pitch_width-40.32)/2), 
                                         16.5, 40.32, linewidth=2, edgecolor=line_color, facecolor='none')
        ax.add_patch(right_penalty)
        
        # Sol kale sahası
        left_goal_area = patches.Rectangle((0, (self.pitch_width-18.32)/2), 5.5, 18.32,
                                          linewidth=2, edgecolor=line_color, facecolor='none')
        ax.add_patch(left_goal_area)
        
        # Sağ kale sahası
        right_goal_area = patches.Rectangle((self.pitch_length-5.5, (self.pitch_width-18.32)/2), 
                                           5.5, 18.32, linewidth=2, edgecolor=line_color, facecolor='none')
        ax.add_patch(right_goal_area)
        
        # Penaltı noktaları
        left_penalty_spot = plt.Circle((11, self.pitch_width/2), 0.5, color=line_color)
        right_penalty_spot = plt.Circle((self.pitch_length-11, self.pitch_width/2), 0.5, color=line_color)
        ax.add_patch(left_penalty_spot)
        ax.add_patch(right_penalty_spot)
        
        # Kaleler
        ax.plot([0, 0], [self.pitch_width/2 - 3.66, self.pitch_width/2 + 3.66], 
               color=line_color, linewidth=4)
        ax.plot([self.pitch_length, self.pitch_length], 
               [self.pitch_width/2 - 3.66, self.pitch_width/2 + 3.66], 
               color=line_color, linewidth=4)
        
        ax.set_xlim(-5, self.pitch_length + 5)
        ax.set_ylim(-5, self.pitch_width + 5)
        ax.axis('off')
        
        return fig, ax
    
    def generate_heatmap(self, positions: List[Tuple[float, float]], 
                        player_name: str = "Oyuncu",
                        team_name: str = "",
                        event_type: str = "Tüm Hareketler",
                        bins: int = 20,
                        alpha: float = 0.6) -> io.BytesIO:
        """
        Oyuncu pozisyonlarından ısı haritası oluştur
        
        Args:
            positions: [(x, y), ...] pozisyon listesi (0-105, 0-68 arası)
            player_name: Oyuncu adı
            team_name: Takım adı
            event_type: Hareket tipi (pas, şut, vs)
            bins: Işı haritası çözünürlüğü
            alpha: Şeffaflık (0-1)
            
        Returns:
            BytesIO: PNG görüntü buffer
        """
        fig, ax = self.create_pitch()
        
        if not positions or len(positions) == 0:
            ax.text(self.pitch_length/2, self.pitch_width/2, 
                   "Veri Bulunamadı", ha='center', va='center',
                   fontsize=20, color='white', weight='bold')
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', 
                       facecolor='#195905', edgecolor='none')
            plt.close()
            buf.seek(0)
            return buf
        
        # Pozisyonları numpy array'e çevir
        positions_array = np.array(positions)
        x = positions_array[:, 0]
        y = positions_array[:, 1]
        
        # Özel renk paleti (yeşil -> sarı -> kırmızı)
        colors = ['#00ff00', '#ffff00', '#ff6600', '#ff0000']
        n_bins = 100
        cmap = LinearSegmentedColormap.from_list('heatmap', colors, N=n_bins)
        
        # 2D histogram (ısı haritası)
        heatmap, xedges, yedges = np.histogram2d(x, y, bins=bins, 
                                                 range=[[0, self.pitch_length], 
                                                       [0, self.pitch_width]])
        
        # Gaussian blur ile yumuşatma
        from scipy.ndimage import gaussian_filter
        heatmap = gaussian_filter(heatmap, sigma=1.5)
        
        # Isı haritasını çiz
        extent = [0, self.pitch_length, 0, self.pitch_width]
        im = ax.imshow(heatmap.T, extent=extent, origin='lower', 
                      cmap=cmap, alpha=alpha, interpolation='bilinear')
        
        # Başlık ve bilgiler
        title = f"🔥 {player_name} - {event_type}"
        if team_name:
            title += f"\n{team_name}"
        ax.set_title(title, fontsize=16, weight='bold', color='white', pad=20)
        
        # Aktivite sayısı
        ax.text(self.pitch_length/2, -2, f"Toplam Aktivite: {len(positions)}", 
               ha='center', fontsize=12, color='white', weight='bold')
        
        # Renk çubuğu
        cbar = plt.colorbar(im, ax=ax, orientation='horizontal', 
                          pad=0.05, aspect=30, shrink=0.6)
        cbar.set_label('Aktivite Yoğunluğu', color='white', fontsize=10)
        cbar.ax.tick_params(colors='white', labelsize=8)
        
        # Buffer'a kaydet
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', 
                   facecolor='#195905', edgecolor='none')
        plt.close()
        buf.seek(0)
        
        return buf
    
    def generate_multi_heatmap(self, player_data: Dict[str, List[Tuple[float, float]]], 
                              team_name: str = "",
                              title: str = "Takım Isı Haritası") -> io.BytesIO:
        """
        Birden fazla oyuncu için birleşik ısı haritası
        
        Args:
            player_data: {player_name: [(x,y), ...], ...}
            team_name: Takım adı
            title: Grafik başlığı
        """
        fig, ax = self.create_pitch()
        
        all_positions = []
        for positions in player_data.values():
            all_positions.extend(positions)
        
        if not all_positions:
            ax.text(self.pitch_length/2, self.pitch_width/2, 
                   "Veri Bulunamadı", ha='center', va='center',
                   fontsize=20, color='white', weight='bold')
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', 
                       facecolor='#195905', edgecolor='none')
            plt.close()
            buf.seek(0)
            return buf
        
        positions_array = np.array(all_positions)
        x = positions_array[:, 0]
        y = positions_array[:, 1]
        
        colors = ['#00ff00', '#ffff00', '#ff6600', '#ff0000']
        cmap = LinearSegmentedColormap.from_list('heatmap', colors, N=100)
        
        heatmap, xedges, yedges = np.histogram2d(x, y, bins=25, 
                                                 range=[[0, self.pitch_length], 
                                                       [0, self.pitch_width]])
        
        from scipy.ndimage import gaussian_filter
        heatmap = gaussian_filter(heatmap, sigma=2)
        
        extent = [0, self.pitch_length, 0, self.pitch_width]
        im = ax.imshow(heatmap.T, extent=extent, origin='lower', 
                      cmap=cmap, alpha=0.6, interpolation='bilinear')
        
        full_title = f"🔥 {title}"
        if team_name:
            full_title += f" - {team_name}"
        ax.set_title(full_title, fontsize=16, weight='bold', color='white', pad=20)
        
        ax.text(self.pitch_length/2, -2, 
               f"{len(player_data)} Oyuncu | {len(all_positions)} Aktivite", 
               ha='center', fontsize=12, color='white', weight='bold')
        
        cbar = plt.colorbar(im, ax=ax, orientation='horizontal', 
                          pad=0.05, aspect=30, shrink=0.6)
        cbar.set_label('Aktivite Yoğunluğu', color='white', fontsize=10)
        cbar.ax.tick_params(colors='white', labelsize=8)
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', 
                   facecolor='#195905', edgecolor='none')
        plt.close()
        buf.seek(0)
        
        return buf
    
    def generate_mock_positions(self, player_position: str = "Forward", 
                               num_points: int = 50) -> List[Tuple[float, float]]:
        """
        Test için mock pozisyon verisi oluştur
        
        Args:
            player_position: Oyuncu pozisyonu (Forward, Midfielder, Defender, Goalkeeper)
            num_points: Oluşturulacak nokta sayısı
        """
        positions = []
        
        if player_position == "Forward":
            # Forvet: Rakip yarı sahada yoğun
            for _ in range(num_points):
                x = np.random.normal(75, 15)  # Ortalama 75m, std 15m
                y = np.random.normal(self.pitch_width/2, 15)
                x = np.clip(x, 52.5, self.pitch_length)
                y = np.clip(y, 0, self.pitch_width)
                positions.append((x, y))
                
        elif player_position == "Midfielder":
            # Orta saha: Her yerde
            for _ in range(num_points):
                x = np.random.normal(self.pitch_length/2, 20)
                y = np.random.normal(self.pitch_width/2, 15)
                x = np.clip(x, 0, self.pitch_length)
                y = np.clip(y, 0, self.pitch_width)
                positions.append((x, y))
                
        elif player_position == "Defender":
            # Defans: Kendi yarı sahada
            for _ in range(num_points):
                x = np.random.normal(25, 15)
                y = np.random.normal(self.pitch_width/2, 15)
                x = np.clip(x, 0, 52.5)
                y = np.clip(y, 0, self.pitch_width)
                positions.append((x, y))
                
        else:  # Goalkeeper
            # Kaleci: Kale önü
            for _ in range(num_points):
                x = np.random.normal(5, 3)
                y = np.random.normal(self.pitch_width/2, 8)
                x = np.clip(x, 0, 16.5)
                y = np.clip(y, 10, self.pitch_width-10)
                positions.append((x, y))
        
        return positions


def extract_positions_from_match_events(match_events: List[Dict]) -> Dict[str, List[Tuple[float, float]]]:
    """
    Maç event verilerinden oyuncu pozisyonlarını çıkar
    
    Args:
        match_events: API'den gelen event listesi
        
    Returns:
        {player_name: [(x, y), ...]}
    """
    player_positions = {}
    
    for event in match_events:
        player_name = event.get('player', {}).get('name')
        if not player_name:
            continue
            
        # Pozisyon bilgisi varsa al
        x = event.get('coordinates', {}).get('x')
        y = event.get('coordinates', {}).get('y')
        
        if x is not None and y is not None:
            if player_name not in player_positions:
                player_positions[player_name] = []
            player_positions[player_name].append((float(x), float(y)))
    
    return player_positions


def filter_positions_by_event_type(match_events: List[Dict], 
                                   event_types: List[str]) -> Dict[str, List[Tuple[float, float]]]:
    """
    Belirli event tiplerini filtrele (şut, pas, vs)
    
    Args:
        match_events: API event listesi
        event_types: ['Shot', 'Pass', 'Dribble', vs]
    """
    player_positions = {}
    
    for event in match_events:
        event_type = event.get('type', {}).get('name')
        if event_type not in event_types:
            continue
            
        player_name = event.get('player', {}).get('name')
        if not player_name:
            continue
            
        x = event.get('coordinates', {}).get('x')
        y = event.get('coordinates', {}).get('y')
        
        if x is not None and y is not None:
            if player_name not in player_positions:
                player_positions[player_name] = []
            player_positions[player_name].append((float(x), float(y)))
    
    return player_positions
