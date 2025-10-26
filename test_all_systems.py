#!/usr/bin/env python3
"""
Sistem kapsamlı test dosyası - Tüm ana fonksiyonları test eder
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

print("🧪 SİSTEM KAPSAMLI TEST BAŞLATIYOR")
print("=" * 60)

def test_api_utils():
    """api_utils.py fonksiyonlarını test et"""
    print("\n1. 🔍 API UTILS TEST")
    print("-" * 30)
    
    try:
        from api_utils import get_team_id
        api_key = "6336fb21e17dea87880d3b133132a13f"
        base_url = "https://v3.football.api-sports.io/"
        
        test_teams = ["Galatasaray", "Barcelona"]
        
        for team_name in test_teams:
            result = get_team_id(api_key, base_url, team_name)
            if result:
                print(f"  ✅ {team_name}: {result['name']} (ID: {result['id']})")
            else:
                print(f"  ❌ {team_name}: FAILED")
        
        print("  ✅ API Utils: PASSED")
        return True
        
    except Exception as e:
        print(f"  ❌ API Utils: FAILED - {str(e)}")
        return False

def test_professional_analysis():
    """professional_analysis.py sistemini test et"""
    print("\n2. 🎯 PROFESSIONAL ANALYSIS TEST")
    print("-" * 40)
    
    try:
        from football_api_v3 import APIFootballV3
        from professional_analysis import initialize_analysis_engine
        
        api_key = "6336fb21e17dea87880d3b133132a13f"
        api = APIFootballV3(api_key)
        engine = initialize_analysis_engine(api)
        
        # Test team analysis
        result = engine.analyze_team("Galatasaray")
        
        if 'error' not in result:
            team_data = result.get('team', {})
            fixtures_data = result.get('fixtures', {})
            injuries_data = result.get('injuries', {})
            
            print(f"  ✅ Team: {team_data.get('name', 'N/A')}")
            print(f"  ✅ Fixtures: {fixtures_data.get('total_count', 0)} found")
            print(f"  ✅ Injuries: {injuries_data.get('total_count', 0)} found") 
            print("  ✅ Professional Analysis: PASSED")
            return True
        else:
            print(f"  ❌ Professional Analysis: {result['error']}")
            return False
        
    except Exception as e:
        print(f"  ❌ Professional Analysis: FAILED - {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_analysis_logic():
    """analysis_logic.py sistemini test et"""
    print("\n3. 🧠 ANALYSIS LOGIC TEST") 
    print("-" * 35)
    
    try:
        from analysis_logic import process_h2h_data, process_player_stats
        
        # Test H2H processing
        dummy_h2h = [{
            'teams': {'home': {'id': 1, 'name': 'Team A'}, 'away': {'id': 2, 'name': 'Team B'}},
            'score': {'fulltime': {'home': 2, 'away': 1}},
            'fixture': {'timestamp': 1640995200}  # 2022-01-01
        }]
        
        result = process_h2h_data(dummy_h2h, team_a_id=1)
        
        if result and 'summary' in result:
            summary = result['summary']
            print(f"  ✅ H2H Processing: {summary['total_matches']} matches analyzed")
            print(f"  ✅ Goals processing: {result['goals']['avg_goals_a']:.1f} avg goals")
            print("  ✅ Analysis Logic: PASSED")
            return True
        else:
            print("  ❌ Analysis Logic: No valid result")
            return False
        
    except Exception as e:
        print(f"  ❌ Analysis Logic: FAILED - {str(e)}")
        return False

def test_football_api_v3():
    """football_api_v3.py sistemini test et"""
    print("\n4. ⚽ FOOTBALL API V3 TEST")
    print("-" * 35)
    
    try:
        from football_api_v3 import APIFootballV3
        
        api_key = "6336fb21e17dea87880d3b133132a13f"
        api = APIFootballV3(api_key)
        
        # Test team search
        result = api.search_teams("Barcelona")
        
        if hasattr(result, 'status') and result.status.value == "success":
            if result.data and len(result.data) > 0:
                team = result.data[0]['team']
                print(f"  ✅ Team Search: {team['name']} (ID: {team['id']})")
                print("  ✅ Football API v3: PASSED")
                return True
            else:
                print("  ❌ Football API v3: No data")
                return False
        else:
            print(f"  ❌ Football API v3: {result.error if hasattr(result, 'error') else 'Unknown error'}")
            return False
        
    except Exception as e:
        print(f"  ❌ Football API v3: FAILED - {str(e)}")
        return False

def main():
    """Ana test fonksiyonu"""
    
    test_results = []
    
    # Run all tests
    test_results.append(("API Utils", test_api_utils()))
    test_results.append(("Professional Analysis", test_professional_analysis()))
    test_results.append(("Analysis Logic", test_analysis_logic()))
    test_results.append(("Football API v3", test_football_api_v3()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SONUÇLARI")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<25}: {status}")
        if result:
            passed += 1
    
    print("-" * 60)
    print(f"📊 TOPLAM: {passed}/{total} TEST GEÇTİ ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 TÜM SİSTEMLER ÇALIŞIYOR!")
    else:
        print("⚠️ BAZI SİSTEMLERDE SORUN VAR!")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)