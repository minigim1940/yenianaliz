# -*- coding: utf-8 -*-
"""
Expected Assists (xA) Calculator
================================
Asist kalitesi ve şans yaratma metrikleri

Metrikler:
1. xA - Expected Assists (pasın gol olma olasılığı)
2. Chance Creation Quality - Şans yaratma kalitesi
3. Key Passes - Anahtar paslar
4. Shot-Creating Actions - Şut yaratan aksiyonlar
5. Goal-Creating Actions - Gol yaratan aksiyonlar
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
import math

class ExpectedAssistsCalculator:
    """Expected Assists (xA) hesaplayıcı"""
    
    # Pass types ve xA multipliers
    PASS_TYPE_MULTIPLIERS = {
        'through_ball': 1.35,       # Ara pas (en değerli)
        'cross': 0.75,              # Orta
        'cutback': 1.20,            # Geriye çekilme
        'long_ball': 0.60,          # Uzun top
        'short_pass': 1.00,         # Kısa pas
        'set_piece': 0.85           # Duran top
    }
    
    # Pass end location multipliers (pası alan oyuncunun pozisyonu)
    LOCATION_MULTIPLIERS = {
        'six_yard_box': 1.50,       # 6 pas kutusu (çok tehlikeli)
        'penalty_area': 1.25,       # Ceza sahası
        'edge_of_box': 1.00,        # Ceza sahası dışı
        'wide_area': 0.70,          # Kanat bölgesi
        'long_range': 0.40          # Uzak mesafe
    }
    
    # Defensive pressure multipliers
    PRESSURE_MULTIPLIERS = {
        'no_pressure': 1.20,        # Baskısız
        'low_pressure': 1.00,       # Düşük baskı
        'medium_pressure': 0.85,    # Orta baskı
        'high_pressure': 0.65       # Yüksek baskı
    }
    
    def __init__(self):
        pass
    
    def calculate_xa_for_pass(
        self,
        pass_type: str,
        end_location: str,
        distance_to_goal: float,
        defensive_pressure: str = 'medium_pressure',
        receiver_quality: float = 1.0
    ) -> float:
        """
        Tek bir pas için xA hesapla
        
        Args:
            pass_type: Pas tipi (through_ball, cross, etc.)
            end_location: Pasın bittiği yer
            distance_to_goal: Kaleye mesafe (metre)
            defensive_pressure: Defansif baskı seviyesi
            receiver_quality: Pası alan oyuncunun kalitesi (0.7-1.3)
            
        Returns:
            xA value (0.0 - 1.0)
        """
        # Base xA (distance to goal bazlı)
        # 5m = 0.35, 10m = 0.20, 15m = 0.12, 20m+ = 0.05
        if distance_to_goal <= 6:
            base_xa = 0.35
        elif distance_to_goal <= 11:
            base_xa = 0.25
        elif distance_to_goal <= 16:
            base_xa = 0.15
        elif distance_to_goal <= 20:
            base_xa = 0.08
        else:
            base_xa = 0.03
        
        # Multipliers
        pass_mult = self.PASS_TYPE_MULTIPLIERS.get(pass_type, 1.0)
        location_mult = self.LOCATION_MULTIPLIERS.get(end_location, 1.0)
        pressure_mult = self.PRESSURE_MULTIPLIERS.get(defensive_pressure, 1.0)
        
        # Composite xA
        xa = base_xa * pass_mult * location_mult * pressure_mult * receiver_quality
        
        # Clamp to [0.01, 0.95]
        return max(0.01, min(0.95, xa))
    
    def estimate_team_xa_from_stats(
        self,
        team_stats: Dict,
        match_count: int = 1
    ) -> Dict[str, float]:
        """
        Takım istatistiklerinden xA tahmini
        
        Args:
            team_stats: Takım istatistikleri
            match_count: Kaç maç
            
        Returns:
            {
                'total_xA': 1.85,
                'xA_per_match': 1.85,
                'key_passes': 12,
                'shot_creating_actions': 18,
                'chance_quality': 75.5
            }
        """
        # Key passes
        key_passes = team_stats.get('key_passes', 0)
        
        # Assists (gerçek)
        assists = team_stats.get('assists', 0)
        
        # Shots on target (rakip takımın)
        # Her key pass bir şut yaratıyorsa...
        
        # xA estimation
        # Varsayım: Her key pass ortalama 0.15 xA değerinde
        # Through balls ve cutbacks daha değerli: 0.25
        # Crosses daha az değerli: 0.10
        
        # Basit tahmin: Key passes * ortalama xA
        average_xa_per_key_pass = 0.15
        estimated_xa = key_passes * average_xa_per_key_pass
        
        # xA per match
        xa_per_match = estimated_xa / match_count if match_count > 0 else estimated_xa
        
        # Shot creating actions tahmini
        # Key passes + successful dribbles + fouls won in box
        successful_dribbles = team_stats.get('dribbles_success', 0)
        shot_creating_actions = key_passes + int(successful_dribbles * 0.5)
        
        # Chance quality (0-100)
        # xA / key passes oranı (kaliteli şans = yüksek xA/key pass)
        if key_passes > 0:
            chance_quality_ratio = (estimated_xa / key_passes) * 100
            chance_quality = min(100, chance_quality_ratio * 6)  # Normalize to 100
        else:
            chance_quality = 50.0
        
        # Over/Under performance (gerçek assist vs xA)
        if estimated_xa > 0:
            over_performance = assists - estimated_xa
        else:
            over_performance = 0.0
        
        return {
            'total_xA': round(estimated_xa, 2),
            'xA_per_match': round(xa_per_match, 2),
            'key_passes': key_passes,
            'key_passes_per_match': round(key_passes / match_count, 2) if match_count > 0 else 0,
            'shot_creating_actions': shot_creating_actions,
            'chance_quality': round(chance_quality, 2),
            'actual_assists': assists,
            'over_performance': round(over_performance, 2),
            'interpretation': self._interpret_xa(xa_per_match)
        }
    
    def calculate_chance_creation_quality(
        self,
        key_passes: int,
        big_chances_created: int,
        shots_from_key_passes: int,
        goals_from_key_passes: int
    ) -> Dict[str, float]:
        """
        Şans yaratma kalitesini hesapla
        
        Args:
            key_passes: Anahtar pas sayısı
            big_chances_created: Büyük şans yaratma
            shots_from_key_passes: Key pass'lerden şut
            goals_from_key_passes: Key pass'lerden gol
            
        Returns:
            Chance creation quality metrics
        """
        if key_passes == 0:
            return self._get_default_chance_quality()
        
        # Big chance ratio (her key pass'in kaçı big chance)
        big_chance_ratio = (big_chances_created / key_passes) * 100
        
        # Conversion to shot (key pass -> şut)
        shot_conversion = (shots_from_key_passes / key_passes) * 100
        
        # Conversion to goal (key pass -> gol)
        goal_conversion = (goals_from_key_passes / key_passes) * 100
        
        # Overall quality score
        quality_score = (
            big_chance_ratio * 0.40 +
            shot_conversion * 0.35 +
            goal_conversion * 0.25
        )
        
        return {
            'chance_quality_score': round(quality_score, 2),
            'big_chance_ratio': round(big_chance_ratio, 2),
            'shot_conversion': round(shot_conversion, 2),
            'goal_conversion': round(goal_conversion, 2),
            'classification': self._classify_chance_quality(quality_score)
        }
    
    def calculate_playmaker_score(
        self,
        xa: float,
        key_passes: int,
        progressive_passes: int,
        through_balls: int,
        assists: int
    ) -> Dict[str, float]:
        """
        Playmaker (oyun kurucu) skorunu hesapla
        
        Combines:
        - xA (şans yaratma)
        - Progressive passes (ileri oyun)
        - Through balls (killer passes)
        - Actual assists (sonuç)
        
        Returns:
            {
                'playmaker_score': 85.5,  # 0-100
                'creativity': 78.0,
                'productivity': 82.0,
                'ranking': 'Elite'
            }
        """
        # Creativity (xA + through balls + progressive passes)
        # Normalized to 0-100
        creativity_raw = (xa * 10) + (through_balls * 2) + (progressive_passes * 0.5)
        creativity = min(100, creativity_raw)
        
        # Productivity (key passes + assists)
        productivity_raw = (key_passes * 3) + (assists * 8)
        productivity = min(100, productivity_raw)
        
        # Overall playmaker score
        playmaker_score = (creativity * 0.55 + productivity * 0.45)
        
        # Ranking
        ranking = self._get_playmaker_ranking(playmaker_score)
        
        return {
            'playmaker_score': round(playmaker_score, 2),
            'creativity': round(creativity, 2),
            'productivity': round(productivity, 2),
            'ranking': ranking,
            'components': {
                'xA_contribution': round((xa * 10), 2),
                'through_balls_contribution': round((through_balls * 2), 2),
                'progressive_contribution': round((progressive_passes * 0.5), 2),
                'assists_contribution': round((assists * 8), 2)
            }
        }
    
    def compare_xa_vs_assists(
        self,
        xa: float,
        actual_assists: int
    ) -> Dict[str, any]:
        """
        xA vs Gerçek Assist karşılaştırması
        
        Returns:
            Over/under performance analysis
        """
        difference = actual_assists - xa
        
        if difference > 2:
            performance = "Overperforming (Lucky or Clinical finishers)"
        elif difference > 0.5:
            performance = "Slightly Overperforming"
        elif difference < -2:
            performance = "Underperforming (Unlucky or Poor finishers)"
        elif difference < -0.5:
            performance = "Slightly Underperforming"
        else:
            performance = "As Expected"
        
        # Efficiency (gerçek / beklenen)
        if xa > 0:
            efficiency = (actual_assists / xa) * 100
        else:
            efficiency = 100.0 if actual_assists > 0 else 0.0
        
        return {
            'xa': round(xa, 2),
            'actual_assists': actual_assists,
            'difference': round(difference, 2),
            'efficiency': round(efficiency, 2),
            'performance': performance
        }
    
    # Helper methods
    
    def _interpret_xa(self, xa_per_match: float) -> str:
        """xA interpretation"""
        if xa_per_match >= 0.50:
            return "Elite Chance Creator (De Bruyne level)"
        elif xa_per_match >= 0.35:
            return "Excellent Chance Creator"
        elif xa_per_match >= 0.25:
            return "Good Chance Creator"
        elif xa_per_match >= 0.15:
            return "Average Chance Creator"
        else:
            return "Limited Chance Creation"
    
    def _classify_chance_quality(self, quality_score: float) -> str:
        """Chance quality classification"""
        if quality_score >= 75:
            return "Elite Quality Chances"
        elif quality_score >= 60:
            return "High Quality Chances"
        elif quality_score >= 45:
            return "Good Quality Chances"
        elif quality_score >= 30:
            return "Average Quality"
        else:
            return "Low Quality Chances"
    
    def _get_playmaker_ranking(self, score: float) -> str:
        """Playmaker ranking"""
        if score >= 85:
            return "Elite (Top 1% - KDB, Bruno Fernandes)"
        elif score >= 70:
            return "Excellent (Top 10%)"
        elif score >= 55:
            return "Good (Top 30%)"
        elif score >= 40:
            return "Average"
        else:
            return "Below Average"
    
    def _get_default_chance_quality(self) -> Dict:
        """Default chance quality"""
        return {
            'chance_quality_score': 50.0,
            'big_chance_ratio': 25.0,
            'shot_conversion': 40.0,
            'goal_conversion': 15.0,
            'classification': 'Average Quality'
        }


# Test
if __name__ == "__main__":
    calculator = ExpectedAssistsCalculator()
    
    print("🎯 Expected Assists (xA) Calculator Test\n")
    
    # Test 1: Single pass xA
    print("1️⃣ Single Pass xA (Through Ball)")
    xa = calculator.calculate_xa_for_pass(
        pass_type='through_ball',
        end_location='penalty_area',
        distance_to_goal=12,
        defensive_pressure='low_pressure',
        receiver_quality=1.1
    )
    print(f"   xA Value: {xa:.3f}")
    print()
    
    # Test 2: Team xA estimation
    print("2️⃣ Team xA Estimation (Creative Team)")
    team_xa = calculator.estimate_team_xa_from_stats(
        team_stats={
            'key_passes': 15,
            'assists': 2,
            'dribbles_success': 8
        },
        match_count=1
    )
    print(f"   xA per Match: {team_xa['xA_per_match']}")
    print(f"   Key Passes: {team_xa['key_passes']}")
    print(f"   Chance Quality: {team_xa['chance_quality']}")
    print(f"   Interpretation: {team_xa['interpretation']}")
    print()
    
    # Test 3: Playmaker Score
    print("3️⃣ Playmaker Score (Kevin De Bruyne Style)")
    playmaker = calculator.calculate_playmaker_score(
        xa=3.5,
        key_passes=25,
        progressive_passes=85,
        through_balls=12,
        assists=4
    )
    print(f"   Playmaker Score: {playmaker['playmaker_score']}")
    print(f"   Creativity: {playmaker['creativity']}")
    print(f"   Productivity: {playmaker['productivity']}")
    print(f"   Ranking: {playmaker['ranking']}")
    print()
    
    # Test 4: xA vs Assists comparison
    print("4️⃣ xA vs Assists Comparison")
    comparison = calculator.compare_xa_vs_assists(xa=2.5, actual_assists=4)
    print(f"   Expected (xA): {comparison['xa']}")
    print(f"   Actual: {comparison['actual_assists']}")
    print(f"   Difference: {comparison['difference']}")
    print(f"   Performance: {comparison['performance']}")
