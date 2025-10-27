# -*- coding: utf-8 -*-
"""
Live Momentum Tracker
=====================
Canlı maç momentum analizi ve trend tespiti
"""

from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
from collections import deque
import math

class MomentumTracker:
    """Maç içi momentum takip sistemi"""
    
    def __init__(self, window_size: int = 10):
        """
        Args:
            window_size: Momentum hesaplama için pencere boyutu (dakika)
        """
        self.window_size = window_size
        self.events = []
        self.momentum_history = []
        
        # Event ağırlıkları
        self.event_weights = {
            'goal': 100,
            'penalty_goal': 100,
            'missed_penalty': -80,
            'shot_on_target': 15,
            'shot_off_target': 5,
            'shot_blocked': 3,
            'corner': 8,
            'free_kick_dangerous': 12,
            'possession_gain': 2,
            'successful_dribble': 6,
            'key_pass': 10,
            'big_chance_created': 25,
            'big_chance_missed': -15,
            'tackle_won': 4,
            'interception': 3,
            'clearance': 2,
            'save': -10,  # Rakip için pozitif
            'yellow_card': -5,
            'red_card': -30,
            'offside': -3,
            'foul_committed': -2,
            'substitution_attacking': 5,
            'substitution_defensive': -3,
        }
    
    def add_event(self, 
                  minute: int,
                  team: str,
                  event_type: str,
                  details: Optional[Dict] = None):
        """
        Maç olayı ekle
        
        Args:
            minute: Dakika
            team: 'home' veya 'away'
            event_type: Olay tipi
            details: Ek detaylar
        """
        weight = self.event_weights.get(event_type, 0)
        
        # Takım için pozitif, rakip için negatif
        if team == 'away':
            weight = -weight
        
        event = {
            'minute': minute,
            'team': team,
            'type': event_type,
            'weight': weight,
            'details': details or {},
            'timestamp': datetime.now()
        }
        
        self.events.append(event)
        
        # Momentum güncelle
        self._update_momentum(minute)
    
    def _update_momentum(self, current_minute: int):
        """Mevcut momentum'u hesapla"""
        # Son N dakikalık olayları al
        recent_events = [
            e for e in self.events 
            if current_minute - self.window_size <= e['minute'] <= current_minute
        ]
        
        if not recent_events:
            momentum = 0
        else:
            # Yakın geçmişteki olaylara daha fazla ağırlık ver (exponential decay)
            total_weight = 0
            for event in recent_events:
                time_diff = current_minute - event['minute']
                decay = math.exp(-time_diff / (self.window_size / 2))
                total_weight += event['weight'] * decay
            
            # -100 ile +100 arasında normalize et
            momentum = max(-100, min(100, total_weight))
        
        self.momentum_history.append({
            'minute': current_minute,
            'momentum': round(momentum, 2),
            'home_score': momentum if momentum > 0 else 0,
            'away_score': abs(momentum) if momentum < 0 else 0
        })
    
    def get_current_momentum(self) -> Dict[str, Any]:
        """Mevcut momentum durumu"""
        if not self.momentum_history:
            return {
                'momentum': 0,
                'trend': 'neutral',
                'dominant_team': 'none',
                'strength': 'none'
            }
        
        current = self.momentum_history[-1]
        momentum = current['momentum']
        
        # Trend analizi (son 5 dakika)
        if len(self.momentum_history) >= 5:
            recent = [m['momentum'] for m in self.momentum_history[-5:]]
            trend_slope = (recent[-1] - recent[0]) / 5
            
            if trend_slope > 5:
                trend = 'rising_home'
            elif trend_slope < -5:
                trend = 'rising_away'
            elif -5 <= trend_slope <= 5:
                trend = 'stable'
            else:
                trend = 'neutral'
        else:
            trend = 'neutral'
        
        # Baskın takım
        if momentum > 20:
            dominant = 'home'
            strength = 'strong' if momentum > 50 else 'moderate'
        elif momentum < -20:
            dominant = 'away'
            strength = 'strong' if momentum < -50 else 'moderate'
        else:
            dominant = 'balanced'
            strength = 'weak'
        
        return {
            'momentum': round(momentum, 2),
            'trend': trend,
            'dominant_team': dominant,
            'strength': strength,
            'minute': current['minute']
        }
    
    def get_momentum_timeline(self) -> List[Dict]:
        """Momentum zaman çizelgesi"""
        return self.momentum_history
    
    def detect_momentum_shifts(self, threshold: float = 30) -> List[Dict]:
        """
        Önemli momentum değişimlerini tespit et
        
        Args:
            threshold: Değişim eşiği
            
        Returns:
            Momentum değişim noktaları
        """
        if len(self.momentum_history) < 2:
            return []
        
        shifts = []
        prev_momentum = self.momentum_history[0]['momentum']
        
        for i, current in enumerate(self.momentum_history[1:], 1):
            momentum_change = current['momentum'] - prev_momentum
            
            if abs(momentum_change) >= threshold:
                # Değişime sebep olan olayları bul
                minute = current['minute']
                recent_events = [
                    e for e in self.events
                    if minute - 5 <= e['minute'] <= minute
                ]
                
                shifts.append({
                    'minute': minute,
                    'from': round(prev_momentum, 2),
                    'to': round(current['momentum'], 2),
                    'change': round(momentum_change, 2),
                    'direction': 'home' if momentum_change > 0 else 'away',
                    'trigger_events': recent_events[-3:] if recent_events else []
                })
            
            prev_momentum = current['momentum']
        
        return shifts
    
    def predict_next_goal(self) -> Dict[str, Any]:
        """
        Momentum bazlı bir sonraki golü tahmin et
        
        Returns:
            Tahmin bilgisi
        """
        current = self.get_current_momentum()
        momentum = current['momentum']
        
        # Momentum'a göre olasılık hesapla
        # +100 momentum = %75 ev sahibi, -100 = %75 deplasman
        home_prob = 50 + (momentum * 0.25)
        away_prob = 100 - home_prob
        
        # Trend faktörü ekle
        if current['trend'] == 'rising_home':
            home_prob += 10
            away_prob -= 10
        elif current['trend'] == 'rising_away':
            home_prob -= 10
            away_prob += 10
        
        # 0-100 arasında sınırla
        home_prob = max(0, min(100, home_prob))
        away_prob = 100 - home_prob
        
        # En olası
        if home_prob > 60:
            likely_scorer = 'home'
            confidence = 'high' if home_prob > 70 else 'medium'
        elif away_prob > 60:
            likely_scorer = 'away'
            confidence = 'high' if away_prob > 70 else 'medium'
        else:
            likely_scorer = 'uncertain'
            confidence = 'low'
        
        return {
            'home_probability': round(home_prob, 1),
            'away_probability': round(away_prob, 1),
            'likely_scorer': likely_scorer,
            'confidence': confidence,
            'based_on_momentum': round(momentum, 2)
        }
    
    def get_pressure_index(self) -> Dict[str, Any]:
        """
        Baskı endeksi - hangi takım daha fazla baskı yapıyor
        
        Returns:
            Baskı analizi
        """
        if not self.events:
            return {'home': 0, 'away': 0, 'dominant': 'none'}
        
        # Son 10 dakikalık saldırı olayları
        recent_minute = self.events[-1]['minute']
        attacking_events = ['shot_on_target', 'shot_off_target', 'corner', 
                          'big_chance_created', 'key_pass', 'successful_dribble']
        
        home_pressure = 0
        away_pressure = 0
        
        for event in self.events:
            if event['minute'] >= recent_minute - 10:
                if event['type'] in attacking_events:
                    if event['team'] == 'home':
                        home_pressure += self.event_weights.get(event['type'], 5)
                    else:
                        away_pressure += self.event_weights.get(event['type'], 5)
        
        total = home_pressure + away_pressure
        if total > 0:
            home_pct = (home_pressure / total) * 100
            away_pct = (away_pressure / total) * 100
        else:
            home_pct = away_pct = 50
        
        return {
            'home': round(home_pct, 1),
            'away': round(away_pct, 1),
            'dominant': 'home' if home_pct > 60 else ('away' if away_pct > 60 else 'balanced')
        }
    
    def get_critical_moments(self) -> List[Dict]:
        """
        Maçın kritik anlarını belirle
        
        Returns:
            Kritik anlar listesi
        """
        critical = []
        
        # Gol anları
        goals = [e for e in self.events if e['type'] == 'goal']
        for goal in goals:
            critical.append({
                'minute': goal['minute'],
                'type': 'goal',
                'team': goal['team'],
                'importance': 'very_high',
                'description': f"{goal['team'].upper()} takımı gol attı"
            })
        
        # Büyük kaçan fırsatlar
        missed_chances = [e for e in self.events if e['type'] == 'big_chance_missed']
        for chance in missed_chances:
            critical.append({
                'minute': chance['minute'],
                'type': 'missed_chance',
                'team': chance['team'],
                'importance': 'high',
                'description': f"{chance['team'].upper()} takımı büyük fırsat kaçırdı"
            })
        
        # Kırmızı kartlar
        red_cards = [e for e in self.events if e['type'] == 'red_card']
        for card in red_cards:
            critical.append({
                'minute': card['minute'],
                'type': 'red_card',
                'team': card['team'],
                'importance': 'very_high',
                'description': f"{card['team'].upper()} takımı kırmızı kart gördü"
            })
        
        # Momentum değişimleri
        shifts = self.detect_momentum_shifts(threshold=40)
        for shift in shifts:
            critical.append({
                'minute': shift['minute'],
                'type': 'momentum_shift',
                'team': shift['direction'],
                'importance': 'medium',
                'description': f"Momentum {shift['direction'].upper()} takımına geçti"
            })
        
        # Dakikaya göre sırala
        critical.sort(key=lambda x: x['minute'])
        
        return critical
    
    def get_match_report(self) -> Dict[str, Any]:
        """
        Detaylı maç momentum raporu
        
        Returns:
            Kapsamlı rapor
        """
        current_momentum = self.get_current_momentum()
        pressure = self.get_pressure_index()
        next_goal_pred = self.predict_next_goal()
        shifts = self.detect_momentum_shifts()
        critical = self.get_critical_moments()
        
        # İstatistikler
        event_counts = {}
        for event in self.events:
            event_type = event['type']
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        return {
            'current_momentum': current_momentum,
            'pressure_index': pressure,
            'next_goal_prediction': next_goal_pred,
            'momentum_shifts': len(shifts),
            'critical_moments': critical,
            'total_events': len(self.events),
            'event_breakdown': event_counts,
            'timeline': self.momentum_history,
            'match_phase': self._determine_match_phase()
        }
    
    def _determine_match_phase(self) -> str:
        """Maç fazını belirle"""
        if not self.events:
            return 'early'
        
        last_minute = self.events[-1]['minute']
        
        if last_minute <= 15:
            return 'early'
        elif last_minute <= 30:
            return 'settling'
        elif last_minute <= 45:
            return 'first_half_end'
        elif last_minute <= 60:
            return 'second_half_start'
        elif last_minute <= 75:
            return 'mid_second_half'
        elif last_minute <= 85:
            return 'crucial'
        else:
            return 'final_push'


class MomentumVisualizer:
    """Momentum görselleştirme yardımcı sınıfı"""
    
    @staticmethod
    def get_momentum_bar_html(momentum: float) -> str:
        """
        Momentum bar HTML oluştur
        
        Args:
            momentum: -100 ile +100 arası momentum değeri
            
        Returns:
            HTML string
        """
        # Renk belirleme
        if momentum > 50:
            color = '#00cc00'  # Koyu yeşil
        elif momentum > 20:
            color = '#66ff66'  # Açık yeşil
        elif momentum > -20:
            color = '#ffff00'  # Sarı
        elif momentum > -50:
            color = '#ff9966'  # Turuncu
        else:
            color = '#ff3333'  # Kırmızı
        
        # Bar genişliği (0-100)
        bar_width = abs(momentum)
        
        # Sol veya sağ
        if momentum >= 0:
            # Ev sahibi (sol)
            html = f"""
            <div style="display: flex; align-items: center; margin: 10px 0;">
                <span style="width: 80px; text-align: right; margin-right: 10px; font-weight: bold;">
                    EV SAHİBİ
                </span>
                <div style="width: 50%; background: #e0e0e0; height: 30px; position: relative;">
                    <div style="width: {bar_width}%; background: {color}; height: 100%; 
                         position: absolute; left: 0;"></div>
                    <span style="position: absolute; left: 50%; top: 50%; 
                         transform: translate(-50%, -50%); font-weight: bold;">
                        {round(momentum, 1)}
                    </span>
                </div>
                <div style="width: 50%; background: #e0e0e0; height: 30px;"></div>
                <span style="width: 80px; text-align: left; margin-left: 10px; opacity: 0.5;">
                    DEPLASMAN
                </span>
            </div>
            """
        else:
            # Deplasman (sağ)
            html = f"""
            <div style="display: flex; align-items: center; margin: 10px 0;">
                <span style="width: 80px; text-align: right; margin-right: 10px; opacity: 0.5;">
                    EV SAHİBİ
                </span>
                <div style="width: 50%; background: #e0e0e0; height: 30px;"></div>
                <div style="width: 50%; background: #e0e0e0; height: 30px; position: relative;">
                    <div style="width: {bar_width}%; background: {color}; height: 100%; 
                         position: absolute; right: 0;"></div>
                    <span style="position: absolute; left: 50%; top: 50%; 
                         transform: translate(-50%, -50%); font-weight: bold;">
                        {round(abs(momentum), 1)}
                    </span>
                </div>
                <span style="width: 80px; text-align: left; margin-left: 10px; font-weight: bold;">
                    DEPLASMAN
                </span>
            </div>
            """
        
        return html
    
    @staticmethod
    def get_trend_emoji(trend: str) -> str:
        """Trend emoji"""
        emoji_map = {
            'rising_home': '📈🏠',
            'rising_away': '📈✈️',
            'stable': '➡️',
            'neutral': '↔️'
        }
        return emoji_map.get(trend, '❓')
    
    @staticmethod
    def get_strength_emoji(strength: str) -> str:
        """Güç emoji"""
        emoji_map = {
            'strong': '💪💪💪',
            'moderate': '💪💪',
            'weak': '💪',
            'none': '😐'
        }
        return emoji_map.get(strength, '❓')


# Demo fonksiyon
def demo_momentum_tracking():
    """Momentum tracking demo"""
    tracker = MomentumTracker(window_size=10)
    
    # Örnek maç simülasyonu
    tracker.add_event(5, 'home', 'shot_on_target')
    tracker.add_event(7, 'home', 'corner')
    tracker.add_event(12, 'away', 'shot_on_target')
    tracker.add_event(15, 'home', 'goal')
    tracker.add_event(20, 'away', 'shot_on_target')
    tracker.add_event(23, 'away', 'big_chance_missed')
    tracker.add_event(30, 'away', 'goal')
    tracker.add_event(35, 'home', 'shot_on_target')
    tracker.add_event(40, 'home', 'corner')
    
    # Rapor
    report = tracker.get_match_report()
    print("MOMENTUM RAPORU:")
    print(f"Mevcut Momentum: {report['current_momentum']}")
    print(f"Baskı Endeksi: {report['pressure_index']}")
    print(f"Sonraki Gol Tahmini: {report['next_goal_prediction']}")
    print(f"Kritik Anlar: {len(report['critical_moments'])}")


if __name__ == "__main__":
    demo_momentum_tracking()
