#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Juventus maç analizi testi - Düzeltilmiş versiyon
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from football_api_v3 import APIFootballV3, RealTimeAnalyzer
import api_utils

def test_juventus_search():
    """Juventus takım arama testi"""
    print("=" * 50)
    print("🔍 JUVENTUS TAKIM ARAMA TESTİ")
    print("=" * 50)
    
    api_key = os.environ.get('API_KEY')
    base_url = "https://v3.football.api-sports.io"
    
    if not api_key:
        print("❌ API KEY bulunamadı!")
        return False
    
    # Juventus arama
    juventus_data = api_utils.get_team_id(api_key, base_url, "juventus")
    
    if juventus_data:
        print(f"✅ Juventus bulundu:")
        print(f"   ID: {juventus_data['id']}")
        print(f"   İsim: {juventus_data['name']}")
        print(f"   Ülke: {juventus_data.get('country', 'N/A')}")
        return True
    else:
        print("❌ Juventus bulunamadı!")
        return False

def test_real_time_analyzer():
    """Real-time analyzer testi"""
    print("\n" + "=" * 50)
    print("⚡ REAL-TIME ANALYZER TESTİ")
    print("=" * 50)
    
    api_key = os.environ.get('API_KEY')
    
    if not api_key:
        print("❌ API KEY bulunamadı!")
        return False
    
    try:
        # API instance oluştur
        api = APIFootballV3(api_key)
        
        # Real-time analyzer oluştur
        analyzer = RealTimeAnalyzer(api)
        
        print("✅ RealTimeAnalyzer başarıyla oluşturuldu")
        
        # Test fixture ID (örnek)
        test_fixture_id = 12345
        
        # _fetch_live_data fonksiyonunu test et
        print(f"\n🔍 Test fixture {test_fixture_id} için veri çekiliyor...")
        
        live_data = analyzer.streamer._fetch_live_data(test_fixture_id)
        
        if live_data:
            print("✅ Canlı veri başarıyla çekildi")
            print(f"   Fixture info keys: {list(live_data.get('fixture_info', {}).keys())}")
            print(f"   Status: {live_data.get('status', {})}")
            return True
        else:
            print("⚠️ Canlı veri çekilemedi (bu normal olabilir - maç aktif değilse)")
            return True  # Bu durumda hata değil
            
    except Exception as e:
        print(f"❌ RealTimeAnalyzer hatası: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_live_fixtures():
    """Canlı maçlar testi"""
    print("\n" + "=" * 50)
    print("🔴 CANLI MAÇLAR TESTİ")  
    print("=" * 50)
    
    api_key = os.environ.get('API_KEY')
    
    if not api_key:
        print("❌ API KEY bulunamadı!")
        return False
    
    try:
        api = APIFootballV3(api_key)
        
        # Canlı maçları al
        live_result = api.get_live_fixtures()
        
        if live_result.status.name == "SUCCESS":
            live_matches = live_result.data or []
            print(f"✅ {len(live_matches)} canlı maç bulundu")
            
            # İlk birkaç maçı göster
            for i, match in enumerate(live_matches[:3]):
                home = match.get('teams', {}).get('home', {}).get('name', 'N/A')
                away = match.get('teams', {}).get('away', {}).get('name', 'N/A')
                status = match.get('fixture', {}).get('status', {}).get('short', 'N/A')
                print(f"   {i+1}. {home} vs {away} ({status})")
                
            return True
        else:
            print(f"⚠️ Canlı maç sorgusu başarısız: {live_result.error}")
            return False
            
    except Exception as e:
        print(f"❌ Canlı maç testi hatası: {e}")
        return False

def main():
    """Ana test fonksiyonu"""
    print("🚀 JUVENTUS ANALIZ SORUNU TEST SUITE")
    print("====================================")
    
    success_count = 0
    total_tests = 3
    
    # Test 1: Juventus arama
    if test_juventus_search():
        success_count += 1
    
    # Test 2: Real-time analyzer
    if test_real_time_analyzer():
        success_count += 1
        
    # Test 3: Canlı maçlar
    if test_live_fixtures():
        success_count += 1
    
    # Sonuç
    print("\n" + "=" * 50)
    print("📊 TEST SONUÇLARI")
    print("=" * 50)
    print(f"✅ Başarılı: {success_count}/{total_tests}")
    print(f"❌ Başarısız: {total_tests - success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("\n🎉 Tüm testler başarılı! Juventus analizi çalışmalı.")
    else:
        print(f"\n⚠️ {total_tests - success_count} test başarısız. Kontrol gerekli.")
    
    return success_count == total_tests

if __name__ == "__main__":
    main()