# -*- coding: utf-8 -*-
"""
Advanced Form Calculation System
================================
Dünya standartlarına uygun, çok faktörlü form hesaplama sistemi

Kullanılan Faktörler:
1. Match Results (Maç Sonuçları) - 40%
2. Opponent Strength (Rakip Gücü) - 30%
3. Goal Difference (Gol Farkı) - 20%
4. Recent Trend (Son Trend) - 10%
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime
import math

class AdvancedFormCalculator:
    """Gelişmiş form hesaplama sistemi"""
    
    # Weight factors (Ağırlık faktörleri)
    WEIGHTS = {
        'result': 0.40,      # Maç sonucu
        'opponent': 0.30,    # Rakip gücü
        'goal_diff': 0.20,   # Gol farkı
        'trend': 0.10        # Trend (ivme)
    }
    
    # Result points (Sonuç puanları)
    RESULT_POINTS = {
        'win': 3.0,
        'draw': 1.0,
        'loss': 0.0
    }
    
    def __init__(self):
        self.baseline_form = 1.5  # Nötr form seviyesi
        
    def calculate_advanced_form(
        self, 
        matches: List[Dict],
        opponent_strengths: Optional[List[float]] = None,
        location_filter: Optional[str] = None,
        num_matches: int = 10
    ) -> Dict[str, float]:
        """
        Gelişmiş form hesaplama
        
        Args:
            matches: Maç listesi [{'goals_for': 2, 'goals_against': 1, 'location': 'home', ...}]
            opponent_strengths: Her maç için rakip gücü listesi (Elo veya benzeri) [1500, 1600, ...]
            location_filter: 'home', 'away' veya None (tüm maçlar)
            num_matches: Kaç maç geriye bakılacak
            
        Returns:
            {
                'form_factor': 1.12,  # 0.7 - 1.3 arası
                'form_score': 75.5,   # 0-100 arası
                'form_string': 'WWDWL',
                'trend': 'improving',  # improving/stable/declining
                'confidence': 0.85,    # 0-1 arası
                'breakdown': {...}     # Detaylı analiz
            }
        """
        if not matches:
            return self._get_default_form()
        
        # Maçları filtrele
        filtered_matches = self._filter_matches(matches, location_filter, num_matches)
        
        if not filtered_matches:
            return self._get_default_form()
        
        # 1. Result Score (Sonuç skoru)
        result_score = self._calculate_result_score(filtered_matches)
        
        # 2. Opponent-adjusted Score (Rakip ayarlı skor)
        opponent_score = self._calculate_opponent_adjusted_score(
            filtered_matches, 
            opponent_strengths
        )
        
        # 3. Goal Difference Score (Gol farkı skoru)
        goal_diff_score = self._calculate_goal_difference_score(filtered_matches)
        
        # 4. Trend Score (Trend skoru - ivme)
        trend_score, trend_direction = self._calculate_trend_score(filtered_matches)
        
        # Weighted composite score (Ağırlıklı toplam skor)
        composite_score = (
            result_score * self.WEIGHTS['result'] +
            opponent_score * self.WEIGHTS['opponent'] +
            goal_diff_score * self.WEIGHTS['goal_diff'] +
            trend_score * self.WEIGHTS['trend']
        )
        
        # Form factor hesapla (0.7 - 1.3 arası)
        form_factor = self._score_to_factor(composite_score)
        
        # Form string (WWDWL)
        form_string = self._get_form_string(filtered_matches[:5])
        
        # Confidence (güvenilirlik - maç sayısına göre)
        confidence = min(1.0, len(filtered_matches) / num_matches)
        
        return {
            'form_factor': form_factor,
            'form_score': composite_score,
            'form_string': form_string,
            'trend': trend_direction,
            'confidence': confidence,
            'breakdown': {
                'result_score': result_score,
                'opponent_adjusted_score': opponent_score,
                'goal_difference_score': goal_diff_score,
                'trend_score': trend_score,
                'matches_analyzed': len(filtered_matches)
            }
        }
    
    def _filter_matches(
        self, 
        matches: List[Dict], 
        location: Optional[str], 
        limit: int
    ) -> List[Dict]:
        """Maçları filtrele ve sırala"""
        filtered = matches
        
        # Lokasyon filtresi
        if location:
            filtered = [m for m in filtered if m.get('location') == location]
        
        # En yeni maçları al
        return filtered[:limit]
    
    def _calculate_result_score(self, matches: List[Dict]) -> float:
        """
        Maç sonuçlarına göre skor hesapla (0-100)
        Yeni maçlara daha fazla ağırlık verilir
        """
        if not matches:
            return 50.0
        
        weighted_points = 0.0
        total_weight = 0.0
        
        for idx, match in enumerate(matches):
            # Ağırlık: En yeni maç en yüksek (ters sıra)
            weight = len(matches) - idx
            
            # Sonuç puanı
            gf = match.get('goals_for', 0)
            ga = match.get('goals_against', 0)
            
            if gf > ga:
                points = self.RESULT_POINTS['win']
            elif gf == ga:
                points = self.RESULT_POINTS['draw']
            else:
                points = self.RESULT_POINTS['loss']
            
            weighted_points += points * weight
            total_weight += weight
        
        # 0-100 arası normalize et (3 puan max)
        avg_points = weighted_points / total_weight
        score = (avg_points / 3.0) * 100
        
        return round(score, 2)
    
    def _calculate_opponent_adjusted_score(
        self, 
        matches: List[Dict],
        opponent_strengths: Optional[List[float]]
    ) -> float:
        """
        Rakip gücüne göre ayarlanmış skor (0-100)
        Güçlü rakiplere karşı alınan sonuçlar daha değerli
        """
        if not matches:
            return 50.0
        
        # Rakip güçleri yoksa, sadece result score döndür
        if not opponent_strengths or len(opponent_strengths) != len(matches):
            return self._calculate_result_score(matches)
        
        weighted_score = 0.0
        total_weight = 0.0
        
        # Ortalama rakip gücü (normalizasyon için)
        avg_opponent_strength = sum(opponent_strengths) / len(opponent_strengths)
        
        for idx, match in enumerate(matches):
            # Maç ağırlığı (yeni maçlar daha önemli)
            match_weight = len(matches) - idx
            
            # Rakip gücü faktörü (1.0 = ortalama, 1.2 = güçlü, 0.8 = zayıf)
            opponent_factor = opponent_strengths[idx] / avg_opponent_strength
            opponent_factor = max(0.7, min(1.3, opponent_factor))
            
            # Sonuç puanı
            gf = match.get('goals_for', 0)
            ga = match.get('goals_against', 0)
            
            if gf > ga:
                points = self.RESULT_POINTS['win']
            elif gf == ga:
                points = self.RESULT_POINTS['draw']
            else:
                points = self.RESULT_POINTS['loss']
            
            # Rakip gücüne göre ayarla
            adjusted_points = points * opponent_factor
            
            weighted_score += adjusted_points * match_weight
            total_weight += match_weight
        
        # 0-100 arası normalize et
        avg_adjusted = weighted_score / total_weight
        score = (avg_adjusted / 3.0) * 100
        
        return round(score, 2)
    
    def _calculate_goal_difference_score(self, matches: List[Dict]) -> float:
        """
        Gol farkı bazlı skor (0-100)
        Büyük farklarla kazanmak/kaybetmek önemlidir
        """
        if not matches:
            return 50.0
        
        weighted_gd = 0.0
        total_weight = 0.0
        
        for idx, match in enumerate(matches):
            weight = len(matches) - idx
            
            gf = match.get('goals_for', 0)
            ga = match.get('goals_against', 0)
            gd = gf - ga
            
            # Gol farkını normalize et (-5 to +5 arası etkili)
            normalized_gd = max(-5, min(5, gd))
            
            weighted_gd += normalized_gd * weight
            total_weight += weight
        
        avg_gd = weighted_gd / total_weight
        
        # -5 to +5 aralığını 0-100'e çevir
        score = ((avg_gd + 5) / 10) * 100
        
        return round(score, 2)
    
    def _calculate_trend_score(self, matches: List[Dict]) -> Tuple[float, str]:
        """
        Form trendi (ivme) hesapla
        Son maçlar önceki maçlardan daha mı iyi?
        
        Returns:
            (score, direction): (0-100, 'improving'/'stable'/'declining')
        """
        if len(matches) < 4:
            return 50.0, 'stable'
        
        # İlk yarı vs İkinci yarı karşılaştırması
        mid = len(matches) // 2
        recent_half = matches[:mid]
        older_half = matches[mid:mid*2]
        
        # Her yarının ortalama puanı
        recent_points = self._get_average_points(recent_half)
        older_points = self._get_average_points(older_half)
        
        # Trend hesapla
        trend_diff = recent_points - older_points
        
        # Trend direction
        if trend_diff > 0.5:
            direction = 'improving'
        elif trend_diff < -0.5:
            direction = 'declining'
        else:
            direction = 'stable'
        
        # Trend score (0-100)
        # -3 to +3 arası değişim beklenir
        normalized_trend = max(-3, min(3, trend_diff))
        score = ((normalized_trend + 3) / 6) * 100
        
        return round(score, 2), direction
    
    def _get_average_points(self, matches: List[Dict]) -> float:
        """Maç listesinin ortalama puanı"""
        if not matches:
            return 0.0
        
        total_points = 0
        for match in matches:
            gf = match.get('goals_for', 0)
            ga = match.get('goals_against', 0)
            
            if gf > ga:
                total_points += 3
            elif gf == ga:
                total_points += 1
        
        return total_points / len(matches)
    
    def _score_to_factor(self, score: float) -> float:
        """
        0-100 arası skoru 0.7-1.3 arası faktöre çevir
        
        Score 0: Factor 0.7 (çok kötü form)
        Score 50: Factor 1.0 (nötr form)
        Score 100: Factor 1.3 (mükemmel form)
        """
        # Linear interpolation
        min_factor = 0.70
        max_factor = 1.30
        neutral_score = 50.0
        
        if score >= neutral_score:
            # 50-100 -> 1.0-1.3
            factor = 1.0 + ((score - neutral_score) / neutral_score) * (max_factor - 1.0)
        else:
            # 0-50 -> 0.7-1.0
            factor = min_factor + (score / neutral_score) * (1.0 - min_factor)
        
        return round(factor, 3)
    
    def _get_form_string(self, matches: List[Dict]) -> str:
        """Form string oluştur (WWDWL)"""
        if not matches:
            return ""
        
        form_chars = []
        for match in matches:
            gf = match.get('goals_for', 0)
            ga = match.get('goals_against', 0)
            
            if gf > ga:
                form_chars.append('W')
            elif gf == ga:
                form_chars.append('D')
            else:
                form_chars.append('L')
        
        return ''.join(form_chars)
    
    def _get_default_form(self) -> Dict:
        """Varsayılan form değerleri"""
        return {
            'form_factor': 1.0,
            'form_score': 50.0,
            'form_string': '',
            'trend': 'stable',
            'confidence': 0.0,
            'breakdown': {
                'result_score': 50.0,
                'opponent_adjusted_score': 50.0,
                'goal_difference_score': 50.0,
                'trend_score': 50.0,
                'matches_analyzed': 0
            }
        }


# Backward compatibility - Eski fonksiyonları yeni sisteme yönlendir
def calculate_form_factor(matches: Optional[List[Dict]], preferred_location: Optional[str] = None) -> float:
    """
    LEGACY FUNCTION - Geriye uyumluluk için
    Yeni AdvancedFormCalculator kullanır
    """
    calculator = AdvancedFormCalculator()
    result = calculator.calculate_advanced_form(
        matches=matches or [],
        location_filter=preferred_location,
        num_matches=10
    )
    return result['form_factor']


# Test fonksiyonu
if __name__ == "__main__":
    # Örnek test
    test_matches = [
        {'goals_for': 3, 'goals_against': 1, 'location': 'home'},   # W (en yeni)
        {'goals_for': 2, 'goals_against': 2, 'location': 'away'},   # D
        {'goals_for': 1, 'goals_against': 0, 'location': 'home'},   # W
        {'goals_for': 0, 'goals_against': 2, 'location': 'away'},   # L
        {'goals_for': 2, 'goals_against': 1, 'location': 'home'},   # W
    ]
    
    # Rakip güçleri (Elo ratings)
    opponent_strengths = [1600, 1450, 1700, 1550, 1500]
    
    calculator = AdvancedFormCalculator()
    result = calculator.calculate_advanced_form(
        matches=test_matches,
        opponent_strengths=opponent_strengths
    )
    
    print("🔍 Gelişmiş Form Analizi:")
    print(f"Form Factor: {result['form_factor']}")
    print(f"Form Score: {result['form_score']}")
    print(f"Form String: {result['form_string']}")
    print(f"Trend: {result['trend']}")
    print(f"Confidence: {result['confidence']:.2%}")
    print(f"\nBreakdown:")
    for key, value in result['breakdown'].items():
        print(f"  {key}: {value}")
