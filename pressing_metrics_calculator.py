# -*- coding: utf-8 -*-
"""
Pressing Metrics Calculator
===========================
PPDA (Passes Per Defensive Action) ve diğer pressing metrikleri

Metrikler:
1. PPDA - Passes Per Defensive Action (düşük = yoğun press)
2. Pressing Intensity - Baskı yoğunluğu (0-100)
3. High Press Success - Yüksek baskı başarı oranı
4. Defensive Third Actions - Defansif bölge müdahaleleri
5. Counter Press - Kaybettikten sonraki ilk 5 saniyedeki baskı
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
import math

class PressingMetricsCalculator:
    """Pressing ve defansif metrikler hesaplayıcı"""
    
    # PPDA Benchmarks (dünya standartları)
    # Liverpool (Klopp era): ~8.0 (çok yoğun)
    # Manchester City (Guardiola): ~9.5 (yoğun)
    # League Average: ~11-13
    # Düşük press takımlar: ~15+
    PPDA_BENCHMARKS = {
        'very_high': (0, 8.0),      # Çok yoğun press
        'high': (8.0, 10.0),        # Yoğun press
        'medium': (10.0, 13.0),     # Orta seviye
        'low': (13.0, 16.0),        # Düşük press
        'very_low': (16.0, 100.0)   # Çok düşük press
    }
    
    # Pressing Intensity Weights
    INTENSITY_WEIGHTS = {
        'defensive_third': 0.20,    # Savunma 3'lüsü
        'middle_third': 0.40,       # Orta saha
        'attacking_third': 0.40     # Hücum 3'lüsü (high press)
    }
    
    def __init__(self):
        pass
    
    def calculate_ppda(
        self,
        opponent_passes: int,
        defensive_actions: int,
        match_count: int = 1
    ) -> Dict[str, float]:
        """
        PPDA (Passes Per Defensive Action) hesapla
        
        PPDA = Rakip Pasları / Defansif Müdahaleler
        
        Düşük PPDA = Yoğun pressing (Liverpool ~8, Man City ~9.5)
        Yüksek PPDA = Düşük pressing (Park the bus takımlar ~15+)
        
        Args:
            opponent_passes: Rakibin toplam pas sayısı
            defensive_actions: Defansif müdahaleler (tackle + interception + foul)
            match_count: Kaç maç ortalaması
            
        Returns:
            {
                'ppda': 10.5,
                'intensity_level': 'high',
                'percentile': 75,  # Lig içi yüzdelik
                'interpretation': 'Yoğun pressing'
            }
        """
        if defensive_actions == 0:
            # Defansif aksiyon yoksa (imkansız ama güvenlik için)
            return self._get_default_ppda()
        
        # PPDA hesapla
        ppda = opponent_passes / defensive_actions
        
        # Maç ortalaması al
        ppda_per_match = ppda / match_count if match_count > 0 else ppda
        
        # Intensity level belirle
        intensity_level = self._get_intensity_level(ppda_per_match)
        
        # Percentile hesapla (lig ortalaması 12 varsayımı ile)
        percentile = self._calculate_ppda_percentile(ppda_per_match)
        
        # Yorumlama
        interpretation = self._interpret_ppda(ppda_per_match)
        
        return {
            'ppda': round(ppda_per_match, 2),
            'intensity_level': intensity_level,
            'percentile': percentile,
            'interpretation': interpretation,
            'raw_data': {
                'opponent_passes': opponent_passes,
                'defensive_actions': defensive_actions,
                'match_count': match_count
            }
        }
    
    def calculate_pressing_intensity(
        self,
        defensive_actions_by_zone: Dict[str, int],
        total_opponent_possessions: int
    ) -> Dict[str, float]:
        """
        Pressing intensity (baskı yoğunluğu) hesapla
        
        Args:
            defensive_actions_by_zone: {
                'defensive_third': 45,
                'middle_third': 78,
                'attacking_third': 32
            }
            total_opponent_possessions: Rakibin toplam top kontrolü
            
        Returns:
            {
                'overall_intensity': 65.5,  # 0-100
                'high_press_percentage': 24.5,
                'zone_breakdown': {...}
            }
        """
        if total_opponent_possessions == 0:
            return self._get_default_intensity()
        
        # Her bölgedeki yoğunluk
        zone_intensities = {}
        total_weighted = 0.0
        
        for zone, actions in defensive_actions_by_zone.items():
            # Bu bölgedeki yoğunluk (%)
            zone_intensity = (actions / total_opponent_possessions) * 100
            zone_intensities[zone] = round(zone_intensity, 2)
            
            # Ağırlıklı toplam
            weight = self.INTENSITY_WEIGHTS.get(zone, 0.33)
            total_weighted += zone_intensity * weight
        
        # Genel yoğunluk skoru (0-100)
        overall_intensity = min(100, total_weighted)
        
        # High press yüzdesi (attacking third'deki aksiyon oranı)
        attacking_actions = defensive_actions_by_zone.get('attacking_third', 0)
        total_actions = sum(defensive_actions_by_zone.values())
        high_press_percentage = (attacking_actions / total_actions * 100) if total_actions > 0 else 0
        
        return {
            'overall_intensity': round(overall_intensity, 2),
            'high_press_percentage': round(high_press_percentage, 2),
            'zone_breakdown': zone_intensities,
            'classification': self._classify_intensity(overall_intensity)
        }
    
    def estimate_ppda_from_stats(
        self,
        team_stats: Dict,
        opponent_stats: Dict
    ) -> Dict[str, float]:
        """
        API istatistiklerinden PPDA tahmini yap
        (Detaylı veri yoksa tahminsel hesaplama)
        
        Args:
            team_stats: Takım istatistikleri
            opponent_stats: Rakip istatistikleri
            
        Returns:
            Estimated PPDA metrics
        """
        # Tahminsel hesaplama
        # Assumption: Her takım maç başına ~400-500 pas yapar
        # Defansif aksiyonlar: tackles + interceptions + fouls
        
        # Rakip pas tahmini (possession % bazlı)
        opponent_possession = opponent_stats.get('possession', 50)
        estimated_opponent_passes = (opponent_possession / 100) * 450  # Ortalama pas sayısı
        
        # Defansif aksiyonlar
        tackles = team_stats.get('tackles', 0)
        interceptions = team_stats.get('interceptions', 0)
        fouls = team_stats.get('fouls', 0)
        
        defensive_actions = tackles + interceptions + (fouls * 0.7)  # Fauller %70 ağırlıklı
        
        if defensive_actions == 0:
            defensive_actions = 15  # Minimum varsayım
        
        # PPDA hesapla
        ppda_result = self.calculate_ppda(
            opponent_passes=int(estimated_opponent_passes),
            defensive_actions=int(defensive_actions),
            match_count=1
        )
        
        # Tahmin olduğunu belirt
        ppda_result['is_estimated'] = True
        ppda_result['confidence'] = 0.65  # Orta güven seviyesi
        
        return ppda_result
    
    def calculate_counter_press_efficiency(
        self,
        possessions_lost: int,
        counter_press_attempts: int,
        successful_counter_presses: int
    ) -> Dict[str, float]:
        """
        Counter press (geri kazanım) verimliliği
        
        Args:
            possessions_lost: Kaybedilen top sayısı
            counter_press_attempts: Karşı baskı denemeleri
            successful_counter_presses: Başarılı karşı baskılar
            
        Returns:
            Counter press metrics
        """
        if possessions_lost == 0:
            return {
                'counter_press_rate': 0.0,
                'success_rate': 0.0,
                'efficiency_score': 0.0
            }
        
        # Karşı baskı oranı (kaybedilen topların yüzdesi)
        counter_press_rate = (counter_press_attempts / possessions_lost) * 100
        
        # Başarı oranı
        if counter_press_attempts > 0:
            success_rate = (successful_counter_presses / counter_press_attempts) * 100
        else:
            success_rate = 0.0
        
        # Verimlilik skoru (0-100)
        efficiency_score = (counter_press_rate * 0.5 + success_rate * 0.5)
        
        return {
            'counter_press_rate': round(counter_press_rate, 2),
            'success_rate': round(success_rate, 2),
            'efficiency_score': round(efficiency_score, 2),
            'classification': self._classify_counter_press(efficiency_score)
        }
    
    def calculate_comprehensive_pressing_score(
        self,
        ppda: float,
        pressing_intensity: float,
        high_press_percentage: float,
        counter_press_efficiency: float
    ) -> Dict[str, float]:
        """
        Kapsamlı pressing skoru (tüm metrikleri birleştir)
        
        Returns:
            {
                'overall_pressing_score': 78.5,  # 0-100
                'ranking': 'Elite',
                'components': {...}
            }
        """
        # PPDA'yı 0-100 skalasına çevir (düşük PPDA = yüksek skor)
        # PPDA 8 = 100, PPDA 16 = 0
        ppda_score = max(0, min(100, ((16 - ppda) / 8) * 100))
        
        # Composite score
        weights = {
            'ppda': 0.35,
            'intensity': 0.30,
            'high_press': 0.20,
            'counter_press': 0.15
        }
        
        overall_score = (
            ppda_score * weights['ppda'] +
            pressing_intensity * weights['intensity'] +
            high_press_percentage * weights['high_press'] +
            counter_press_efficiency * weights['counter_press']
        )
        
        # Ranking
        ranking = self._get_pressing_ranking(overall_score)
        
        return {
            'overall_pressing_score': round(overall_score, 2),
            'ranking': ranking,
            'components': {
                'ppda_score': round(ppda_score, 2),
                'intensity_score': round(pressing_intensity, 2),
                'high_press_score': round(high_press_percentage, 2),
                'counter_press_score': round(counter_press_efficiency, 2)
            },
            'weights': weights
        }
    
    # Helper methods
    
    def _get_intensity_level(self, ppda: float) -> str:
        """PPDA'dan yoğunluk seviyesi"""
        for level, (min_val, max_val) in self.PPDA_BENCHMARKS.items():
            if min_val <= ppda < max_val:
                return level
        return 'medium'
    
    def _calculate_ppda_percentile(self, ppda: float, league_avg: float = 12.0) -> int:
        """Lig içi yüzdelik hesapla"""
        # Basit tahmin: PPDA 8 = top 10%, PPDA 12 = median, PPDA 16 = bottom 10%
        if ppda <= 8:
            return 95
        elif ppda <= 10:
            return 75
        elif ppda <= 12:
            return 50
        elif ppda <= 14:
            return 25
        else:
            return 10
    
    def _interpret_ppda(self, ppda: float) -> str:
        """PPDA yorumlama"""
        if ppda < 8:
            return "Çok Yoğun Pressing (Liverpool/Klopp tarzı)"
        elif ppda < 10:
            return "Yoğun Pressing (Man City/Guardiola tarzı)"
        elif ppda < 13:
            return "Orta Seviye Pressing (Lig ortalaması)"
        elif ppda < 16:
            return "Düşük Pressing (Savunma odaklı)"
        else:
            return "Çok Düşük Pressing (Park the bus)"
    
    def _classify_intensity(self, intensity: float) -> str:
        """Intensity classification"""
        if intensity >= 80:
            return "Very High"
        elif intensity >= 60:
            return "High"
        elif intensity >= 40:
            return "Medium"
        elif intensity >= 20:
            return "Low"
        else:
            return "Very Low"
    
    def _classify_counter_press(self, efficiency: float) -> str:
        """Counter press classification"""
        if efficiency >= 75:
            return "Elite (Klopp Style)"
        elif efficiency >= 60:
            return "Excellent"
        elif efficiency >= 45:
            return "Good"
        elif efficiency >= 30:
            return "Average"
        else:
            return "Poor"
    
    def _get_pressing_ranking(self, score: float) -> str:
        """Overall pressing ranking"""
        if score >= 85:
            return "Elite (Top 5%)"
        elif score >= 70:
            return "Excellent (Top 20%)"
        elif score >= 55:
            return "Good (Top 40%)"
        elif score >= 40:
            return "Average (Middle 40%)"
        else:
            return "Below Average (Bottom 20%)"
    
    def _get_default_ppda(self) -> Dict:
        """Default PPDA values"""
        return {
            'ppda': 12.0,
            'intensity_level': 'medium',
            'percentile': 50,
            'interpretation': 'Orta Seviye Pressing',
            'raw_data': {}
        }
    
    def _get_default_intensity(self) -> Dict:
        """Default intensity values"""
        return {
            'overall_intensity': 50.0,
            'high_press_percentage': 30.0,
            'zone_breakdown': {
                'defensive_third': 33.3,
                'middle_third': 33.3,
                'attacking_third': 33.3
            },
            'classification': 'Medium'
        }


# Test
if __name__ == "__main__":
    calculator = PressingMetricsCalculator()
    
    print("🔥 Pressing Metrics Calculator Test\n")
    
    # Test 1: PPDA Calculation
    print("1️⃣ PPDA Test (Liverpool Style)")
    ppda_result = calculator.calculate_ppda(
        opponent_passes=320,
        defensive_actions=42,
        match_count=1
    )
    print(f"   PPDA: {ppda_result['ppda']}")
    print(f"   Level: {ppda_result['intensity_level']}")
    print(f"   Interpretation: {ppda_result['interpretation']}")
    print()
    
    # Test 2: Pressing Intensity
    print("2️⃣ Pressing Intensity Test")
    intensity_result = calculator.calculate_pressing_intensity(
        defensive_actions_by_zone={
            'defensive_third': 25,
            'middle_third': 45,
            'attacking_third': 38
        },
        total_opponent_possessions=150
    )
    print(f"   Overall Intensity: {intensity_result['overall_intensity']}")
    print(f"   High Press %: {intensity_result['high_press_percentage']}")
    print(f"   Classification: {intensity_result['classification']}")
    print()
    
    # Test 3: Comprehensive Score
    print("3️⃣ Comprehensive Pressing Score")
    comprehensive = calculator.calculate_comprehensive_pressing_score(
        ppda=8.5,
        pressing_intensity=72.0,
        high_press_percentage=35.0,
        counter_press_efficiency=68.0
    )
    print(f"   Overall Score: {comprehensive['overall_pressing_score']}")
    print(f"   Ranking: {comprehensive['ranking']}")
    print(f"   Components: {comprehensive['components']}")
