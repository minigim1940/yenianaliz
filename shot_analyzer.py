# -*- coding: utf-8 -*-
"""
Shot Analyzer - PHASE 3.3
==========================
Şut analizi ve xG per shot hesaplama
"""

from typing import Dict, List, Optional, Any
from collections import Counter


class ShotAnalyzer:
    """Şut verilerini analiz eden sınıf"""
    
    # xG values by shot type and location
    XG_BASE_VALUES = {
        'inside_box': 0.15,
        'outside_box': 0.05,
        'penalty': 0.76,
        'header': 0.08,
        'free_kick': 0.04
    }
    
    def __init__(self):
        """Initialize analyzer"""
        pass
    
    def analyze_match_shots(
        self,
        match_events: Optional[List[Dict]] = None,
        match_stats: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Maç şutlarını analiz et
        
        Args:
            match_events: /fixtures/events API response
            match_stats: /fixtures/statistics API response
        
        Returns:
            {
                'total_shots': 15,
                'shots_on_target': 6,
                'shots_off_target': 4,
                'blocked_shots': 5,
                'inside_box': 10,
                'outside_box': 5,
                'shot_accuracy': 40.0,
                'xg_total': 1.8,
                'xg_per_shot': 0.12,
                'shot_types': {...},
                'shot_quality': 'high' | 'medium' | 'low'
            }
        """
        result = {
            'total_shots': 0,
            'shots_on_target': 0,
            'shots_off_target': 0,
            'blocked_shots': 0,
            'inside_box': 0,
            'outside_box': 0,
            'shot_accuracy': 0.0,
            'xg_total': 0.0,
            'xg_per_shot': 0.0,
            'shot_types': {},
            'shot_quality': 'medium',
            'goals_scored': 0,
            'conversion_rate': 0.0
        }
        
        # Method 1: From match_stats (daha yaygın)
        if match_stats:
            stats_list = match_stats.get('statistics', [])
            for stat in stats_list:
                stat_type = stat.get('type', '')
                value = stat.get('value')
                
                if value is None or value == 0:
                    continue
                
                if stat_type == 'Total Shots':
                    result['total_shots'] = int(value)
                elif stat_type == 'Shots on Goal':
                    result['shots_on_target'] = int(value)
                elif stat_type == 'Shots off Goal':
                    result['shots_off_target'] = int(value)
                elif stat_type == 'Blocked Shots':
                    result['blocked_shots'] = int(value)
                elif stat_type == 'Shots insidebox':
                    result['inside_box'] = int(value)
                elif stat_type == 'Shots outsidebox':
                    result['outside_box'] = int(value)
        
        # Method 2: From events (daha detaylı ama nadiren kullanılabilir)
        if match_events:
            goal_events = [e for e in match_events if e.get('type') == 'Goal']
            result['goals_scored'] = len(goal_events)
            
            # Shot type analysis from comments
            shot_types = []
            for event in match_events:
                if event.get('type') in ['Goal', 'Var']:  # VAR can indicate shot
                    comment = event.get('comments', '') or event.get('detail', '')
                    shot_types.append(comment)
            
            result['shot_types'] = dict(Counter(shot_types))
        
        # Calculate derived metrics
        if result['total_shots'] > 0:
            # Shot accuracy
            result['shot_accuracy'] = round(
                (result['shots_on_target'] / result['total_shots']) * 100, 1
            )
            
            # xG calculation (simplified)
            inside_xg = result['inside_box'] * self.XG_BASE_VALUES['inside_box']
            outside_xg = result['outside_box'] * self.XG_BASE_VALUES['outside_box']
            result['xg_total'] = round(inside_xg + outside_xg, 2)
            
            # xG per shot
            result['xg_per_shot'] = round(result['xg_total'] / result['total_shots'], 3)
            
            # Conversion rate
            if result['goals_scored'] > 0:
                result['conversion_rate'] = round(
                    (result['goals_scored'] / result['total_shots']) * 100, 1
                )
        
        # Shot quality assessment
        if result['shot_accuracy'] >= 50 or result['xg_per_shot'] >= 0.15:
            result['shot_quality'] = 'high'
        elif result['shot_accuracy'] >= 35 or result['xg_per_shot'] >= 0.10:
            result['shot_quality'] = 'medium'
        else:
            result['shot_quality'] = 'low'
        
        return result
    
    def compare_teams_shooting(
        self,
        home_shots: Dict,
        away_shots: Dict
    ) -> Dict[str, Any]:
        """
        İki takımın şut performansını karşılaştır
        
        Returns:
            {
                'shot_dominance': 'home' | 'away' | 'balanced',
                'quality_winner': 'home' | 'away' | 'balanced',
                'home_advantage': +0.15,  # xG difference
                'key_insights': [...]
            }
        """
        comparison = {
            'shot_dominance': 'balanced',
            'quality_winner': 'balanced',
            'home_advantage': 0.0,
            'key_insights': []
        }
        
        # Quantity comparison
        shot_diff = home_shots['total_shots'] - away_shots['total_shots']
        if shot_diff > 5:
            comparison['shot_dominance'] = 'home'
            comparison['key_insights'].append(
                f"Ev sahibi {shot_diff} şut fazla atmış"
            )
        elif shot_diff < -5:
            comparison['shot_dominance'] = 'away'
            comparison['key_insights'].append(
                f"Deplasman {abs(shot_diff)} şut fazla atmış"
            )
        
        # Quality comparison
        home_quality_score = (
            home_shots['shot_accuracy'] * 0.4 +
            home_shots['xg_per_shot'] * 1000 * 0.6
        )
        away_quality_score = (
            away_shots['shot_accuracy'] * 0.4 +
            away_shots['xg_per_shot'] * 1000 * 0.6
        )
        
        quality_diff = home_quality_score - away_quality_score
        if quality_diff > 10:
            comparison['quality_winner'] = 'home'
            comparison['key_insights'].append(
                "Ev sahibi daha kaliteli şutlar atmış"
            )
        elif quality_diff < -10:
            comparison['quality_winner'] = 'away'
            comparison['key_insights'].append(
                "Deplasman daha kaliteli şutlar atmış"
            )
        
        # xG advantage
        comparison['home_advantage'] = round(
            home_shots['xg_total'] - away_shots['xg_total'], 2
        )
        
        # Efficiency insights
        if home_shots['conversion_rate'] > away_shots['conversion_rate'] * 1.5:
            comparison['key_insights'].append(
                "Ev sahibi çok daha etkili (yüksek konversiyon)"
            )
        elif away_shots['conversion_rate'] > home_shots['conversion_rate'] * 1.5:
            comparison['key_insights'].append(
                "Deplasman çok daha etkili (yüksek konversiyon)"
            )
        
        return comparison
    
    def get_shooting_recommendations(self, shot_analysis: Dict) -> List[str]:
        """
        Şut analizine göre öneriler ver
        
        Returns:
            List of tactical recommendations
        """
        recommendations = []
        
        # Low shot count
        if shot_analysis['total_shots'] < 8:
            recommendations.append(
                "⚠️ Düşük şut sayısı - Daha fazla hücum gerekli"
            )
        
        # Poor accuracy
        if shot_analysis['shot_accuracy'] < 30:
            recommendations.append(
                "🎯 Düşük isabet - Şut pozisyonu iyileştirmeli"
            )
        
        # Too many long shots
        if shot_analysis['outside_box'] > shot_analysis['inside_box']:
            recommendations.append(
                "📏 Çok fazla uzak şut - Ceza alanına girme eksik"
            )
        
        # High blocked shots
        total_shots = shot_analysis['total_shots']
        if total_shots > 0 and shot_analysis['blocked_shots'] / total_shots > 0.4:
            recommendations.append(
                "🛡️ Çok bloklanıyor - Açı yaratma gerekli"
            )
        
        # Good shooting
        if shot_analysis['shot_quality'] == 'high':
            recommendations.append(
                "✅ Mükemmel şut kalitesi - Gol gelme ihtimali yüksek"
            )
        
        # High xG but low goals
        if (shot_analysis['xg_total'] > 1.5 and 
            shot_analysis['goals_scored'] < shot_analysis['xg_total'] * 0.6):
            recommendations.append(
                "💔 xG'ye göre az gol - Bitiricilik sorun olabilir"
            )
        
        return recommendations if recommendations else ["✅ Dengeli şut performansı"]


# Test
if __name__ == "__main__":
    print("🧪 SHOT ANALYZER TEST\n")
    print("="*80)
    
    # Sample match stats
    sample_stats = {
        'statistics': [
            {'type': 'Total Shots', 'value': 15},
            {'type': 'Shots on Goal', 'value': 6},
            {'type': 'Shots off Goal', 'value': 4},
            {'type': 'Blocked Shots', 'value': 5},
            {'type': 'Shots insidebox', 'value': 10},
            {'type': 'Shots outsidebox', 'value': 5}
        ]
    }
    
    analyzer = ShotAnalyzer()
    
    # Analyze
    result = analyzer.analyze_match_shots(match_stats=sample_stats)
    
    print("📊 Shot Analysis Results:")
    print(f"   Total Shots: {result['total_shots']}")
    print(f"   On Target: {result['shots_on_target']} ({result['shot_accuracy']:.1f}%)")
    print(f"   Inside Box: {result['inside_box']}")
    print(f"   Outside Box: {result['outside_box']}")
    print(f"   xG Total: {result['xg_total']}")
    print(f"   xG per Shot: {result['xg_per_shot']}")
    print(f"   Shot Quality: {result['shot_quality'].upper()}")
    
    print("\n💡 Recommendations:")
    recs = analyzer.get_shooting_recommendations(result)
    for rec in recs:
        print(f"   {rec}")
    
    print("\n" + "="*80)
    print("✅ TEST COMPLETE")
