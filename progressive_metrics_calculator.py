# -*- coding: utf-8 -*-
"""
Progressive Metrics Calculator
==============================
Progressive passes, carries ve field tilt metrikleri

Metrikler:
1. Progressive Passes - İleriye doğru etkili paslar
2. Progressive Carries - Topla ileriye taşımalar
3. Field Tilt - Sahanın hangi yarısında oynanıyor
4. Final Third Entries - Son 3'lü girişleri
5. Build-up Quality - Oyun kurma kalitesi
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
import math

class ProgressiveMetricsCalculator:
    """Progressive passing ve build-up metrikleri"""
    
    # Progressive pass kriterleri (StatsBomb standardı)
    # Pass mesafesi ve ilerleme miktarına göre
    PROGRESSIVE_THRESHOLDS = {
        'own_third': {
            'min_distance': 30,      # metre (kendi 3'lüsünden)
            'min_progression': 10    # metre ilerleme
        },
        'middle_third': {
            'min_distance': 15,      # metre (orta sahadan)
            'min_progression': 10    # metre ilerleme
        },
        'final_third': {
            'min_distance': 10,      # metre (son 3'lüden)
            'min_progression': 10    # metre ilerleme
        }
    }
    
    # Field zones (saha bölgeleri)
    FIELD_ZONES = {
        'defensive_third': (0, 35),      # Savunma 3'lüsü
        'middle_third': (35, 70),        # Orta saha
        'final_third': (70, 105)         # Son 3'lü
    }
    
    def __init__(self):
        pass
    
    def calculate_progressive_passes(
        self,
        total_passes: int,
        forward_passes: int,
        passes_into_final_third: int,
        key_passes: int,
        match_count: int = 1
    ) -> Dict[str, float]:
        """
        Progressive pass metriklerini hesapla
        
        Progressive Pass: Kaleye en az 10m yaklaştıran veya 
        son 3'lüye giren her pas
        
        Args:
            total_passes: Toplam pas sayısı
            forward_passes: İleri yönlü paslar
            passes_into_final_third: Son 3'lüye paslar
            key_passes: Anahtar paslar (şans yaratan)
            match_count: Kaç maç ortalaması
            
        Returns:
            {
                'progressive_passes_per_match': 45.5,
                'progressive_percentage': 12.5,
                'quality_score': 78.3,
                'final_third_penetration': 15.2
            }
        """
        if total_passes == 0:
            return self._get_default_progressive()
        
        # Tahmini progressive pass sayısı
        # Varsayım: Forward passes'in %60'ı + Final third passes'in %100'ü progressive
        estimated_progressive = (forward_passes * 0.60) + passes_into_final_third
        
        # Maç başına ortalama
        progressive_per_match = estimated_progressive / match_count if match_count > 0 else estimated_progressive
        
        # Progressive yüzdesi
        progressive_percentage = (estimated_progressive / total_passes) * 100
        
        # Kalite skoru (key passes oranı)
        # Yüksek quality = daha fazla key pass
        quality_score = self._calculate_pass_quality(
            key_passes, 
            estimated_progressive, 
            total_passes
        )
        
        # Son 3'lü penetrasyon (maç başına)
        final_third_penetration = passes_into_final_third / match_count if match_count > 0 else passes_into_final_third
        
        return {
            'progressive_passes_per_match': round(progressive_per_match, 2),
            'progressive_percentage': round(progressive_percentage, 2),
            'quality_score': round(quality_score, 2),
            'final_third_penetration': round(final_third_penetration, 2),
            'interpretation': self._interpret_progressive_passing(progressive_per_match),
            'raw_data': {
                'total_passes': total_passes,
                'estimated_progressive': estimated_progressive,
                'match_count': match_count
            }
        }
    
    def calculate_field_tilt(
        self,
        possession_in_zones: Dict[str, float],
        touches_in_zones: Dict[str, int],
        passes_in_zones: Dict[str, int]
    ) -> Dict[str, float]:
        """
        Field Tilt (saha eğilimi) hesapla
        
        Field Tilt: Oyunun hangi yarıda geçtiğini gösterir
        Pozitif değer = Rakip yarısında oynanıyor (attacking)
        Negatif değer = Kendi yarısında oynanıyor (defending)
        
        Args:
            possession_in_zones: {
                'defensive_third': 25.5,  # %
                'middle_third': 35.0,
                'final_third': 39.5
            }
            touches_in_zones: Her bölgedeki top dokunuşu
            passes_in_zones: Her bölgedeki paslar
            
        Returns:
            {
                'field_tilt_score': 15.5,  # -50 to +50
                'dominant_zone': 'final_third',
                'attacking_percentage': 65.0,
                'interpretation': 'Dominant in opponent half'
            }
        """
        # Weighted field tilt score
        # Final third = +1, Middle = 0, Defensive = -1
        zone_weights = {
            'defensive_third': -1.0,
            'middle_third': 0.0,
            'final_third': 1.0
        }
        
        # Possession bazlı tilt
        possession_tilt = sum(
            possession_in_zones.get(zone, 0) * weight
            for zone, weight in zone_weights.items()
        )
        
        # Touches bazlı tilt
        total_touches = sum(touches_in_zones.values())
        if total_touches > 0:
            touch_tilt = sum(
                (touches_in_zones.get(zone, 0) / total_touches * 100) * weight
                for zone, weight in zone_weights.items()
            )
        else:
            touch_tilt = 0.0
        
        # Composite tilt score (-50 to +50)
        field_tilt_score = (possession_tilt * 0.6 + touch_tilt * 0.4) * 0.5
        
        # Dominant zone
        dominant_zone = max(possession_in_zones, key=possession_in_zones.get)
        
        # Attacking percentage (final + middle thirds)
        attacking_percentage = (
            possession_in_zones.get('final_third', 0) + 
            possession_in_zones.get('middle_third', 0)
        )
        
        # Interpretation
        interpretation = self._interpret_field_tilt(field_tilt_score)
        
        return {
            'field_tilt_score': round(field_tilt_score, 2),
            'dominant_zone': dominant_zone,
            'attacking_percentage': round(attacking_percentage, 2),
            'zone_distribution': possession_in_zones,
            'interpretation': interpretation
        }
    
    def calculate_build_up_quality(
        self,
        progressive_passes: int,
        final_third_entries: int,
        possession_losses: int,
        goals_scored: int,
        shots: int
    ) -> Dict[str, float]:
        """
        Build-up quality (oyun kurma kalitesi) hesapla
        
        Kaliteli build-up:
        1. Yüksek progressive pass oranı
        2. Çok final third girişi
        3. Az top kaybı
        4. Build-up'tan gol/şut
        
        Returns:
            {
                'build_up_quality_score': 75.5,  # 0-100
                'efficiency': 68.0,
                'penetration_rate': 12.5,
                'conversion_rate': 15.0
            }
        """
        if progressive_passes == 0:
            return self._get_default_build_up()
        
        # 1. Efficiency (top kaybı başına progressive pass)
        if possession_losses > 0:
            efficiency = (progressive_passes / possession_losses) * 100
            efficiency = min(100, efficiency)  # Cap at 100
        else:
            efficiency = 100.0
        
        # 2. Penetration rate (final third girişi / progressive pass)
        if progressive_passes > 0:
            penetration_rate = (final_third_entries / progressive_passes) * 100
        else:
            penetration_rate = 0.0
        
        # 3. Conversion rate (gol+şut / final third girişi)
        if final_third_entries > 0:
            conversion_rate = ((goals_scored + shots) / final_third_entries) * 100
        else:
            conversion_rate = 0.0
        
        # Build-up quality score (composite)
        quality_score = (
            efficiency * 0.40 +
            penetration_rate * 0.35 +
            conversion_rate * 0.25
        )
        quality_score = min(100, quality_score)
        
        return {
            'build_up_quality_score': round(quality_score, 2),
            'efficiency': round(efficiency, 2),
            'penetration_rate': round(penetration_rate, 2),
            'conversion_rate': round(conversion_rate, 2),
            'classification': self._classify_build_up(quality_score)
        }
    
    def estimate_progressive_metrics_from_stats(
        self,
        team_stats: Dict,
        match_count: int = 1
    ) -> Dict[str, float]:
        """
        API istatistiklerinden progressive metrikleri tahmin et
        
        Args:
            team_stats: Takım istatistikleri
            match_count: Kaç maç
            
        Returns:
            Comprehensive progressive metrics
        """
        # Paslar
        total_passes = team_stats.get('total_passes', 0)
        pass_accuracy = team_stats.get('pass_accuracy', 75) / 100
        
        # Tahmini forward passes (%40'ı forward)
        forward_passes = int(total_passes * 0.40)
        
        # Final third passes tahmini (%15'i final third)
        final_third_passes = int(total_passes * 0.15)
        
        # Key passes
        key_passes = team_stats.get('key_passes', int(total_passes * 0.03))
        
        # Progressive passes hesapla
        progressive_result = self.calculate_progressive_passes(
            total_passes=total_passes,
            forward_passes=forward_passes,
            passes_into_final_third=final_third_passes,
            key_passes=key_passes,
            match_count=match_count
        )
        
        # Field tilt tahmini (possession bazlı)
        possession = team_stats.get('possession', 50)
        
        # Tahmini zone distribution
        if possession > 55:  # Dominant
            zone_possession = {
                'defensive_third': 20.0,
                'middle_third': 35.0,
                'final_third': 45.0
            }
        elif possession < 45:  # Defensive
            zone_possession = {
                'defensive_third': 45.0,
                'middle_third': 35.0,
                'final_third': 20.0
            }
        else:  # Balanced
            zone_possession = {
                'defensive_third': 30.0,
                'middle_third': 40.0,
                'final_third': 30.0
            }
        
        # Tahmini touches (possession bazlı)
        estimated_touches = int(possession * 6)  # ~300 touch for 50% possession
        zone_touches = {
            'defensive_third': int(estimated_touches * zone_possession['defensive_third'] / 100),
            'middle_third': int(estimated_touches * zone_possession['middle_third'] / 100),
            'final_third': int(estimated_touches * zone_possession['final_third'] / 100)
        }
        
        zone_passes = {
            'defensive_third': int(total_passes * zone_possession['defensive_third'] / 100),
            'middle_third': int(total_passes * zone_possession['middle_third'] / 100),
            'final_third': int(total_passes * zone_possession['final_third'] / 100)
        }
        
        field_tilt = self.calculate_field_tilt(
            possession_in_zones=zone_possession,
            touches_in_zones=zone_touches,
            passes_in_zones=zone_passes
        )
        
        # Build-up quality
        shots = team_stats.get('shots_total', 0)
        goals = team_stats.get('goals_scored', 0)
        possession_losses = team_stats.get('possession_lost', int(total_passes * 0.20))
        
        build_up = self.calculate_build_up_quality(
            progressive_passes=int(progressive_result['progressive_passes_per_match'] * match_count),
            final_third_entries=final_third_passes,
            possession_losses=possession_losses,
            goals_scored=goals,
            shots=shots
        )
        
        return {
            'progressive_passing': progressive_result,
            'field_tilt': field_tilt,
            'build_up_quality': build_up,
            'is_estimated': True,
            'confidence': 0.70
        }
    
    # Helper methods
    
    def _calculate_pass_quality(
        self, 
        key_passes: int, 
        progressive_passes: float, 
        total_passes: int
    ) -> float:
        """Pass quality score (0-100)"""
        if total_passes == 0:
            return 50.0
        
        # Key pass ratio
        key_pass_ratio = (key_passes / total_passes) * 100
        
        # Progressive ratio
        progressive_ratio = (progressive_passes / total_passes) * 100
        
        # Quality score
        quality = (key_pass_ratio * 30 + progressive_ratio * 70)
        
        return min(100, quality)
    
    def _interpret_progressive_passing(self, progressive_per_match: float) -> str:
        """Progressive passing interpretation"""
        if progressive_per_match >= 60:
            return "Elite Progressive Passing (Man City style)"
        elif progressive_per_match >= 45:
            return "Excellent Progressive Passing"
        elif progressive_per_match >= 30:
            return "Good Progressive Passing"
        elif progressive_per_match >= 20:
            return "Average Progressive Passing"
        else:
            return "Limited Progressive Passing"
    
    def _interpret_field_tilt(self, tilt_score: float) -> str:
        """Field tilt interpretation"""
        if tilt_score >= 20:
            return "Dominant in Opponent Half (High Pressure)"
        elif tilt_score >= 10:
            return "Attacking Tendency"
        elif tilt_score >= -10:
            return "Balanced Play"
        elif tilt_score >= -20:
            return "Defensive Tendency"
        else:
            return "Deep Defensive Block"
    
    def _classify_build_up(self, quality_score: float) -> str:
        """Build-up quality classification"""
        if quality_score >= 80:
            return "Elite (Barcelona/Man City level)"
        elif quality_score >= 65:
            return "Excellent"
        elif quality_score >= 50:
            return "Good"
        elif quality_score >= 35:
            return "Average"
        else:
            return "Poor"
    
    def _get_default_progressive(self) -> Dict:
        """Default progressive values"""
        return {
            'progressive_passes_per_match': 30.0,
            'progressive_percentage': 10.0,
            'quality_score': 50.0,
            'final_third_penetration': 10.0,
            'interpretation': 'Average Progressive Passing',
            'raw_data': {}
        }
    
    def _get_default_build_up(self) -> Dict:
        """Default build-up values"""
        return {
            'build_up_quality_score': 50.0,
            'efficiency': 50.0,
            'penetration_rate': 30.0,
            'conversion_rate': 25.0,
            'classification': 'Average'
        }


# Test
if __name__ == "__main__":
    calculator = ProgressiveMetricsCalculator()
    
    print("⚡ Progressive Metrics Calculator Test\n")
    
    # Test 1: Progressive Passes
    print("1️⃣ Progressive Passes Test (Man City Style)")
    prog_result = calculator.calculate_progressive_passes(
        total_passes=650,
        forward_passes=280,
        passes_into_final_third=95,
        key_passes=18,
        match_count=1
    )
    print(f"   Progressive Passes/Match: {prog_result['progressive_passes_per_match']}")
    print(f"   Progressive %: {prog_result['progressive_percentage']}%")
    print(f"   Quality Score: {prog_result['quality_score']}")
    print(f"   Interpretation: {prog_result['interpretation']}")
    print()
    
    # Test 2: Field Tilt
    print("2️⃣ Field Tilt Test (Attacking Team)")
    tilt_result = calculator.calculate_field_tilt(
        possession_in_zones={
            'defensive_third': 20.0,
            'middle_third': 35.0,
            'final_third': 45.0
        },
        touches_in_zones={
            'defensive_third': 60,
            'middle_third': 120,
            'final_third': 150
        },
        passes_in_zones={
            'defensive_third': 100,
            'middle_third': 250,
            'final_third': 300
        }
    )
    print(f"   Field Tilt Score: {tilt_result['field_tilt_score']}")
    print(f"   Dominant Zone: {tilt_result['dominant_zone']}")
    print(f"   Attacking %: {tilt_result['attacking_percentage']}%")
    print(f"   Interpretation: {tilt_result['interpretation']}")
    print()
    
    # Test 3: Build-up Quality
    print("3️⃣ Build-up Quality Test")
    buildup_result = calculator.calculate_build_up_quality(
        progressive_passes=55,
        final_third_entries=28,
        possession_losses=45,
        goals_scored=2,
        shots=15
    )
    print(f"   Build-up Quality Score: {buildup_result['build_up_quality_score']}")
    print(f"   Efficiency: {buildup_result['efficiency']}")
    print(f"   Penetration Rate: {buildup_result['penetration_rate']}%")
    print(f"   Classification: {buildup_result['classification']}")
