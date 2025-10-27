# -*- coding: utf-8 -*-
"""
xG (Expected Goals) Calculator Module
=====================================
Pozisyon bazlı beklenen gol hesaplama motoru
"""

import math
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import json

class xGCalculator:
    """Beklenen Gol (Expected Goals) Hesaplama Motoru"""
    
    def __init__(self):
        """xG hesaplayıcıyı başlat"""
        self.position_weights = self._initialize_position_weights()
        self.situation_multipliers = self._initialize_situation_multipliers()
        
    def _initialize_position_weights(self) -> Dict[str, float]:
        """Pozisyon bazlı temel xG değerleri"""
        return {
            # Ceza sahası içi bölgeler
            'center_6yard': 0.85,      # 6 pas içi merkez (çok yüksek)
            'left_6yard': 0.75,        # 6 pas içi sol
            'right_6yard': 0.75,       # 6 pas içi sağ
            'center_penalty': 0.45,    # Penaltı noktası civarı
            'left_penalty': 0.35,      # Ceza sahası sol
            'right_penalty': 0.35,     # Ceza sahası sağ
            'deep_left': 0.15,         # Arka yan sol
            'deep_right': 0.15,        # Arka yan sağ
            
            # Ceza sahası dışı
            'edge_box': 0.08,          # Ceza sahası çizgisi
            'long_range': 0.03,        # Uzak mesafe
            'very_long': 0.01,         # Çok uzak
            
            # Özel pozisyonlar
            'penalty_kick': 0.76,      # Penaltı vuruşu
            'header_close': 0.35,      # Yakın kafa vuruşu
            'header_far': 0.12,        # Uzak kafa vuruşu
        }
    
    def _initialize_situation_multipliers(self) -> Dict[str, float]:
        """Durum bazlı çarpanlar"""
        return {
            'open_play': 1.0,          # Normal oyun
            'counter_attack': 1.3,     # Kontra atak
            'set_piece': 0.85,         # Duran top
            'corner': 0.12,            # Korner
            'free_kick_direct': 0.05,  # Direkt serbest vuruş
            'penalty': 0.76,           # Penaltı
            'fast_break': 1.4,         # Hızlı atak
            'one_on_one': 1.8,         # 1v1 kaleci
            'rebound': 1.2,            # Sekme topta
            'cross': 0.8,              # Orta sonrası
        }
    
    def calculate_shot_xg(self, 
                         distance: float,
                         angle: float,
                         situation: str = 'open_play',
                         is_header: bool = False,
                         defender_count: int = 0,
                         goalkeeper_position: str = 'normal',
                         foot: str = 'strong',
                         body_part: str = 'foot') -> Dict[str, Any]:
        """
        Tek bir şut için xG hesapla
        
        Args:
            distance: Kaleye mesafe (metre)
            angle: Şut açısı (derece, 0=düz, 90=yan)
            situation: Oyun durumu
            is_header: Kafa vuruşu mu
            defender_count: Şutçu ile kale arası defans sayısı
            goalkeeper_position: Kaleci pozisyonu
            foot: Kullanılan ayak (strong/weak)
            body_part: Vücut bölgesi (foot/header/other)
            
        Returns:
            xG değeri ve detaylar
        """
        # Temel xG hesaplama
        base_xg = self._calculate_base_xg(distance, angle)
        
        # Durum çarpanı
        situation_mult = self.situation_multipliers.get(situation, 1.0)
        
        # Kafa vuruşu çarpanı
        header_mult = 0.7 if is_header else 1.0
        
        # Defans baskısı azaltıcı
        defense_mult = 1.0 - (defender_count * 0.15)
        defense_mult = max(defense_mult, 0.3)  # Minimum %30
        
        # Kaleci pozisyon çarpanı
        gk_multipliers = {
            'out': 1.5,      # Kaleci oyun dışı
            'bad': 1.3,      # Kötü pozisyon
            'normal': 1.0,   # Normal
            'good': 0.8,     # İyi pozisyon
        }
        gk_mult = gk_multipliers.get(goalkeeper_position, 1.0)
        
        # Ayak çarpanı
        foot_mult = 1.0 if foot == 'strong' else 0.75
        
        # Final xG hesaplama
        final_xg = (base_xg * 
                   situation_mult * 
                   header_mult * 
                   defense_mult * 
                   gk_mult * 
                   foot_mult)
        
        # xG değerini 0-1 arasında sınırla
        final_xg = max(0.01, min(0.99, final_xg))
        
        return {
            'xg_value': round(final_xg, 3),
            'base_xg': round(base_xg, 3),
            'multipliers': {
                'situation': situation_mult,
                'header': header_mult,
                'defense': defense_mult,
                'goalkeeper': gk_mult,
                'foot': foot_mult
            },
            'factors': {
                'distance': distance,
                'angle': angle,
                'situation': situation,
                'is_header': is_header,
                'defenders': defender_count
            }
        }
    
    def _calculate_base_xg(self, distance: float, angle: float) -> float:
        """Mesafe ve açıya göre temel xG hesapla"""
        # Mesafe faktörü (logaritmik azalma)
        if distance <= 6:
            distance_factor = 0.8
        elif distance <= 11:
            distance_factor = 0.5
        elif distance <= 16.5:
            distance_factor = 0.25
        elif distance <= 25:
            distance_factor = 0.1
        else:
            distance_factor = 0.03
        
        # Açı faktörü (0° = düz önünde, 90° = yan taraf)
        angle_rad = math.radians(angle)
        angle_factor = math.cos(angle_rad) ** 2
        
        # Kombine et
        base_xg = distance_factor * angle_factor
        
        return base_xg
    
    def calculate_match_xg(self, shots: List[Dict]) -> Dict[str, Any]:
        """
        Bir maç için toplam xG hesapla
        
        Args:
            shots: Şut listesi (her biri calculate_shot_xg parametrelerini içermeli)
            
        Returns:
            Maç xG özeti
        """
        total_xg = 0.0
        shot_xgs = []
        
        for shot in shots:
            xg_result = self.calculate_shot_xg(**shot)
            shot_xgs.append(xg_result)
            total_xg += xg_result['xg_value']
        
        return {
            'total_xg': round(total_xg, 2),
            'shot_count': len(shots),
            'avg_xg_per_shot': round(total_xg / len(shots), 3) if shots else 0,
            'best_chance': max(shot_xgs, key=lambda x: x['xg_value']) if shot_xgs else None,
            'shots': shot_xgs
        }
    
    def calculate_team_xg(self, 
                         team_stats: Dict[str, Any],
                         opponent_stats: Dict[str, Any]) -> Dict[str, Any]:
        """
        Takım istatistiklerinden tahmini xG hesapla
        
        Args:
            team_stats: Takım istatistikleri
            opponent_stats: Rakip istatistikleri
            
        Returns:
            Tahmin edilen xG değeri
        """
        # Şut istatistiklerinden xG tahmini
        shots_total = team_stats.get('shots_total', 0)
        shots_on = team_stats.get('shots_on_target', 0)
        shots_inside = team_stats.get('shots_inside_box', 0)
        shots_outside = team_stats.get('shots_outside_box', 0)
        
        # Temel xG hesaplama
        # Ceza sahası içi şutlar için ortalama xG: 0.3
        # Ceza sahası dışı şutlar için ortalama xG: 0.05
        xg_inside = shots_inside * 0.3
        xg_outside = shots_outside * 0.05
        
        # İskala içi oran çarpanı
        if shots_total > 0:
            on_target_ratio = shots_on / shots_total
            accuracy_mult = 0.8 + (on_target_ratio * 0.4)  # 0.8 - 1.2 arası
        else:
            accuracy_mult = 1.0
        
        # Rakip savunma kalitesi
        opponent_def_rating = opponent_stats.get('defense_rating', 50)
        defense_mult = 1.0 - ((opponent_def_rating - 50) / 200)  # ±0.25
        
        # Ev sahibi avantajı
        is_home = team_stats.get('is_home', False)
        home_mult = 1.1 if is_home else 1.0
        
        # Final xG
        estimated_xg = (xg_inside + xg_outside) * accuracy_mult * defense_mult * home_mult
        
        return {
            'estimated_xg': round(estimated_xg, 2),
            'shots_breakdown': {
                'total': shots_total,
                'on_target': shots_on,
                'inside_box': shots_inside,
                'outside_box': shots_outside
            },
            'multipliers': {
                'accuracy': round(accuracy_mult, 2),
                'opponent_defense': round(defense_mult, 2),
                'home_advantage': home_mult
            }
        }
    
    def compare_xg_vs_goals(self, xg: float, actual_goals: int) -> Dict[str, Any]:
        """
        xG ile gerçek gol sayısını karşılaştır
        
        Args:
            xg: Beklenen gol
            actual_goals: Gerçekleşen gol
            
        Returns:
            Karşılaştırma analizi
        """
        difference = actual_goals - xg
        
        # Performans değerlendirmesi
        if difference > 1.5:
            performance = "Olağanüstü Bitiricilik"
            rating = "excellent"
        elif difference > 0.5:
            performance = "İyi Bitiricilik"
            rating = "good"
        elif difference > -0.5:
            performance = "Normal Bitiricilik"
            rating = "average"
        elif difference > -1.5:
            performance = "Zayıf Bitiricilik"
            rating = "poor"
        else:
            performance = "Çok Zayıf Bitiricilik"
            rating = "very_poor"
        
        # Şans faktörü
        luck_factor = abs(difference)
        if luck_factor > 2:
            luck_desc = "Çok Şanslı/Şanssız" if difference > 0 else "Çok Şanssız"
        elif luck_factor > 1:
            luck_desc = "Şanslı/Şanssız" if difference > 0 else "Şanssız"
        else:
            luck_desc = "Normal"
        
        return {
            'xg': round(xg, 2),
            'actual_goals': actual_goals,
            'difference': round(difference, 2),
            'performance': performance,
            'rating': rating,
            'luck': luck_desc,
            'efficiency': round((actual_goals / xg * 100), 1) if xg > 0 else 0
        }
    
    def get_position_zone(self, x: float, y: float, 
                         field_length: float = 105, 
                         field_width: float = 68) -> str:
        """
        Saha koordinatlarından pozisyon bölgesi belirle
        
        Args:
            x: X koordinatı (0 = savunma, field_length = hücum)
            y: Y koordinatı (0 = sol, field_width = sağ)
            field_length: Saha uzunluğu (metre)
            field_width: Saha genişliği (metre)
            
        Returns:
            Bölge adı
        """
        # Kaleye mesafe (x ekseni)
        distance_to_goal = field_length - x
        
        # Merkeze mesafe (y ekseni)
        center_y = field_width / 2
        distance_to_center = abs(y - center_y)
        
        # 6 pas sahası: x > 99.5m (kaleye 5.5m), merkeze 9.15m yakın
        if distance_to_goal <= 5.5 and distance_to_center <= 9.15:
            if distance_to_center <= 3:
                return 'center_6yard'
            elif y < center_y:
                return 'left_6yard'
            else:
                return 'right_6yard'
        
        # Ceza sahası: x > 88.5m (kaleye 16.5m), merkeze 20.15m yakın
        if distance_to_goal <= 16.5 and distance_to_center <= 20.15:
            if distance_to_center <= 7:
                return 'center_penalty'
            elif y < center_y:
                return 'left_penalty'
            else:
                return 'right_penalty'
        
        # Ceza sahası kenarı
        if distance_to_goal <= 18:
            return 'edge_box'
        
        # Uzak mesafe
        if distance_to_goal <= 30:
            return 'long_range'
        
        return 'very_long'


class LivexGTracker:
    """Canlı maç xG takibi"""
    
    def __init__(self):
        self.calculator = xGCalculator()
        self.match_data = {
            'home': {'xg': 0.0, 'shots': [], 'goals': 0},
            'away': {'xg': 0.0, 'shots': [], 'goals': 0}
        }
        self.timeline = []
    
    def add_shot(self, team: str, shot_data: Dict, minute: int, is_goal: bool = False):
        """Canlı maçta şut ekle"""
        xg_result = self.calculator.calculate_shot_xg(**shot_data)
        
        self.match_data[team]['shots'].append(xg_result)
        self.match_data[team]['xg'] += xg_result['xg_value']
        
        if is_goal:
            self.match_data[team]['goals'] += 1
        
        # Zaman çizelgesine ekle
        self.timeline.append({
            'minute': minute,
            'team': team,
            'xg': xg_result['xg_value'],
            'is_goal': is_goal,
            'cumulative_home_xg': self.match_data['home']['xg'],
            'cumulative_away_xg': self.match_data['away']['xg']
        })
    
    def get_current_state(self) -> Dict[str, Any]:
        """Mevcut xG durumunu getir"""
        return {
            'home_xg': round(self.match_data['home']['xg'], 2),
            'away_xg': round(self.match_data['away']['xg'], 2),
            'home_goals': self.match_data['home']['goals'],
            'away_goals': self.match_data['away']['goals'],
            'home_efficiency': self._calculate_efficiency('home'),
            'away_efficiency': self._calculate_efficiency('away'),
            'timeline': self.timeline
        }
    
    def _calculate_efficiency(self, team: str) -> float:
        """Takım bitiricilik oranı"""
        xg = self.match_data[team]['xg']
        goals = self.match_data[team]['goals']
        
        if xg > 0:
            return round((goals / xg) * 100, 1)
        return 0.0
    
    def get_match_summary(self) -> Dict[str, Any]:
        """Maç sonu xG özeti"""
        home_comp = self.calculator.compare_xg_vs_goals(
            self.match_data['home']['xg'],
            self.match_data['home']['goals']
        )
        away_comp = self.calculator.compare_xg_vs_goals(
            self.match_data['away']['xg'],
            self.match_data['away']['goals']
        )
        
        return {
            'final_score': f"{self.match_data['home']['goals']} - {self.match_data['away']['goals']}",
            'final_xg': f"{round(self.match_data['home']['xg'], 2)} - {round(self.match_data['away']['xg'], 2)}",
            'home_analysis': home_comp,
            'away_analysis': away_comp,
            'total_shots': len(self.match_data['home']['shots']) + len(self.match_data['away']['shots']),
            'timeline': self.timeline
        }


# Örnek kullanım fonksiyonları
def demo_xg_calculation():
    """xG hesaplama demo"""
    calc = xGCalculator()
    
    # Örnek: Ceza sahası içinden şut
    shot1 = calc.calculate_shot_xg(
        distance=12,
        angle=15,
        situation='open_play',
        defender_count=1,
        goalkeeper_position='normal'
    )
    print("Örnek Şut 1:", shot1)
    
    # Örnek: 1v1 pozisyon
    shot2 = calc.calculate_shot_xg(
        distance=8,
        angle=5,
        situation='one_on_one',
        defender_count=0,
        goalkeeper_position='bad'
    )
    print("\nÖrnek Şut 2 (1v1):", shot2)
    
    # Örnek: Uzak mesafe
    shot3 = calc.calculate_shot_xg(
        distance=28,
        angle=20,
        situation='open_play',
        defender_count=3
    )
    print("\nÖrnek Şut 3 (Uzak):", shot3)


if __name__ == "__main__":
    demo_xg_calculation()
