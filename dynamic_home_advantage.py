# -*- coding: utf-8 -*-
"""
Dynamic Home Advantage Calculator
=================================
Takım bazlı, dinamik ev sahibi avantajı hesaplama sistemi

Faktörler:
1. Team-specific home performance (Takımın ev performansı) - 50%
2. League average home advantage (Lig ortalaması) - 20%
3. Stadium factors (Stadyum faktörleri) - 15%
4. Recent home form (Son ev formu) - 15%
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
import math

class DynamicHomeAdvantageCalculator:
    """Dinamik ev sahibi avantajı hesaplayıcı"""
    
    # League-specific base home advantages (Lig bazlı varsayılan değerler)
    # Dünya istatistiklerine göre
    LEAGUE_BASE_ADVANTAGES = {
        39: 1.15,   # Premier League (İngiltere)
        140: 1.18,  # La Liga (İspanya)
        78: 1.12,   # Bundesliga (Almanya) - daha düşük (seyirci desteği dengeli)
        135: 1.20,  # Serie A (İtalya) - yüksek
        61: 1.16,   # Ligue 1 (Fransa)
        203: 1.22,  # Süper Lig (Türkiye) - çok yüksek (sıcak atmosfer)
        2: 1.10,    # Champions League (nötr saha etkisi)
        3: 1.10,    # Europa League
    }
    
    # Default if league not found
    DEFAULT_LEAGUE_ADVANTAGE = 1.15
    
    # Min/Max boundaries
    MIN_ADVANTAGE = 1.02
    MAX_ADVANTAGE = 1.35
    
    def __init__(self):
        pass
    
    def calculate_home_advantage(
        self,
        team_id: int,
        team_name: str,
        league_id: int,
        home_stats: Optional[Dict] = None,
        away_stats: Optional[Dict] = None,
        stadium_capacity: Optional[int] = None,
        avg_attendance: Optional[int] = None,
        recent_home_matches: Optional[List[Dict]] = None
    ) -> Dict[str, float]:
        """
        Takım bazlı ev sahibi avantajını hesapla
        
        Args:
            team_id: Takım ID
            team_name: Takım adı
            league_id: Lig ID
            home_stats: Ev sahibi istatistikleri {'wins': 10, 'draws': 3, 'losses': 2, 'goals_for': 30, 'goals_against': 12}
            away_stats: Deplasman istatistikleri {'wins': 5, 'draws': 5, 'losses': 5, 'goals_for': 18, 'goals_against': 18}
            stadium_capacity: Stadyum kapasitesi
            avg_attendance: Ortalama seyirci sayısı
            recent_home_matches: Son ev maçları
            
        Returns:
            {
                'home_advantage': 1.18,
                'components': {
                    'performance_based': 1.20,
                    'league_average': 1.15,
                    'stadium_factor': 1.22,
                    'recent_form': 1.15
                },
                'confidence': 0.85
            }
        """
        # 1. League base advantage (Lig bazlı temel avantaj)
        league_advantage = self.LEAGUE_BASE_ADVANTAGES.get(
            league_id, 
            self.DEFAULT_LEAGUE_ADVANTAGE
        )
        
        # 2. Performance-based advantage (Performans bazlı)
        performance_advantage = self._calculate_performance_advantage(
            home_stats, 
            away_stats
        )
        
        # 3. Stadium factor (Stadyum faktörü)
        stadium_factor = self._calculate_stadium_factor(
            stadium_capacity,
            avg_attendance,
            league_id
        )
        
        # 4. Recent home form (Son ev formu)
        recent_form_factor = self._calculate_recent_home_form(
            recent_home_matches
        )
        
        # Weighted composite (Ağırlıklı birleştirme)
        weights = {
            'performance': 0.50,
            'league': 0.20,
            'stadium': 0.15,
            'form': 0.15
        }
        
        composite_advantage = (
            performance_advantage * weights['performance'] +
            league_advantage * weights['league'] +
            stadium_factor * weights['stadium'] +
            recent_form_factor * weights['form']
        )
        
        # Sınırlara uygula
        final_advantage = max(
            self.MIN_ADVANTAGE, 
            min(self.MAX_ADVANTAGE, composite_advantage)
        )
        
        # Confidence (güvenilirlik - ne kadar veri var?)
        confidence = self._calculate_confidence(
            home_stats, 
            away_stats, 
            recent_home_matches
        )
        
        return {
            'home_advantage': round(final_advantage, 3),
            'components': {
                'performance_based': round(performance_advantage, 3),
                'league_average': round(league_advantage, 3),
                'stadium_factor': round(stadium_factor, 3),
                'recent_form': round(recent_form_factor, 3)
            },
            'confidence': round(confidence, 2),
            'interpretation': self._get_interpretation(final_advantage)
        }
    
    def _calculate_performance_advantage(
        self,
        home_stats: Optional[Dict],
        away_stats: Optional[Dict]
    ) -> float:
        """
        Ev ve deplasman performansını karşılaştır
        """
        if not home_stats or not away_stats:
            return self.DEFAULT_LEAGUE_ADVANTAGE
        
        # Puanlardan karşılaştırma
        home_matches = home_stats.get('wins', 0) + home_stats.get('draws', 0) + home_stats.get('losses', 0)
        away_matches = away_stats.get('wins', 0) + away_stats.get('draws', 0) + away_stats.get('losses', 0)
        
        if home_matches == 0 or away_matches == 0:
            return self.DEFAULT_LEAGUE_ADVANTAGE
        
        # Puan ortalamaları
        home_points = (home_stats.get('wins', 0) * 3 + home_stats.get('draws', 0)) / home_matches
        away_points = (away_stats.get('wins', 0) * 3 + away_stats.get('draws', 0)) / away_matches
        
        # Gol ortalamaları
        home_goals_for = home_stats.get('goals_for', 0) / home_matches
        away_goals_for = away_stats.get('goals_for', 0) / away_matches
        
        home_goals_against = home_stats.get('goals_against', 0) / home_matches
        away_goals_against = away_stats.get('goals_against', 0) / away_matches
        
        # Puan oranı
        if away_points > 0:
            points_ratio = home_points / away_points
        else:
            points_ratio = 2.0 if home_points > 0 else 1.0
        
        # Gol farkı oranı
        if away_goals_for > 0:
            goals_for_ratio = home_goals_for / away_goals_for
        else:
            goals_for_ratio = 1.5 if home_goals_for > 0 else 1.0
        
        if home_goals_against > 0:
            goals_against_ratio = away_goals_against / home_goals_against
        else:
            goals_against_ratio = 1.5 if away_goals_against < home_goals_against else 1.0
        
        # Composite advantage
        advantage = (
            points_ratio * 0.5 +
            goals_for_ratio * 0.25 +
            goals_against_ratio * 0.25
        )
        
        # Normalize to reasonable range (1.02 - 1.35)
        advantage = max(1.02, min(1.35, advantage))
        
        return advantage
    
    def _calculate_stadium_factor(
        self,
        capacity: Optional[int],
        attendance: Optional[int],
        league_id: int
    ) -> float:
        """
        Stadyum ve seyirci faktörü
        Büyük, dolu stadyumlar daha fazla avantaj sağlar
        """
        if not capacity or not attendance:
            # Veri yoksa lig ortalamasını kullan
            return self.LEAGUE_BASE_ADVANTAGES.get(
                league_id, 
                self.DEFAULT_LEAGUE_ADVANTAGE
            )
        
        # Doluluk oranı
        attendance_rate = min(1.0, attendance / capacity)
        
        # Stadyum büyüklüğü faktörü (normalize edilmiş)
        # 10k = small, 50k = medium, 80k+ = large
        if capacity < 20000:
            size_factor = 0.95  # Küçük stadyum - daha az avantaj
        elif capacity < 50000:
            size_factor = 1.00  # Orta stadyum
        elif capacity < 70000:
            size_factor = 1.05  # Büyük stadyum
        else:
            size_factor = 1.08  # Çok büyük stadyum
        
        # Doluluk faktörü
        # %30 doluluk = 0.90, %100 doluluk = 1.10
        occupancy_factor = 0.90 + (attendance_rate * 0.20)
        
        # Composite
        stadium_advantage = size_factor * occupancy_factor
        
        # Lig bazlı ayarlama
        league_base = self.LEAGUE_BASE_ADVANTAGES.get(
            league_id, 
            self.DEFAULT_LEAGUE_ADVANTAGE
        )
        
        final = league_base * stadium_advantage
        
        return max(self.MIN_ADVANTAGE, min(self.MAX_ADVANTAGE, final))
    
    def _calculate_recent_home_form(
        self,
        recent_matches: Optional[List[Dict]]
    ) -> float:
        """
        Son ev maçlarının formu
        """
        if not recent_matches or len(recent_matches) < 3:
            return self.DEFAULT_LEAGUE_ADVANTAGE
        
        # Son 5 ev maçını al
        matches = recent_matches[:5]
        
        wins = 0
        total_gd = 0  # Goal difference
        
        for match in matches:
            gf = match.get('goals_for', 0)
            ga = match.get('goals_against', 0)
            
            if gf > ga:
                wins += 1
            
            total_gd += (gf - ga)
        
        # Win rate
        win_rate = wins / len(matches)
        
        # Average goal difference
        avg_gd = total_gd / len(matches)
        
        # Form factor
        # 0% kazanma = 1.02, 100% kazanma = 1.30
        # Gol farkı da etkili
        base_factor = 1.02 + (win_rate * 0.28)
        
        # Gol farkı ayarlaması (-2 to +2 arası anlamlı)
        gd_adjustment = max(-0.05, min(0.05, avg_gd * 0.02))
        
        form_factor = base_factor + gd_adjustment
        
        return max(self.MIN_ADVANTAGE, min(self.MAX_ADVANTAGE, form_factor))
    
    def _calculate_confidence(
        self,
        home_stats: Optional[Dict],
        away_stats: Optional[Dict],
        recent_matches: Optional[List[Dict]]
    ) -> float:
        """
        Hesaplamanın güvenilirliği (0-1)
        Daha fazla veri = daha yüksek güven
        """
        confidence_factors = []
        
        # Home stats var mı?
        if home_stats and home_stats.get('wins', 0) + home_stats.get('draws', 0) + home_stats.get('losses', 0) >= 10:
            confidence_factors.append(1.0)
        elif home_stats:
            matches = home_stats.get('wins', 0) + home_stats.get('draws', 0) + home_stats.get('losses', 0)
            confidence_factors.append(min(1.0, matches / 10))
        else:
            confidence_factors.append(0.0)
        
        # Away stats var mı?
        if away_stats and away_stats.get('wins', 0) + away_stats.get('draws', 0) + away_stats.get('losses', 0) >= 10:
            confidence_factors.append(1.0)
        elif away_stats:
            matches = away_stats.get('wins', 0) + away_stats.get('draws', 0) + away_stats.get('losses', 0)
            confidence_factors.append(min(1.0, matches / 10))
        else:
            confidence_factors.append(0.0)
        
        # Recent matches var mı?
        if recent_matches and len(recent_matches) >= 5:
            confidence_factors.append(1.0)
        elif recent_matches:
            confidence_factors.append(min(1.0, len(recent_matches) / 5))
        else:
            confidence_factors.append(0.0)
        
        # Ortalama güven
        return sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.0
    
    def _get_interpretation(self, advantage: float) -> str:
        """Avantaj yorumu"""
        if advantage >= 1.25:
            return "Çok Güçlü Ev Avantajı"
        elif advantage >= 1.18:
            return "Güçlü Ev Avantajı"
        elif advantage >= 1.12:
            return "Orta Seviye Ev Avantajı"
        elif advantage >= 1.08:
            return "Düşük Ev Avantajı"
        else:
            return "Minimal Ev Avantajı"


# Backward compatibility function
def get_team_specific_home_advantage(
    team_id: int,
    league_id: int,
    home_stats: Optional[Dict] = None,
    away_stats: Optional[Dict] = None
) -> float:
    """
    LEGACY FUNCTION - Geriye uyumluluk için
    """
    calculator = DynamicHomeAdvantageCalculator()
    result = calculator.calculate_home_advantage(
        team_id=team_id,
        team_name="",
        league_id=league_id,
        home_stats=home_stats,
        away_stats=away_stats
    )
    return result['home_advantage']


# Test
if __name__ == "__main__":
    calculator = DynamicHomeAdvantageCalculator()
    
    # Test case: Galatasaray (Süper Lig)
    test_home_stats = {
        'wins': 12,
        'draws': 3,
        'losses': 2,
        'goals_for': 38,
        'goals_against': 15
    }
    
    test_away_stats = {
        'wins': 6,
        'draws': 5,
        'losses': 6,
        'goals_for': 22,
        'goals_against': 20
    }
    
    test_recent_home = [
        {'goals_for': 3, 'goals_against': 1},
        {'goals_for': 2, 'goals_against': 0},
        {'goals_for': 1, 'goals_against': 1},
        {'goals_for': 4, 'goals_against': 0},
        {'goals_for': 2, 'goals_against': 1},
    ]
    
    result = calculator.calculate_home_advantage(
        team_id=645,
        team_name="Galatasaray",
        league_id=203,  # Süper Lig
        home_stats=test_home_stats,
        away_stats=test_away_stats,
        stadium_capacity=52000,
        avg_attendance=48000,
        recent_home_matches=test_recent_home
    )
    
    print("🏟️ Dinamik Ev Sahibi Avantajı Analizi")
    print(f"Takım: Galatasaray")
    print(f"Ev Avantajı: {result['home_advantage']}")
    print(f"Yorum: {result['interpretation']}")
    print(f"Güven: {result['confidence']:.2%}")
    print(f"\nBileşenler:")
    for key, value in result['components'].items():
        print(f"  {key}: {value}")
