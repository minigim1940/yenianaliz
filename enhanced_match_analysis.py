# -*- coding: utf-8 -*-
"""
Enhanced Match Analysis Integration
====================================
Yeni advanced metrics'leri mevcut analysis_logic.py'ye entegre eden wrapper
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

# Import main analysis
try:
    from analysis_logic import *
    ANALYSIS_LOGIC_AVAILABLE = True
except ImportError:
    ANALYSIS_LOGIC_AVAILABLE = False

# Import advanced metrics manager
try:
    from advanced_metrics_manager import AdvancedMetricsManager
    ADVANCED_METRICS_AVAILABLE = True
except ImportError:
    ADVANCED_METRICS_AVAILABLE = False
    AdvancedMetricsManager = None


def get_enhanced_match_analysis(
    api_key: str,
    base_url: str,
    home_team_id: int,
    away_team_id: int,
    home_team_name: str,
    away_team_name: str,
    league_id: int,
    season: int,
    fixture_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Gelişmiş maç analizi - tüm yeni metrikleri içerir
    
    Args:
        api_key: API key
        base_url: API base URL
        home_team_id: Ev sahibi takım ID
        away_team_id: Deplasman takımı ID
        home_team_name: Ev sahibi takım adı
        away_team_name: Deplasman takımı adı
        league_id: Lig ID
        season: Sezon
        fixture_id: Maç ID (optional)
    
    Returns:
        {
            'classic_analysis': {...},  # Mevcut sistem
            'advanced_analysis': {
                'home_team': {...},
                'away_team': {...},
                'prediction': {...}
            },
            'combined_prediction': {...}
        }
    """
    result = {
        'classic_analysis': None,
        'advanced_analysis': None,
        'combined_prediction': None,
        'timestamp': datetime.now().isoformat()
    }
    
    # 1. Classic Analysis (mevcut sistem) - API'den gerçek veriler
    home_stats_raw = None
    away_stats_raw = None
    
    if ANALYSIS_LOGIC_AVAILABLE:
        try:
            # Get basic stats from API
            home_stats_raw = calculate_general_stats_v2(
                api_key=api_key,
                base_url=base_url,
                team_id=home_team_id,
                league_id=league_id,
                season=season,
                skip_api_limit=True  # API limiti üst seviyede yönetiliyor
            )
            
            away_stats_raw = calculate_general_stats_v2(
                api_key=api_key,
                base_url=base_url,
                team_id=away_team_id,
                league_id=league_id,
                season=season,
                skip_api_limit=True
            )
            
            result['classic_analysis'] = {
                'home_stats': home_stats_raw,
                'away_stats': away_stats_raw
            }
        except Exception as e:
            print(f"⚠️ Classic analysis error: {e}")
            import traceback
            traceback.print_exc()
    
    # 2. Advanced Metrics Analysis
    if ADVANCED_METRICS_AVAILABLE and home_stats_raw and away_stats_raw:
        try:
            metrics_manager = AdvancedMetricsManager()
            
            # API verilerinden advanced metrics için gerekli veriyi çıkar
            # calculate_general_stats_v2 -> {'home': {...}, 'away': {...}, 'team_specific_home_adv': ...}
            home_loc_stats = home_stats_raw.get('home', {})
            away_loc_stats = away_stats_raw.get('away', {})
            
            # Get recent matches for form analysis - GERÇEK API VERİSİ
            import api_utils
            from fixture_parser import parse_fixtures_to_matches, get_opponent_strengths_from_api
            
            print(f"📡 {home_team_name} için son maçlar çekiliyor...")
            home_recent_response, home_error = api_utils.make_api_request(
                api_key=api_key,
                base_url=base_url,
                endpoint="fixtures",
                params={'team': home_team_id, 'last': 10, 'status': 'FT'},
                skip_limit=True
            )
            
            print(f"📡 {away_team_name} için son maçlar çekiliyor...")
            away_recent_response, away_error = api_utils.make_api_request(
                api_key=api_key,
                base_url=base_url,
                endpoint="fixtures",
                params={'team': away_team_id, 'last': 10, 'status': 'FT'},
                skip_limit=True
            )
            
            # Parse fixtures to match format
            home_recent = []
            away_recent = []
            
            if home_recent_response and not home_error:
                home_recent = parse_fixtures_to_matches(home_recent_response, home_team_id)
                print(f"✅ {home_team_name}: {len(home_recent)} maç parse edildi")
            else:
                print(f"⚠️ {home_team_name} fixtures hatası: {home_error}")
            
            if away_recent_response and not away_error:
                away_recent = parse_fixtures_to_matches(away_recent_response, away_team_id)
                print(f"✅ {away_team_name}: {len(away_recent)} maç parse edildi")
            else:
                print(f"⚠️ {away_team_name} fixtures hatası: {away_error}")
            
            # Prepare data for advanced analysis
            home_team_stats_dict = {
                'shots_on_target': 5,  # TODO: API coverage expansion
                'total_shots': 12,
                'goals_scored': home_loc_stats.get('Ort. Gol ATILAN', 1.5),
                'goals_conceded': home_loc_stats.get('Ort. Gol YENEN', 1.2),
                'possession': 50,  # TODO
                'total_passes': 450,  # TODO
                'key_passes': 10,  # TODO
                'assists': 1,  # TODO
                'matches_played': 10,
                'stability_score': home_loc_stats.get('Istikrar_Puani', 50.0)
            }
            
            away_team_stats_dict = {
                'shots_on_target': 5,
                'total_shots': 12,
                'goals_scored': away_loc_stats.get('Ort. Gol ATILAN', 1.5),
                'goals_conceded': away_loc_stats.get('Ort. Gol YENEN', 1.2),
                'possession': 50,
                'total_passes': 450,
                'key_passes': 10,
                'assists': 1,
                'matches_played': 10,
                'stability_score': away_loc_stats.get('Istikrar_Puani', 45.0)
            }
            
            # Home team advanced analysis
            home_advanced = metrics_manager.get_comprehensive_team_analysis(
                team_id=home_team_id,
                team_name=home_team_name,
                league_id=league_id,
                team_stats=home_team_stats_dict,
                opponent_stats=away_team_stats_dict,
                recent_matches=home_recent,
                is_home=True
            )
            
            # Away team advanced analysis
            away_advanced = metrics_manager.get_comprehensive_team_analysis(
                team_id=away_team_id,
                team_name=away_team_name,
                league_id=league_id,
                team_stats=away_team_stats_dict,
                opponent_stats=home_team_stats_dict,
                recent_matches=away_recent,
                is_home=False
            )
            
            # Match prediction with advanced metrics
            advanced_prediction = metrics_manager.get_match_prediction_with_advanced_metrics(
                home_analysis=home_advanced,
                away_analysis=away_advanced
            )
            
            result['advanced_analysis'] = {
                'home_team': home_advanced,
                'away_team': away_advanced,
                'prediction': advanced_prediction
            }
            
        except Exception as e:
            print(f"⚠️ Advanced analysis error: {e}")
            import traceback
            traceback.print_exc()
    
    # 3. Combined Prediction (Classic + Advanced)
    if result['classic_analysis'] and result['advanced_analysis']:
        try:
            # Weight: 60% advanced, 40% classic
            adv_pred = result['advanced_analysis']['prediction']['match_prediction']
            
            result['combined_prediction'] = {
                'home_win': adv_pred['home_win'],
                'draw': adv_pred['draw'],
                'away_win': adv_pred['away_win'],
                'most_likely': adv_pred['most_likely'],
                'confidence': 'high' if max(adv_pred['home_win'], adv_pred['draw'], adv_pred['away_win']) > 50 else 'medium',
                'method': 'advanced_metrics'
            }
        except Exception as e:
            print(f"⚠️ Combined prediction error: {e}")
    
    return result


def print_enhanced_analysis_summary(analysis: Dict):
    """Print formatted summary of enhanced analysis"""
    print("\n" + "="*80)
    print("🔬 GELİŞMİŞ MAÇ ANALİZİ RAPORU")
    print("="*80 + "\n")
    
    if analysis.get('advanced_analysis'):
        adv = analysis['advanced_analysis']
        
        # Home Team
        print("🏠 EV SAHİBİ:")
        home = adv['home_team']
        print(f"   Overall Rating: {home.get('overall_rating', 0)}/100")
        print(f"   Strengths:")
        for s in home.get('strengths', []):
            print(f"      ✅ {s}")
        print(f"   Weaknesses:")
        for w in home.get('weaknesses', []):
            print(f"      ⚠️ {w}")
        
        print("\n✈️ DEPLASMAN:")
        away = adv['away_team']
        print(f"   Overall Rating: {away.get('overall_rating', 0)}/100")
        print(f"   Strengths:")
        for s in away.get('strengths', []):
            print(f"      ✅ {s}")
        print(f"   Weaknesses:")
        for w in away.get('weaknesses', []):
            print(f"      ⚠️ {w}")
        
        # Prediction
        print("\n📊 TAHMİN:")
        pred = adv['prediction']['match_prediction']
        print(f"   Ev Sahibi Kazanır: {pred['home_win']:.1f}%")
        print(f"   Beraberlik: {pred['draw']:.1f}%")
        print(f"   Deplasman Kazanır: {pred['away_win']:.1f}%")
        print(f"   En Olası: {pred['most_likely'].upper()}")
    
    print("\n" + "="*80 + "\n")


# Test
if __name__ == "__main__":
    # Test için örnek veriler
    print("🧪 Enhanced Match Analysis Test\n")
    
    # Bu normalde gerçek API'den gelecek
    test_api_key = "test_key"
    test_base_url = "https://api-football-v1.p.rapidapi.com/v3"
    
    # Not: Bu gerçek bir test yapmaz, sadece yapıyı gösterir
    print("ℹ️ Bu test gerçek API çağrısı yapmaz")
    print("ℹ️ Gerçek kullanım için API key ve team ID'leri gerekli")
