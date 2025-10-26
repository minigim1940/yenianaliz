#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Juventus için gerçek canlı maç testi
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from football_api_v3 import APIFootballV3
import api_utils

def test_juventus_fixtures():
    """Juventus'un yaklaşan maçlarını test et"""
    print("=" * 60)
    print("🏟️ JUVENTUS YAKLASAN MAÇLARI TESTİ")
    print("=" * 60)
    
    api_key = "6336fb21e17dea87880d3b133132a13f"
    base_url = "https://v3.football.api-sports.io"
    
    # Juventus takım bilgilerini al
    juventus = api_utils.get_team_id(api_key, base_url, "juventus")
    
    if not juventus:
        print("❌ Juventus bulunamadı!")
        return False
        
    print(f"✅ Juventus (ID: {juventus['id']}) bulundu")
    
    # API instance oluştur
    api = APIFootballV3(api_key)
    
    # Juventus'un yaklaşan maçlarını al
    print("\n🔍 Juventus'un yaklaşan maçları aranıyor...")
    
    try:
        # Bugünün maçlarını kontrol et
        from datetime import datetime, timedelta
        today = datetime.now().strftime('%Y-%m-%d')
        
        fixtures_result = api.get_fixtures_by_date(today, team_id=juventus['id'])
        
        if fixtures_result.status.name == "SUCCESS" and fixtures_result.data:
            print(f"\n📅 Bugünkü Juventus maçları ({today}):")
            for fixture in fixtures_result.data:
                home = fixture.get('teams', {}).get('home', {}).get('name', 'N/A')
                away = fixture.get('teams', {}).get('away', {}).get('name', 'N/A') 
                status = fixture.get('fixture', {}).get('status', {}).get('short', 'N/A')
                fixture_id = fixture.get('fixture', {}).get('id', 'N/A')
                
                print(f"   🎯 {home} vs {away} (Status: {status}, ID: {fixture_id})")
                
                # Bu maç için canlı analiz test et
                if status in ['1H', '2H', 'HT', 'LIVE', 'NS']:
                    print(f"   🧪 Fixture {fixture_id} için analiz testi yapılıyor...")
                    
                    from football_api_v3 import RealTimeAnalyzer
                    analyzer = RealTimeAnalyzer(api)
                    
                    # _fetch_live_data test et
                    live_data = analyzer.streamer._fetch_live_data(fixture_id)
                    
                    if live_data:
                        print(f"   ✅ Canlı veri başarıyla alındı")
                        print(f"       Status: {live_data.get('status', {})}")
                        print(f"       Score: {live_data.get('score', {})}")
                    else:
                        print(f"   ⚠️ Canlı veri alınamadı (normal olabilir)")
                        
        else:
            print("ℹ️ Bugün Juventus maçı yok")
            
        # Yaklaşan birkaç günü de kontrol et
        print("\n🔍 Yaklaşan günlerde Juventus maçları aranıyor...")
        
        for i in range(1, 8):  # Gelecek 7 gün
            future_date = (datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d')
            fixtures_result = api.get_fixtures_by_date(future_date, team_id=juventus['id'])
            
            if fixtures_result.status.name == "SUCCESS" and fixtures_result.data:
                print(f"\n📅 {future_date} tarihindeki Juventus maçları:")
                for fixture in fixtures_result.data:
                    home = fixture.get('teams', {}).get('home', {}).get('name', 'N/A')
                    away = fixture.get('teams', {}).get('away', {}).get('name', 'N/A')
                    status = fixture.get('fixture', {}).get('status', {}).get('short', 'N/A')
                    fixture_id = fixture.get('fixture', {}).get('id', 'N/A')
                    
                    print(f"   ⚽ {home} vs {away} (Status: {status}, ID: {fixture_id})")
                    
                break  # İlk bulduğumuzda dur
                
        return True
        
    except Exception as e:
        print(f"❌ Hata: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_juventus_live_search():
    """Juventus için canlı maç arama testi (app.py'deki gibi)"""
    print("\n" + "=" * 60)
    print("🔴 JUVENTUS CANLI MAÇ ARAMA TESTİ")
    print("=" * 60)
    
    api_key = "6336fb21e17dea87880d3b133132a13f"
    
    try:
        api = APIFootballV3(api_key)
        
        # search_fixtures_by_team fonksiyonu benzeri
        team_search = "juventus"
        
        print(f"🔍 '{team_search}' için maçlar aranıyor...")
        
        # Takım ID'sini al
        juventus = api_utils.get_team_id(api_key, "https://v3.football.api-sports.io", team_search)
        
        if not juventus:
            print("❌ Takım bulunamadı!")
            return False
            
        print(f"✅ Takım bulundu: {juventus['name']} (ID: {juventus['id']})")
        
        # Yaklaşan maçları al
        from datetime import datetime, timedelta
        
        all_fixtures = []
        
        # Bugün ve gelecek 7 günü kontrol et
        for i in range(0, 8):
            check_date = (datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d')
            fixtures_result = api.get_fixtures_by_date(check_date, team_id=juventus['id'])
            
            if fixtures_result.status.name == "SUCCESS" and fixtures_result.data:
                all_fixtures.extend(fixtures_result.data)
        
        print(f"\n📋 Toplam {len(all_fixtures)} maç bulundu")
        
        # Canlı maçları filtrele
        live_fixtures = [f for f in all_fixtures if f.get('fixture', {}).get('status', {}).get('short') in 
                        ['1H', '2H', 'HT', 'ET', 'BT', 'LIVE']]
        
        print(f"🔴 {len(live_fixtures)} canlı maç")
        
        # Yaklaşan maçları filtrele
        upcoming_fixtures = [f for f in all_fixtures if f.get('fixture', {}).get('status', {}).get('short') == 'NS'][:3]
        
        print(f"⏰ {len(upcoming_fixtures)} yaklaşan maç")
        
        # Canlı maçları göster
        if live_fixtures:
            print("\n🔴 CANLI MAÇLAR:")
            for fixture in live_fixtures:
                home = fixture.get('teams', {}).get('home', {}).get('name', 'N/A')
                away = fixture.get('teams', {}).get('away', {}).get('name', 'N/A')
                status = fixture.get('fixture', {}).get('status', {}).get('short', 'N/A')
                fixture_id = fixture.get('fixture', {}).get('id', 'N/A')
                
                print(f"   🔥 {home} vs {away} ({status}) - ID: {fixture_id}")
                
                # Bu maç için gerçek zamanlı analiz test et
                print(f"      🧪 Analiz testi yapılıyor...")
                from football_api_v3 import RealTimeAnalyzer
                analyzer = RealTimeAnalyzer(api)
                
                result = analyzer.start_real_time_analysis(fixture_id)
                
                if result['status'] == 'analysis_started':
                    print(f"      ✅ Analiz başarıyla başlatıldı!")
                else:
                    print(f"      ⚠️ Analiz hatası: {result.get('message', 'Bilinmeyen')}")
        
        # Yaklaşan maçları göster
        if upcoming_fixtures:
            print("\n⏰ YAKLASAN MAÇLAR:")
            for fixture in upcoming_fixtures:
                home = fixture.get('teams', {}).get('home', {}).get('name', 'N/A')
                away = fixture.get('teams', {}).get('away', {}).get('name', 'N/A')
                fixture_date = fixture.get('fixture', {}).get('date', 'N/A')
                fixture_id = fixture.get('fixture', {}).get('id', 'N/A')
                
                print(f"   📅 {home} vs {away} ({fixture_date}) - ID: {fixture_id}")
                
        return True
        
    except Exception as e:
        print(f"❌ Canlı arama hatası: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🚀 JUVENTUS GERÇEK MAÇ TESTLERİ")
    print("===============================")
    
    success_count = 0
    total_tests = 2
    
    # Test 1: Juventus fixtures
    if test_juventus_fixtures():
        success_count += 1
    
    # Test 2: Juventus canlı arama
    if test_juventus_live_search():
        success_count += 1
    
    # Sonuç
    print("\n" + "=" * 60)
    print("📊 GERÇEK TEST SONUÇLARI")
    print("=" * 60)
    print(f"✅ Başarılı: {success_count}/{total_tests}")
    print(f"❌ Başarısız: {total_tests - success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("\n🎉 Tüm gerçek testler başarılı!")
        print("💡 Juventus canlı analizi artık çalışmalı.")
    else:
        print(f"\n⚠️ {total_tests - success_count} gerçek test başarısız.")
        
    return success_count == total_tests

if __name__ == "__main__":
    main()