# -*- coding: utf-8 -*-
"""
Advanced Metrics Manager
========================
Tüm gelişmiş metrikleri tek bir yerden yönet

Modüller:
1. Advanced Form Calculator
2. Dynamic Home Advantage Calculator
3. Expected Goals Calculator
4. Pressing Metrics Calculator
5. Progressive Metrics Calculator
6. Expected Assists Calculator
"""

from typing import Dict, List, Optional, Any
from datetime import datetime

# Import all calculators
try:
    from advanced_form_calculator import AdvancedFormCalculator
    FORM_CALC_AVAILABLE = True
except ImportError:
    FORM_CALC_AVAILABLE = False
    AdvancedFormCalculator = None

try:
    from dynamic_home_advantage import DynamicHomeAdvantageCalculator
    HOME_ADV_CALC_AVAILABLE = True
except ImportError:
    HOME_ADV_CALC_AVAILABLE = False
    DynamicHomeAdvantageCalculator = None

try:
    from expected_goals_calculator import ExpectedGoalsCalculator
    XG_CALC_AVAILABLE = True
except ImportError:
    XG_CALC_AVAILABLE = False
    ExpectedGoalsCalculator = None

try:
    from pressing_metrics_calculator import PressingMetricsCalculator
    PRESSING_CALC_AVAILABLE = True
except ImportError:
    PRESSING_CALC_AVAILABLE = False
    PressingMetricsCalculator = None

try:
    from progressive_metrics_calculator import ProgressiveMetricsCalculator
    PROGRESSIVE_CALC_AVAILABLE = True
except ImportError:
    PROGRESSIVE_CALC_AVAILABLE = False
    ProgressiveMetricsCalculator = None

try:
    from expected_assists_calculator import ExpectedAssistsCalculator
    XA_CALC_AVAILABLE = True
except ImportError:
    XA_CALC_AVAILABLE = False
    ExpectedAssistsCalculator = None


class AdvancedMetricsManager:
    """Tüm gelişmiş metrikleri yöneten merkezi sınıf"""
    
    def __init__(self):
        """Initialize all available calculators"""
        self.form_calc = AdvancedFormCalculator() if FORM_CALC_AVAILABLE else None
        self.home_adv_calc = DynamicHomeAdvantageCalculator() if HOME_ADV_CALC_AVAILABLE else None
        self.xg_calc = ExpectedGoalsCalculator() if XG_CALC_AVAILABLE else None
        self.pressing_calc = PressingMetricsCalculator() if PRESSING_CALC_AVAILABLE else None
        self.progressive_calc = ProgressiveMetricsCalculator() if PROGRESSIVE_CALC_AVAILABLE else None
        self.xa_calc = ExpectedAssistsCalculator() if XA_CALC_AVAILABLE else None
        
        # Availability check
        self.available_modules = self._check_availability()
    
    def _check_availability(self) -> Dict[str, bool]:
        """Check which modules are available"""
        return {
            'advanced_form': FORM_CALC_AVAILABLE,
            'dynamic_home_advantage': HOME_ADV_CALC_AVAILABLE,
            'expected_goals': XG_CALC_AVAILABLE,
            'pressing_metrics': PRESSING_CALC_AVAILABLE,
            'progressive_metrics': PROGRESSIVE_CALC_AVAILABLE,
            'expected_assists': XA_CALC_AVAILABLE
        }
    
    def get_comprehensive_team_analysis(
        self,
        team_id: int,
        team_name: str,
        league_id: int,
        team_stats: Dict,
        opponent_stats: Dict,
        recent_matches: Optional[List[Dict]] = None,
        home_stats: Optional[Dict] = None,
        away_stats: Optional[Dict] = None,
        is_home: bool = True
    ) -> Dict[str, Any]:
        """
        Kapsamlı takım analizi - tüm metrikleri birleştir
        
        Returns:
            {
                'form_analysis': {...},
                'home_advantage': {...},
                'expected_goals': {...},
                'pressing': {...},
                'progressive': {...},
                'chance_creation': {...},
                'overall_rating': 78.5,
                'strengths': [...],
                'weaknesses': [...]
            }
        """
        analysis = {}
        
        # 1. Form Analysis
        if self.form_calc and recent_matches:
            try:
                form_result = self.form_calc.calculate_advanced_form(
                    matches=recent_matches,
                    location_filter='home' if is_home else 'away',
                    num_matches=10
                )
                analysis['form_analysis'] = form_result
            except Exception as e:
                print(f"⚠️ Form analysis error: {e}")
                analysis['form_analysis'] = None
        
        # 2. Home Advantage (if home team)
        if self.home_adv_calc and is_home:
            try:
                home_adv_result = self.home_adv_calc.calculate_home_advantage(
                    team_id=team_id,
                    team_name=team_name,
                    league_id=league_id,
                    home_stats=home_stats,
                    away_stats=away_stats
                )
                analysis['home_advantage'] = home_adv_result
            except Exception as e:
                print(f"⚠️ Home advantage error: {e}")
                analysis['home_advantage'] = None
        
        # 3. Expected Goals
        if self.xg_calc:
            try:
                if is_home:
                    xg_result = self.xg_calc.calculate_match_xg(
                        home_team_stats=team_stats,
                        away_team_stats=opponent_stats
                    )
                    analysis['expected_goals'] = {
                        'team_xG': xg_result['home_xG'],
                        'opponent_xG': xg_result['away_xG'],
                        'prediction': xg_result['prediction']
                    }
                else:
                    xg_result = self.xg_calc.calculate_match_xg(
                        home_team_stats=opponent_stats,
                        away_team_stats=team_stats
                    )
                    analysis['expected_goals'] = {
                        'team_xG': xg_result['away_xG'],
                        'opponent_xG': xg_result['home_xG'],
                        'prediction': xg_result['prediction']
                    }
            except Exception as e:
                print(f"⚠️ xG calculation error: {e}")
                analysis['expected_goals'] = None
        
        # 4. Pressing Metrics
        if self.pressing_calc:
            try:
                pressing_result = self.pressing_calc.estimate_ppda_from_stats(
                    team_stats=team_stats,
                    opponent_stats=opponent_stats
                )
                analysis['pressing'] = pressing_result
            except Exception as e:
                print(f"⚠️ Pressing metrics error: {e}")
                analysis['pressing'] = None
        
        # 5. Progressive Metrics
        if self.progressive_calc:
            try:
                progressive_result = self.progressive_calc.estimate_progressive_metrics_from_stats(
                    team_stats=team_stats,
                    match_count=1
                )
                analysis['progressive'] = progressive_result
            except Exception as e:
                print(f"⚠️ Progressive metrics error: {e}")
                analysis['progressive'] = None
        
        # 6. Expected Assists
        if self.xa_calc:
            try:
                xa_result = self.xa_calc.estimate_team_xa_from_stats(
                    team_stats=team_stats,
                    match_count=1
                )
                analysis['chance_creation'] = xa_result
            except Exception as e:
                print(f"⚠️ xA calculation error: {e}")
                analysis['chance_creation'] = None
        
        # 7. Overall Rating & SWOT Analysis
        analysis['overall_rating'] = self._calculate_overall_rating(analysis)
        analysis['strengths'] = self._identify_strengths(analysis)
        analysis['weaknesses'] = self._identify_weaknesses(analysis)
        
        return analysis
    
    def _calculate_overall_rating(self, analysis: Dict) -> float:
        """Calculate overall team rating (0-100) from all metrics"""
        scores = []
        
        # Form
        if analysis.get('form_analysis'):
            scores.append(analysis['form_analysis'].get('form_score', 50))
        
        # xG
        if analysis.get('expected_goals'):
            xg = analysis['expected_goals'].get('team_xG', 1.5)
            # Normalize xG to 0-100 (2.5 xG = 100)
            scores.append(min(100, (xg / 2.5) * 100))
        
        # Pressing
        if analysis.get('pressing'):
            ppda = analysis['pressing'].get('ppda', 12)
            # Convert PPDA to score (lower is better)
            # PPDA 8 = 100, PPDA 16 = 0
            pressing_score = max(0, min(100, ((16 - ppda) / 8) * 100))
            scores.append(pressing_score)
        
        # Progressive
        if analysis.get('progressive'):
            prog_data = analysis['progressive'].get('progressive_passing', {})
            prog_score = prog_data.get('quality_score', 50)
            scores.append(prog_score)
        
        # Chance Creation
        if analysis.get('chance_creation'):
            chance_quality = analysis['chance_creation'].get('chance_quality', 50)
            scores.append(chance_quality)
        
        # Average
        if scores:
            return round(sum(scores) / len(scores), 2)
        else:
            return 50.0
    
    def _identify_strengths(self, analysis: Dict) -> List[str]:
        """Identify team strengths from metrics"""
        strengths = []
        
        # Form
        if analysis.get('form_analysis'):
            if analysis['form_analysis'].get('form_score', 0) >= 70:
                strengths.append(f"Mükemmel Form ({analysis['form_analysis']['form_string']})")
        
        # Home Advantage
        if analysis.get('home_advantage'):
            if analysis['home_advantage'].get('home_advantage', 1.0) >= 1.20:
                strengths.append("Güçlü Ev Sahibi Avantajı")
        
        # Pressing
        if analysis.get('pressing'):
            if analysis['pressing'].get('ppda', 15) <= 10:
                strengths.append("Yoğun Pressing")
        
        # Progressive Play
        if analysis.get('progressive'):
            prog_data = analysis['progressive'].get('progressive_passing', {})
            if prog_data.get('quality_score', 0) >= 70:
                strengths.append("İleri Oyun Kalitesi")
        
        # Chance Creation
        if analysis.get('chance_creation'):
            if analysis['chance_creation'].get('chance_quality', 0) >= 70:
                strengths.append("Yüksek Şans Yaratma")
        
        return strengths if strengths else ["Dengeli Performans"]
    
    def _identify_weaknesses(self, analysis: Dict) -> List[str]:
        """Identify team weaknesses from metrics"""
        weaknesses = []
        
        # Form
        if analysis.get('form_analysis'):
            if analysis['form_analysis'].get('form_score', 100) <= 35:
                weaknesses.append(f"Zayıf Form ({analysis['form_analysis']['form_string']})")
        
        # Pressing
        if analysis.get('pressing'):
            if analysis['pressing'].get('ppda', 10) >= 15:
                weaknesses.append("Düşük Pressing Yoğunluğu")
        
        # Progressive Play
        if analysis.get('progressive'):
            prog_data = analysis['progressive'].get('progressive_passing', {})
            if prog_data.get('quality_score', 100) <= 35:
                weaknesses.append("Zayıf İleri Oyun")
        
        # Chance Creation
        if analysis.get('chance_creation'):
            if analysis['chance_creation'].get('chance_quality', 100) <= 35:
                weaknesses.append("Düşük Şans Yaratma")
        
        return weaknesses if weaknesses else ["Belirgin Zayıflık Yok"]
    
    def get_match_prediction_with_advanced_metrics(
        self,
        home_analysis: Dict,
        away_analysis: Dict
    ) -> Dict[str, Any]:
        """
        İki takımın advanced metrics'lerini kullanarak maç tahmini
        
        Returns:
            Enhanced prediction with all modern metrics
        """
        prediction = {
            'home_team': {},
            'away_team': {},
            'match_prediction': {},
            'key_factors': []
        }
        
        # Home team summary
        prediction['home_team'] = {
            'overall_rating': home_analysis.get('overall_rating', 50),
            'strengths': home_analysis.get('strengths', []),
            'weaknesses': home_analysis.get('weaknesses', [])
        }
        
        # Away team summary
        prediction['away_team'] = {
            'overall_rating': away_analysis.get('overall_rating', 50),
            'strengths': away_analysis.get('strengths', []),
            'weaknesses': away_analysis.get('weaknesses', [])
        }
        
        # Match prediction (simplified)
        home_rating = home_analysis.get('overall_rating', 50)
        away_rating = away_analysis.get('overall_rating', 50)
        
        # Home advantage bonus
        home_adv = home_analysis.get('home_advantage', {}).get('home_advantage', 1.15)
        home_rating_adjusted = home_rating * home_adv
        
        # Win probabilities
        total = home_rating_adjusted + away_rating + 30  # +30 for draw baseline
        
        home_win_prob = (home_rating_adjusted / total) * 100
        away_win_prob = (away_rating / total) * 100
        draw_prob = 100 - home_win_prob - away_win_prob
        
        prediction['match_prediction'] = {
            'home_win': round(home_win_prob, 2),
            'draw': round(draw_prob, 2),
            'away_win': round(away_win_prob, 2),
            'most_likely': 'home' if home_win_prob > max(draw_prob, away_win_prob) else 'away' if away_win_prob > draw_prob else 'draw'
        }
        
        # Key factors
        if home_rating > away_rating + 10:
            prediction['key_factors'].append("Ev sahibi genel kalite avantajına sahip")
        elif away_rating > home_rating + 10:
            prediction['key_factors'].append("Deplasman takımı kalite avantajına sahip")
        
        return prediction
    
    def print_availability_status(self):
        """Print which modules are available"""
        print("📊 Advanced Metrics Manager - Modül Durumu\n")
        for module, available in self.available_modules.items():
            status = "✅ Aktif" if available else "❌ Yok"
            print(f"   {module}: {status}")
        print()


# Test
if __name__ == "__main__":
    manager = AdvancedMetricsManager()
    
    # Status check
    manager.print_availability_status()
    
    # Test comprehensive analysis
    print("🔬 Kapsamlı Takım Analizi Test\n")
    
    test_team_stats = {
        'shots_on_target': 6,
        'total_shots': 15,
        'goals_scored': 2,
        'goals_conceded': 1,
        'possession': 58,
        'total_passes': 520,
        'key_passes': 12,
        'assists': 2,
        'dribbles_success': 8,
        'tackles': 18,
        'interceptions': 12,
        'fouls': 10,
        'matches_played': 1
    }
    
    test_opponent_stats = {
        'shots_on_target': 3,
        'total_shots': 8,
        'goals_scored': 1,
        'goals_conceded': 2,
        'possession': 42,
        'total_passes': 380,
        'matches_played': 1
    }
    
    test_recent_matches = [
        {'goals_for': 2, 'goals_against': 1, 'location': 'home'},
        {'goals_for': 3, 'goals_against': 0, 'location': 'home'},
        {'goals_for': 1, 'goals_against': 1, 'location': 'home'},
        {'goals_for': 2, 'goals_against': 0, 'location': 'home'},
        {'goals_for': 1, 'goals_against': 2, 'location': 'home'},
    ]
    
    analysis = manager.get_comprehensive_team_analysis(
        team_id=645,
        team_name="Galatasaray",
        league_id=203,
        team_stats=test_team_stats,
        opponent_stats=test_opponent_stats,
        recent_matches=test_recent_matches,
        is_home=True
    )
    
    print(f"Overall Rating: {analysis['overall_rating']}")
    print(f"\nStrengths:")
    for s in analysis['strengths']:
        print(f"  ✅ {s}")
    print(f"\nWeaknesses:")
    for w in analysis['weaknesses']:
        print(f"  ⚠️ {w}")
