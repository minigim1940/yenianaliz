# -*- coding: utf-8 -*-
"""
Expected Goals (xG) Calculator
==============================
Dünya standartlarına uygun Expected Goals hesaplama sistemi

Faktörler:
1. Shot Distance (Şut mesafesi)
2. Shot Angle (Şut açısı)
3. Body Part (Vücut bölgesi - ayak/kafa)
4. Assist Type (Asist tipi - pas/cross/set piece)
5. Game State (Maç durumu - önde/arkada)
6. Defensive Pressure (Defansif baskı)

NOT: API'den detaylı şut verileri gelmediği için,
takım istatistiklerinden tahminsel xG hesaplayacağız.
"""

from typing import Dict, List, Optional, Tuple
import math

class ExpectedGoalsCalculator:
    """Expected Goals (xG) hesaplayıcı"""
    
    # Shot distance multipliers (metre bazlı)
    # Penalty area içi (5-11m): 0.15-0.35
    # Penalty area dışı (11-16m): 0.08-0.15
    # Long range (16m+): 0.02-0.08
    DISTANCE_XG_MAP = {
        (0, 6): 0.45,    # Çok yakın (6 adım/penaltı noktası)
        (6, 11): 0.25,   # Yakın (ceza sahası içi)
        (11, 16): 0.12,  # Orta mesafe (ceza sahası yakını)
        (16, 25): 0.05,  # Uzak mesafe
        (25, 100): 0.02  # Çok uzak
    }
    
    # Angle multipliers
    ANGLE_MULTIPLIERS = {
        'central': 1.0,      # Orta (0-15 derece)
        'wide': 0.75,        # Geniş açı (15-30 derece)
        'very_wide': 0.50    # Çok geniş (30+ derece)
    }
    
    # Body part multipliers
    BODY_PART_MULTIPLIERS = {
        'right_foot': 1.0,
        'left_foot': 1.0,
        'header': 0.70,
        'other': 0.50
    }
    
    # Assist type multipliers
    ASSIST_TYPE_MULTIPLIERS = {
        'through_ball': 1.15,  # Ara pas
        'cross': 0.85,         # Orta
        'pass': 1.0,           # Normal pas
        'rebound': 0.90,       # Sekme
        'set_piece': 0.95,     # Duran top
        'no_assist': 0.80      # Bireysel
    }
    
    # Game state multipliers
    GAME_STATE_MULTIPLIERS = {
        'drawing': 1.0,
        'winning': 0.95,   # Önde oynuyorken daha az riskli
        'losing': 1.05     # Arkada oynuyorken daha riskli
    }
    
    def __init__(self):
        pass
    
    def calculate_xg_from_shot_data(
        self,
        shot_distance: float,
        shot_angle: float,
        body_part: str = 'right_foot',
        assist_type: str = 'pass',
        game_state: str = 'drawing',
        defensive_pressure: float = 0.5
    ) -> float:
        """
        Tek bir şut için xG hesapla (ideal durum - detaylı veri varsa)
        
        Args:
            shot_distance: Şut mesafesi (metre)
            shot_angle: Şut açısı (derece, kaleye göre)
            body_part: Kullanılan vücut bölgesi
            assist_type: Asist tipi
            game_state: Maç durumu
            defensive_pressure: Defansif baskı (0-1)
            
        Returns:
            xG value (0.0 - 1.0)
        """
        # 1. Base xG from distance
        base_xg = self._get_xg_from_distance(shot_distance)
        
        # 2. Angle adjustment
        angle_mult = self._get_angle_multiplier(shot_angle)
        
        # 3. Body part adjustment
        body_mult = self.BODY_PART_MULTIPLIERS.get(body_part, 1.0)
        
        # 4. Assist type adjustment
        assist_mult = self.ASSIST_TYPE_MULTIPLIERS.get(assist_type, 1.0)
        
        # 5. Game state adjustment
        state_mult = self.GAME_STATE_MULTIPLIERS.get(game_state, 1.0)
        
        # 6. Defensive pressure adjustment (0 = no pressure, 1 = high pressure)
        pressure_mult = 1.0 - (defensive_pressure * 0.3)  # Max %30 azalma
        
        # Composite xG
        xg = (base_xg * angle_mult * body_mult * 
              assist_mult * state_mult * pressure_mult)
        
        # Clamp to [0.01, 0.99]
        return max(0.01, min(0.99, xg))
    
    def estimate_team_xg_from_stats(
        self,
        team_stats: Dict,
        opponent_stats: Dict,
        is_home: bool = True
    ) -> Dict[str, float]:
        """
        Takım istatistiklerinden tahmini xG hesapla
        (API'den detaylı şut verileri gelmediğinde)
        
        Args:
            team_stats: Takım istatistikleri
            opponent_stats: Rakip takım istatistikleri
            is_home: Ev sahibi mi?
            
        Returns:
            {
                'xG': 1.85,
                'xGA': 1.20,
                'xG_difference': 0.65,
                'over_performance': 0.15,  # Gerçek goller - xG
                'components': {...}
            }
        """
        # Şut istatistiklerinden xG tahmini
        shots_on_target = team_stats.get('shots_on_target', 0)
        total_shots = team_stats.get('total_shots', 0)
        
        # Opponent defensive strength
        opponent_goals_conceded = opponent_stats.get('goals_conceded', 0)
        opponent_matches = opponent_stats.get('matches_played', 1)
        opponent_defensive_strength = opponent_goals_conceded / opponent_matches if opponent_matches > 0 else 1.2
        
        # Base xG calculation
        # Assumption: On target shots have higher xG
        if total_shots > 0:
            shot_accuracy = shots_on_target / total_shots
        else:
            shot_accuracy = 0.33  # Default
        
        # xG per shot (estimated)
        # High accuracy = better shot quality
        xg_per_shot = 0.08 + (shot_accuracy * 0.12)  # 0.08 - 0.20 arası
        
        # Total xG
        estimated_xg = total_shots * xg_per_shot
        
        # Adjust for opponent strength
        opponent_adjustment = opponent_defensive_strength / 1.2  # Normalize
        estimated_xg *= opponent_adjustment
        
        # Home advantage adjustment
        if is_home:
            estimated_xg *= 1.08
        
        # xG Against (tahmini)
        opponent_shots = opponent_stats.get('total_shots', 0)
        if opponent_shots > 0:
            opponent_accuracy = opponent_stats.get('shots_on_target', 0) / opponent_shots
        else:
            opponent_accuracy = 0.33
        
        xg_per_opponent_shot = 0.08 + (opponent_accuracy * 0.12)
        estimated_xga = opponent_shots * xg_per_opponent_shot
        
        # Team defensive strength adjustment
        team_goals_conceded = team_stats.get('goals_conceded', 0)
        team_matches = team_stats.get('matches_played', 1)
        team_defensive_strength = team_goals_conceded / team_matches if team_matches > 0 else 1.2
        team_adjustment = team_defensive_strength / 1.2
        estimated_xga *= team_adjustment
        
        # Over/under performance
        actual_goals = team_stats.get('goals_scored', 0)
        over_performance = actual_goals - estimated_xg
        
        return {
            'xG': round(estimated_xg, 2),
            'xGA': round(estimated_xga, 2),
            'xG_difference': round(estimated_xg - estimated_xga, 2),
            'over_performance': round(over_performance, 2),
            'components': {
                'shot_quality': round(xg_per_shot, 3),
                'opponent_adjustment': round(opponent_adjustment, 2),
                'defensive_quality': round(team_defensive_strength, 2)
            }
        }
    
    def calculate_match_xg(
        self,
        home_team_stats: Dict,
        away_team_stats: Dict,
        league_avg_goals: float = 2.7
    ) -> Dict:
        """
        Maç için her iki takımın xG'sini hesapla
        
        Returns:
            {
                'home_xG': 1.85,
                'away_xG': 1.35,
                'total_xG': 3.20,
                'prediction': {
                    'most_likely_score': '2-1',
                    'over_2.5_probability': 0.62,
                    'btts_probability': 0.58
                }
            }
        """
        # Home team xG
        home_xg_data = self.estimate_team_xg_from_stats(
            home_team_stats,
            away_team_stats,
            is_home=True
        )
        
        # Away team xG
        away_xg_data = self.estimate_team_xg_from_stats(
            away_team_stats,
            home_team_stats,
            is_home=False
        )
        
        home_xg = home_xg_data['xG']
        away_xg = away_xg_data['xG']
        total_xg = home_xg + away_xg
        
        # Over 2.5 probability (Poisson distribution approximation)
        over_2_5_prob = self._calculate_over_probability(total_xg, 2.5)
        
        # BTTS probability
        # Probability that both score >= 1
        home_scores_prob = 1 - math.exp(-home_xg)  # P(X >= 1) = 1 - P(X = 0)
        away_scores_prob = 1 - math.exp(-away_xg)
        btts_prob = home_scores_prob * away_scores_prob
        
        # Most likely score (simplified)
        home_goals_likely = round(home_xg)
        away_goals_likely = round(away_xg)
        
        return {
            'home_xG': home_xg,
            'away_xG': away_xg,
            'total_xG': round(total_xg, 2),
            'home_xG_breakdown': home_xg_data,
            'away_xG_breakdown': away_xg_data,
            'prediction': {
                'most_likely_score': f'{home_goals_likely}-{away_goals_likely}',
                'over_2.5_probability': round(over_2_5_prob, 2),
                'btts_probability': round(btts_prob, 2),
                'high_scoring_match': total_xg > 3.0
            }
        }
    
    def _get_xg_from_distance(self, distance: float) -> float:
        """Mesafeden base xG değeri"""
        for (min_dist, max_dist), xg_value in self.DISTANCE_XG_MAP.items():
            if min_dist <= distance < max_dist:
                return xg_value
        return 0.02  # Very far
    
    def _get_angle_multiplier(self, angle: float) -> float:
        """Açıdan multiplier"""
        if angle <= 15:
            return self.ANGLE_MULTIPLIERS['central']
        elif angle <= 30:
            return self.ANGLE_MULTIPLIERS['wide']
        else:
            return self.ANGLE_MULTIPLIERS['very_wide']
    
    def _calculate_over_probability(self, lambda_param: float, threshold: float) -> float:
        """
        Poisson distribution ile Over probability
        P(X > threshold) = 1 - P(X <= threshold)
        """
        # Simplified Poisson CDF for small integers
        prob_under = 0.0
        for k in range(int(threshold) + 1):
            prob_under += (math.exp(-lambda_param) * (lambda_param ** k)) / math.factorial(k)
        
        return 1 - prob_under


# Test
if __name__ == "__main__":
    calculator = ExpectedGoalsCalculator()
    
    # Test 1: Tek şut için xG
    print("🎯 Tek Şut için xG Hesaplama:")
    shot_xg = calculator.calculate_xg_from_shot_data(
        shot_distance=12,  # 12 metre
        shot_angle=10,     # 10 derece (merkez)
        body_part='right_foot',
        assist_type='through_ball',
        game_state='drawing',
        defensive_pressure=0.3
    )
    print(f"xG: {shot_xg:.3f}")
    print()
    
    # Test 2: Takım istatistiklerinden xG
    print("📊 Takım İstatistiklerinden xG Tahmini:")
    team_stats = {
        'shots_on_target': 6,
        'total_shots': 15,
        'goals_scored': 2,
        'goals_conceded': 1,
        'matches_played': 1
    }
    
    opponent_stats = {
        'shots_on_target': 3,
        'total_shots': 8,
        'goals_scored': 1,
        'goals_conceded': 2,
        'matches_played': 1
    }
    
    match_xg = calculator.calculate_match_xg(team_stats, opponent_stats)
    
    print(f"Ev Sahibi xG: {match_xg['home_xG']}")
    print(f"Deplasman xG: {match_xg['away_xG']}")
    print(f"Toplam xG: {match_xg['total_xG']}")
    print(f"\nTahmin:")
    print(f"  En Muhtemel Skor: {match_xg['prediction']['most_likely_score']}")
    print(f"  Over 2.5 Olasılığı: {match_xg['prediction']['over_2.5_probability']:.2%}")
    print(f"  BTTS Olasılığı: {match_xg['prediction']['btts_probability']:.2%}")
