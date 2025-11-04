# -*- coding: utf-8 -*-
"""
Advanced Metrics Real-Time Test
================================
Gerçek API verilerini kullanarak Advanced Metrics sistemini test et
"""

import os
from enhanced_match_analysis import get_enhanced_match_analysis

# API credentials
API_KEY = os.getenv('RAPIDAPI_KEY', 'YOUR_API_KEY_HERE')
BASE_URL = "https://api-football-v1.p.rapidapi.com/v3"

def test_real_match():
    """
    Gerçek bir maç için test
    Ajax vs Galatasaray (görüntüdeki maç)
    """
    
    print("🧪 ADVANCED METRICS TEST - Gerçek API Verisi\n")
    print("="*80)
    print("Maç: Ajax vs Galatasaray")
    print("="*80 + "\n")
    
    # Test parametreleri
    home_team_id = 610  # Ajax
    away_team_id = 645  # Galatasaray
    home_team_name = "Ajax"
    away_team_name = "Galatasaray"
    league_id = 2  # UEFA Champions League
    season = 2024
    
    try:
        print("📡 API'den veriler çekiliyor...")
        
        analysis = get_enhanced_match_analysis(
            api_key=API_KEY,
            base_url=BASE_URL,
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            home_team_name=home_team_name,
            away_team_name=away_team_name,
            league_id=league_id,
            season=season
        )
        
        # Sonuçları kontrol et
        print("\n" + "="*80)
        print("📊 TEST SONUÇLARI")
        print("="*80 + "\n")
        
        # Classic Analysis
        if analysis.get('classic_analysis'):
            print("✅ Classic Analysis: BAŞARILI")
            home = analysis['classic_analysis']['home_stats']
            away = analysis['classic_analysis']['away_stats']
            print(f"   Home: Gol {home.get('home', {}).get('Ort. Gol ATILAN', 'N/A')}")
            print(f"   Away: Gol {away.get('away', {}).get('Ort. Gol ATILAN', 'N/A')}")
        else:
            print("❌ Classic Analysis: BAŞARISIZ")
        
        # Advanced Analysis
        if analysis.get('advanced_analysis'):
            print("\n✅ Advanced Analysis: BAŞARILI")
            adv = analysis['advanced_analysis']
            
            # Home team
            home_team = adv.get('home_team', {})
            print(f"\n🏠 {home_team_name}:")
            print(f"   Overall Rating: {home_team.get('overall_rating', 'N/A')}/100")
            
            strengths = home_team.get('strengths', [])
            if strengths:
                print(f"   Strengths: {len(strengths)} adet")
                for s in strengths[:3]:  # İlk 3 tanesi
                    print(f"      ✅ {s}")
            
            # Away team
            away_team = adv.get('away_team', {})
            print(f"\n✈️ {away_team_name}:")
            print(f"   Overall Rating: {away_team.get('overall_rating', 'N/A')}/100")
            
            strengths = away_team.get('strengths', [])
            if strengths:
                print(f"   Strengths: {len(strengths)} adet")
                for s in strengths[:3]:
                    print(f"      ✅ {s}")
            
            # Prediction
            pred = adv.get('prediction', {}).get('match_prediction', {})
            if pred:
                print(f"\n📊 Tahmin:")
                print(f"   Ev Sahibi: {pred.get('home_win', 0):.1f}%")
                print(f"   Beraberlik: {pred.get('draw', 0):.1f}%")
                print(f"   Deplasman: {pred.get('away_win', 0):.1f}%")
                print(f"   En Olası: {pred.get('most_likely', 'N/A').upper()}")
        else:
            print("\n❌ Advanced Analysis: BAŞARISIZ")
            print(f"   Hata: {analysis.get('error', 'Bilinmeyen hata')}")
        
        # Combined Prediction
        if analysis.get('combined_prediction'):
            print("\n✅ Combined Prediction: BAŞARILI")
        
        print("\n" + "="*80)
        print("🎯 TEST TAMAMLANDI")
        print("="*80 + "\n")
        
        # Detaylı debug için full output
        if not analysis.get('advanced_analysis'):
            print("🔍 DEBUG - Full Analysis Object:")
            import json
            print(json.dumps(analysis, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"\n❌ TEST BAŞARISIZ: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_real_match()
