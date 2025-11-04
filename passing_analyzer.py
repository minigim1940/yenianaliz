# -*- coding: utf-8 -*-
"""
Passing Network Analyzer - PHASE 3.3
=====================================
Pas ağı ve hücum organizasyonu analizi
"""

from typing import Dict, List, Optional, Any


class PassingAnalyzer:
    """Pas verilerini analiz eden sınıf"""
    
    # Quality thresholds
    EXCELLENT_ACCURACY = 85.0
    GOOD_ACCURACY = 75.0
    AVERAGE_ACCURACY = 65.0
    
    def __init__(self):
        """Initialize analyzer"""
        pass
    
    def analyze_passing_performance(
        self,
        match_stats: Optional[Dict] = None,
        team_stats: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Pas performansını analiz et
        
        Args:
            match_stats: /fixtures/statistics API response
            team_stats: Team season statistics
        
        Returns:
            {
                'total_passes': 450,
                'accurate_passes': 380,
                'pass_accuracy': 84.4,
                'key_passes': 12,
                'progressive_passes_est': 45,
                'passes_per_match': 450.0,
                'long_balls': 35,
                'crosses': 18,
                'cross_accuracy': 25.0,
                'passing_quality': 'excellent' | 'good' | 'average' | 'poor',
                'creativity_score': 75.0,
                'build_up_quality': 'high' | 'medium' | 'low'
            }
        """
        result = {
            'total_passes': 0,
            'accurate_passes': 0,
            'pass_accuracy': 0.0,
            'key_passes': 0,
            'progressive_passes_est': 0,
            'passes_per_match': 0.0,
            'long_balls': 0,
            'crosses': 0,
            'cross_accuracy': 0.0,
            'passing_quality': 'average',
            'creativity_score': 50.0,
            'build_up_quality': 'medium',
            'possession_pct': 50.0
        }
        
        # Extract from match stats
        if match_stats:
            stats_list = match_stats.get('statistics', [])
            for stat in stats_list:
                stat_type = stat.get('type', '')
                value = stat.get('value')
                
                if value is None:
                    continue
                
                if stat_type == 'Total passes':
                    result['total_passes'] = int(value)
                elif stat_type == 'Passes accurate':
                    result['accurate_passes'] = int(value)
                elif stat_type == 'Passes %':
                    # Value might be "84%" or 84
                    if isinstance(value, str):
                        result['pass_accuracy'] = float(value.strip('%'))
                    else:
                        result['pass_accuracy'] = float(value)
                elif stat_type == 'Ball Possession':
                    if isinstance(value, str):
                        result['possession_pct'] = float(value.strip('%'))
                    else:
                        result['possession_pct'] = float(value)
        
        # Calculate pass accuracy if not provided
        if result['pass_accuracy'] == 0.0 and result['total_passes'] > 0:
            result['pass_accuracy'] = round(
                (result['accurate_passes'] / result['total_passes']) * 100, 1
            )
        
        # Estimate advanced metrics
        if result['total_passes'] > 0:
            # Progressive passes estimation (10-15% of total passes)
            result['progressive_passes_est'] = int(result['total_passes'] * 0.12)
            
            # Key passes estimation (2-3% of total)
            result['key_passes'] = int(result['total_passes'] * 0.025)
            
            # Long balls estimation (8-10% of total)
            result['long_balls'] = int(result['total_passes'] * 0.09)
            
            # Crosses estimation (4-5% of total)
            result['crosses'] = int(result['total_passes'] * 0.045)
            
            # Cross accuracy (typically 20-30%)
            result['cross_accuracy'] = 25.0
        
        # Passing quality assessment
        accuracy = result['pass_accuracy']
        if accuracy >= self.EXCELLENT_ACCURACY:
            result['passing_quality'] = 'excellent'
        elif accuracy >= self.GOOD_ACCURACY:
            result['passing_quality'] = 'good'
        elif accuracy >= self.AVERAGE_ACCURACY:
            result['passing_quality'] = 'average'
        else:
            result['passing_quality'] = 'poor'
        
        # Creativity score (0-100)
        # Based on: pass accuracy (40%), possession (30%), key passes (30%)
        accuracy_score = min(100, (accuracy / 90) * 100)
        possession_score = (result['possession_pct'] / 70) * 100
        key_pass_score = min(100, (result['key_passes'] / 15) * 100)
        
        result['creativity_score'] = round(
            accuracy_score * 0.4 + possession_score * 0.3 + key_pass_score * 0.3,
            1
        )
        
        # Build-up quality
        if result['pass_accuracy'] >= 80 and result['possession_pct'] >= 55:
            result['build_up_quality'] = 'high'
        elif result['pass_accuracy'] >= 70 and result['possession_pct'] >= 45:
            result['build_up_quality'] = 'medium'
        else:
            result['build_up_quality'] = 'low'
        
        return result
    
    def compare_passing_styles(
        self,
        home_passing: Dict,
        away_passing: Dict
    ) -> Dict[str, Any]:
        """
        İki takımın pas stilini karşılaştır
        
        Returns:
            {
                'possession_winner': 'home' | 'away' | 'balanced',
                'accuracy_winner': 'home' | 'away' | 'balanced',
                'creativity_winner': 'home' | 'away' | 'balanced',
                'passing_dominance': 'home' | 'away' | 'balanced',
                'style_difference': 'possession vs counter' | 'balanced',
                'key_insights': [...]
            }
        """
        comparison = {
            'possession_winner': 'balanced',
            'accuracy_winner': 'balanced',
            'creativity_winner': 'home' if home_passing['creativity_score'] > away_passing['creativity_score'] else 'away',
            'passing_dominance': 'balanced',
            'style_difference': 'balanced',
            'key_insights': []
        }
        
        # Possession comparison
        poss_diff = home_passing['possession_pct'] - away_passing['possession_pct']
        if poss_diff > 15:
            comparison['possession_winner'] = 'home'
            comparison['key_insights'].append(
                f"Ev sahibi top kontrolünde çok dominant ({home_passing['possession_pct']:.0f}%)"
            )
        elif poss_diff < -15:
            comparison['possession_winner'] = 'away'
            comparison['key_insights'].append(
                f"Deplasman top kontrolünde dominant ({away_passing['possession_pct']:.0f}%)"
            )
        
        # Accuracy comparison
        acc_diff = home_passing['pass_accuracy'] - away_passing['pass_accuracy']
        if acc_diff > 10:
            comparison['accuracy_winner'] = 'home'
            comparison['key_insights'].append("Ev sahibi daha isabetli paslar yapıyor")
        elif acc_diff < -10:
            comparison['accuracy_winner'] = 'away'
            comparison['key_insights'].append("Deplasman daha isabetli paslar yapıyor")
        
        # Overall passing dominance
        home_total_score = (
            home_passing['possession_pct'] * 0.4 +
            home_passing['pass_accuracy'] * 0.3 +
            home_passing['creativity_score'] * 0.3
        )
        away_total_score = (
            away_passing['possession_pct'] * 0.4 +
            away_passing['pass_accuracy'] * 0.3 +
            away_passing['creativity_score'] * 0.3
        )
        
        total_diff = home_total_score - away_total_score
        if total_diff > 15:
            comparison['passing_dominance'] = 'home'
        elif total_diff < -15:
            comparison['passing_dominance'] = 'away'
        
        # Style analysis
        home_poss = home_passing['possession_pct']
        away_poss = away_passing['possession_pct']
        
        if home_poss > 60 and away_poss < 40:
            comparison['style_difference'] = 'possession (home) vs counter (away)'
            comparison['key_insights'].append("Ev sahibi kontrol, deplasman kontra savaşı")
        elif away_poss > 60 and home_poss < 40:
            comparison['style_difference'] = 'counter (home) vs possession (away)'
            comparison['key_insights'].append("Deplasman kontrol, ev sahibi kontra savaşı")
        
        return comparison
    
    def get_passing_recommendations(self, passing_analysis: Dict) -> List[str]:
        """
        Pas analizine göre öneriler
        """
        recommendations = []
        
        # Low possession
        if passing_analysis['possession_pct'] < 40:
            recommendations.append("⚠️ Düşük top kontrolü - Orta sahayı güçlendir")
        
        # Poor accuracy
        if passing_analysis['pass_accuracy'] < 70:
            recommendations.append("🎯 Düşük pas isabeti - Basit paslarla oyna")
        
        # Low creativity
        if passing_analysis['creativity_score'] < 40:
            recommendations.append("💡 Yaratıcılık eksik - Daha fazla key pass gerekli")
        
        # Excellent passing
        if passing_analysis['passing_quality'] == 'excellent':
            recommendations.append("✅ Mükemmel pas performansı - Oyun kontrolde")
        
        # High possession but low creativity
        if (passing_analysis['possession_pct'] > 60 and 
            passing_analysis['creativity_score'] < 50):
            recommendations.append("🔄 Yüksek kontrol ama etkisiz - Son paslar gerekli")
        
        return recommendations if recommendations else ["✅ Dengeli pas oyunu"]


# Test
if __name__ == "__main__":
    print("🧪 PASSING ANALYZER TEST\n")
    print("="*80)
    
    # Sample match stats
    sample_stats = {
        'statistics': [
            {'type': 'Total passes', 'value': 450},
            {'type': 'Passes accurate', 'value': 380},
            {'type': 'Passes %', 'value': '84%'},
            {'type': 'Ball Possession', 'value': '58%'}
        ]
    }
    
    analyzer = PassingAnalyzer()
    
    # Analyze
    result = analyzer.analyze_passing_performance(match_stats=sample_stats)
    
    print("📊 Passing Analysis Results:")
    print(f"   Total Passes: {result['total_passes']}")
    print(f"   Pass Accuracy: {result['pass_accuracy']:.1f}%")
    print(f"   Possession: {result['possession_pct']:.1f}%")
    print(f"   Key Passes (est): {result['key_passes']}")
    print(f"   Progressive Passes (est): {result['progressive_passes_est']}")
    print(f"   Passing Quality: {result['passing_quality'].upper()}")
    print(f"   Creativity Score: {result['creativity_score']:.1f}/100")
    print(f"   Build-up Quality: {result['build_up_quality'].upper()}")
    
    print("\n💡 Recommendations:")
    recs = analyzer.get_passing_recommendations(result)
    for rec in recs:
        print(f"   {rec}")
    
    print("\n" + "="*80)
    print("✅ TEST COMPLETE")
