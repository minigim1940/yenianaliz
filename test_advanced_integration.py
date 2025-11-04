# -*- coding: utf-8 -*-
"""
Advanced Metrics Integration Test
==================================
Tüm yeni sistemlerin entegrasyon testi
"""

import sys
from typing import Dict

print("="*80)
print("🧪 ADVANCED METRICS INTEGRATION TEST")
print("="*80 + "\n")

# Test 1: Module Imports
print("📦 Test 1: Module Import Kontrolü\n")

modules_status = {}

try:
    from advanced_form_calculator import AdvancedFormCalculator
    modules_status['advanced_form_calculator'] = True
    print("   ✅ AdvancedFormCalculator")
except ImportError as e:
    modules_status['advanced_form_calculator'] = False
    print(f"   ❌ AdvancedFormCalculator: {e}")

try:
    from dynamic_home_advantage import DynamicHomeAdvantageCalculator
    modules_status['dynamic_home_advantage'] = True
    print("   ✅ DynamicHomeAdvantageCalculator")
except ImportError as e:
    modules_status['dynamic_home_advantage'] = False
    print(f"   ❌ DynamicHomeAdvantageCalculator: {e}")

try:
    from expected_goals_calculator import ExpectedGoalsCalculator
    modules_status['expected_goals_calculator'] = True
    print("   ✅ ExpectedGoalsCalculator")
except ImportError as e:
    modules_status['expected_goals_calculator'] = False
    print(f"   ❌ ExpectedGoalsCalculator: {e}")

try:
    from pressing_metrics_calculator import PressingMetricsCalculator
    modules_status['pressing_metrics_calculator'] = True
    print("   ✅ PressingMetricsCalculator")
except ImportError as e:
    modules_status['pressing_metrics_calculator'] = False
    print(f"   ❌ PressingMetricsCalculator: {e}")

try:
    from progressive_metrics_calculator import ProgressiveMetricsCalculator
    modules_status['progressive_metrics_calculator'] = True
    print("   ✅ ProgressiveMetricsCalculator")
except ImportError as e:
    modules_status['progressive_metrics_calculator'] = False
    print(f"   ❌ ProgressiveMetricsCalculator: {e}")

try:
    from expected_assists_calculator import ExpectedAssistsCalculator
    modules_status['expected_assists_calculator'] = True
    print("   ✅ ExpectedAssistsCalculator")
except ImportError as e:
    modules_status['expected_assists_calculator'] = False
    print(f"   ❌ ExpectedAssistsCalculator: {e}")

try:
    from advanced_metrics_manager import AdvancedMetricsManager
    modules_status['advanced_metrics_manager'] = True
    print("   ✅ AdvancedMetricsManager")
except ImportError as e:
    modules_status['advanced_metrics_manager'] = False
    print(f"   ❌ AdvancedMetricsManager: {e}")

# Summary
available_count = sum(1 for v in modules_status.values() if v)
total_count = len(modules_status)
print(f"\n📊 Durum: {available_count}/{total_count} modül yüklendi")

if available_count < total_count:
    print("\n⚠️ Bazı modüller yüklenemedi. Lütfen hataları kontrol edin.")
    sys.exit(1)

print("\n" + "="*80 + "\n")

# Test 2: AdvancedMetricsManager Integration
print("🔧 Test 2: AdvancedMetricsManager Entegrasyon Testi\n")

try:
    manager = AdvancedMetricsManager()
    print("   ✅ AdvancedMetricsManager instance oluşturuldu")
    
    # Availability check
    manager.print_availability_status()
    
except Exception as e:
    print(f"   ❌ Manager oluşturma hatası: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("="*80 + "\n")

# Test 3: Sample Team Analysis
print("🏟️ Test 3: Örnek Takım Analizi\n")

# Sample data (realistic football statistics)
sample_team_stats = {
    'shots_on_target': 6,
    'total_shots': 15,
    'goals_scored': 2.1,  # per match
    'goals_conceded': 1.1,
    'possession': 58,
    'total_passes': 520,
    'key_passes': 12,
    'assists': 1.8,
    'dribbles_success': 8,
    'tackles': 18,
    'interceptions': 12,
    'fouls': 10,
    'matches_played': 10
}

sample_opponent_stats = {
    'shots_on_target': 3,
    'total_shots': 8,
    'goals_scored': 1.0,
    'goals_conceded': 1.8,
    'possession': 42,
    'total_passes': 380,
    'key_passes': 6,
    'assists': 0.9,
    'matches_played': 10
}

sample_recent_matches = [
    {'goals_for': 3, 'goals_against': 1, 'location': 'home', 'opponent_strength': 75},
    {'goals_for': 2, 'goals_against': 0, 'location': 'home', 'opponent_strength': 68},
    {'goals_for': 1, 'goals_against': 1, 'location': 'home', 'opponent_strength': 82},
    {'goals_for': 2, 'goals_against': 1, 'location': 'home', 'opponent_strength': 71},
    {'goals_for': 1, 'goals_against': 2, 'location': 'away', 'opponent_strength': 88},
    {'goals_for': 2, 'goals_against': 2, 'location': 'away', 'opponent_strength': 79},
    {'goals_for': 3, 'goals_against': 0, 'location': 'home', 'opponent_strength': 65},
    {'goals_for': 1, 'goals_against': 0, 'location': 'away', 'opponent_strength': 73},
    {'goals_for': 2, 'goals_against': 1, 'location': 'home', 'opponent_strength': 77},
    {'goals_for': 1, 'goals_against': 1, 'location': 'home', 'opponent_strength': 70}
]

try:
    print("   Analiz ediliyor: Galatasaray (örnek)\n")
    
    analysis = manager.get_comprehensive_team_analysis(
        team_id=645,
        team_name="Galatasaray",
        league_id=203,
        team_stats=sample_team_stats,
        opponent_stats=sample_opponent_stats,
        recent_matches=sample_recent_matches,
        is_home=True
    )
    
    # Print results
    print(f"   📈 Overall Rating: {analysis['overall_rating']}/100")
    
    print(f"\n   💪 Strengths:")
    for strength in analysis['strengths']:
        print(f"      ✅ {strength}")
    
    print(f"\n   ⚠️ Weaknesses:")
    for weakness in analysis['weaknesses']:
        print(f"      🔸 {weakness}")
    
    # Detailed metrics
    print(f"\n   📊 Detaylı Metrikler:")
    
    if analysis.get('form_analysis'):
        form = analysis['form_analysis']
        print(f"      Form Score: {form.get('form_score', 0):.1f}/100 ({form.get('form_string', 'N/A')})")
    
    if analysis.get('home_advantage'):
        ha = analysis['home_advantage']
        print(f"      Home Advantage: {ha.get('home_advantage', 1.0):.2f}x")
    
    if analysis.get('expected_goals'):
        xg = analysis['expected_goals']
        print(f"      Expected Goals (xG): {xg.get('team_xG', 0):.2f}")
        print(f"      Expected Goals Against (xGA): {xg.get('opponent_xG', 0):.2f}")
    
    if analysis.get('pressing'):
        press = analysis['pressing']
        print(f"      PPDA: {press.get('ppda', 0):.2f}")
        print(f"      Pressing Score: {press.get('pressing_score', 0):.1f}/100")
    
    if analysis.get('progressive'):
        prog = analysis['progressive'].get('progressive_passing', {})
        print(f"      Progressive Quality: {prog.get('quality_score', 0):.1f}/100")
        print(f"      Field Tilt: {analysis['progressive'].get('field_tilt', {}).get('score', 0):.1f}")
    
    if analysis.get('chance_creation'):
        xa = analysis['chance_creation']
        print(f"      Expected Assists (xA): {xa.get('team_xa', 0):.2f}")
        print(f"      Playmaker Score: {xa.get('playmaker_score', 0):.1f}/100")
    
    print("\n   ✅ Takım analizi tamamlandı")
    
except Exception as e:
    print(f"   ❌ Analiz hatası: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*80 + "\n")

# Test 4: Match Prediction
print("⚽ Test 4: Maç Tahmin Testi\n")

# Second team (opponent)
opponent_stats = {
    'shots_on_target': 4,
    'total_shots': 11,
    'goals_scored': 1.3,
    'goals_conceded': 1.5,
    'possession': 52,
    'total_passes': 480,
    'key_passes': 9,
    'assists': 1.2,
    'matches_played': 10
}

opponent_recent = [
    {'goals_for': 2, 'goals_against': 1, 'location': 'away', 'opponent_strength': 72},
    {'goals_for': 1, 'goals_against': 2, 'location': 'away', 'opponent_strength': 78},
    {'goals_for': 0, 'goals_against': 1, 'location': 'home', 'opponent_strength': 75},
    {'goals_for': 2, 'goals_against': 0, 'location': 'away', 'opponent_strength': 68},
    {'goals_for': 1, 'goals_against': 1, 'location': 'home', 'opponent_strength': 74}
]

try:
    print("   Maç: Galatasaray (Ev) vs Fenerbahçe (Deplasman)\n")
    
    # Home team analysis (already have it from Test 3)
    home_analysis = analysis
    
    # Away team analysis
    away_analysis = manager.get_comprehensive_team_analysis(
        team_id=610,
        team_name="Fenerbahçe",
        league_id=203,
        team_stats=opponent_stats,
        opponent_stats=sample_team_stats,
        recent_matches=opponent_recent,
        is_home=False
    )
    
    # Match prediction
    prediction = manager.get_match_prediction_with_advanced_metrics(
        home_analysis=home_analysis,
        away_analysis=away_analysis
    )
    
    print(f"   📊 Maç Tahmini:")
    pred = prediction['match_prediction']
    print(f"      Ev Sahibi Kazanır: {pred['home_win']:.1f}%")
    print(f"      Beraberlik: {pred['draw']:.1f}%")
    print(f"      Deplasman Kazanır: {pred['away_win']:.1f}%")
    print(f"      En Olası Sonuç: {pred['most_likely'].upper()}")
    
    print(f"\n   🏠 Galatasaray: {home_analysis['overall_rating']:.1f}/100")
    print(f"   ✈️ Fenerbahçe: {away_analysis['overall_rating']:.1f}/100")
    
    print("\n   ✅ Maç tahmini tamamlandı")
    
except Exception as e:
    print(f"   ❌ Tahmin hatası: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*80)
print("✅ TÜM TESTLER BAŞARILI!")
print("="*80 + "\n")

print("📋 Özet:")
print(f"   • {available_count} modül aktif")
print(f"   • Takım analizi: ✅")
print(f"   • Maç tahmini: ✅")
print(f"   • Entegrasyon: ✅")
print("\n🎯 Advanced Metrics sistemi kullanıma hazır!")
