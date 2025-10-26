#!/usr/bin/env python3
"""
Büyük ligler üzerinden TÜM takımları çeken script
"""

from api_utils import make_api_request, get_all_current_leagues
import json
import time
import re

def fetch_teams_by_leagues():
    API_KEY = '6336fb21e17dea87880d3b133132a13f'
    BASE_URL = 'https://v3.football.api-sports.io'
    
    print("🏆 LİGLERDEN TÜM TAKIMLAR ÇEKİLİYOR...")
    print("=" * 60)
    
    # Önce tüm ligleri al
    leagues, error = get_all_current_leagues(API_KEY, BASE_URL)
    if error or not leagues:
        print(f"❌ Ligler alınamadı: {error}")
        return []
    
    print(f"📋 Bulunan lig sayısı: {len(leagues)}")
    
    all_teams = {}  # ID bazlı dedup için
    processed_leagues = 0
    
    # Önemli ligler öncelikli
    priority_leagues = [
        'Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1',
        'Champions League', 'Europa League', 'Super Lig', 'Primeira Liga',
        'Eredivisie', 'Serie B', 'Championship', 'Liga MX'
    ]
    
    # Öncelikli ligleri önce işle
    priority_league_ids = []
    for league in leagues:
        if league.get('league_name') in priority_leagues:
            priority_league_ids.append(league)
    
    # Tüm ligleri işle (öncelikli + diğerleri)
    all_league_list = priority_league_ids + [l for l in leagues if l not in priority_league_ids]
    
    for league_info in all_league_list[:50]:  # İlk 50 lig (API limit)
        try:
            league_name = league_info.get('league_name', 'Unknown')
            league_id = league_info.get('league_id')
            season = league_info.get('season', 2024)
            
            print(f"\n🏆 Lig: {league_name} (ID: {league_id}, Season: {season})")
            
            # Lig takımlarını al
            response, error = make_api_request(
                API_KEY, BASE_URL, "teams", 
                {'league': league_id, 'season': season}, 
                skip_limit=True
            )
            
            if error:
                print(f"  ❌ Error: {error}")
                continue
                
            if not response:
                print(f"  ⚠️ Takım bulunamadı")
                continue
            
            league_team_count = 0
            for team_data in response:
                team_info = team_data.get('team', {})
                team_id = team_info.get('id')
                
                if team_id and team_id not in all_teams:
                    all_teams[team_id] = {
                        'id': team_info.get('id'),
                        'name': team_info.get('name'),
                        'code': team_info.get('code'),
                        'country': team_info.get('country'),
                        'founded': team_info.get('founded'),
                        'logo': team_info.get('logo'),
                        'leagues': []
                    }
                    league_team_count += 1
                
                # Takımın liglerini takip et
                if team_id in all_teams:
                    all_teams[team_id]['leagues'].append({
                        'league_name': league_name,
                        'league_id': league_id,
                        'season': season
                    })
            
            print(f"  ✅ {len(response)} takım bulundu, {league_team_count} yeni takım eklendi")
            print(f"  📊 Toplam benzersiz takım: {len(all_teams)}")
            
            processed_leagues += 1
            time.sleep(0.3)  # Rate limit
            
        except Exception as e:
            print(f"  ❌ Exception: {e}")
            continue
    
    print(f"\n🎯 İşlem tamamlandı:")
    print(f"   📋 İşlenen lig sayısı: {processed_leagues}")
    print(f"   ⚽ Toplam benzersiz takım: {len(all_teams)}")
    
    return list(all_teams.values())

def create_smart_mapping(teams):
    """Akıllı mapping oluştur - çakışmaları minimize et"""
    print(f"\n🧠 {len(teams)} TAKIM İÇİN AKILLI MAPPING OLUŞTURULUYOR...")
    print("=" * 60)
    
    mapping_dict = {}
    conflicts = {}
    
    for team in teams:
        team_name = team.get('name', '')
        team_id = team.get('id')
        team_country = team.get('country', 'Unknown')
        
        if not team_name or not team_id:
            continue
        
        # Temiz isim oluştur
        clean_name = re.sub(r'[^\w\s]', '', team_name.lower())
        clean_name = re.sub(r'\s+', ' ', clean_name).strip()
        
        # Ana isim varyasyonları
        variations = [clean_name]
        
        # Boşluksuz versiyon
        no_space = clean_name.replace(' ', '')
        if len(no_space) >= 3:
            variations.append(no_space)
        
        # Kısaltmalar
        words = clean_name.split()
        if len(words) >= 2:
            # İlk harfler
            acronym = ''.join([word[0] for word in words if word and len(word) > 0])
            if len(acronym) >= 2:
                variations.append(acronym)
        
        # FC, AC gibi önekleri kaldır
        prefixes_to_remove = ['fc', 'ac', 'sc', 'cf', 'cd', 'ca', 'club', 'sporting', 'real', 'atletico']
        for prefix in prefixes_to_remove:
            if clean_name.startswith(prefix + ' '):
                short_name = clean_name[len(prefix)+1:].strip()
                if len(short_name) >= 3:
                    variations.append(short_name)
        
        # United, City gibi sonekleri kısalt
        if 'united' in clean_name:
            variations.append(clean_name.replace('united', 'utd'))
        if 'city' in clean_name and len(clean_name) > 10:
            variations.append(clean_name.replace('city', '').strip())
        
        # Her varyasyon için mapping ekle
        for variation in set(variations):
            if len(variation) >= 2:
                if variation in mapping_dict:
                    # Çakışma var - conflict listesine ekle
                    if variation not in conflicts:
                        conflicts[variation] = []
                    conflicts[variation].append({
                        'team_id': team_id,
                        'team_name': team_name,
                        'country': team_country
                    })
                else:
                    mapping_dict[variation] = team_id
    
    # Çakışmaları çöz - ülke kodu ekleyerek
    for conflict_key, conflict_teams in conflicts.items():
        print(f"⚠️ Çakışma çözülüyor: '{conflict_key}' -> {len(conflict_teams)} takım")
        
        # En popüler takımı ana key'de bırak (lig sayısına göre)
        main_team = max(conflict_teams, key=lambda x: len(teams[next((i for i, t in enumerate(teams) if t['id'] == x['team_id']), 0)].get('leagues', [])))
        mapping_dict[conflict_key] = main_team['team_id']
        
        # Diğerleri için ülke kodlu varyant oluştur
        for team_info in conflict_teams:
            if team_info['team_id'] != main_team['team_id']:
                country_code = team_info['country'][:3].lower() if team_info['country'] else 'xxx'
                new_key = f"{conflict_key}_{country_code}"
                mapping_dict[new_key] = team_info['team_id']
    
    return mapping_dict

def update_api_utils_mapping(mapping_dict):
    """api_utils.py'daki team_mappings'i güncelle"""
    
    print(f"\n🔧 API_UTILS.PY GÜNCELLENİYOR...")
    print("=" * 60)
    
    # Mevcut mapping'i koru (manuel eklenenler)
    manual_mappings = {
        # Turkish teams  
        'galatasaray': 645, 'gala': 645, 'gs': 645,
        'fenerbahce': 611, 'fenerbahçe': 611, 'fener': 611, 'fb': 611,
        'besiktas': 549, 'beşiktaş': 549, 'bjk': 549,
        'trabzonspor': 998, 'trabzon': 998,
        # Popular shortcuts
        'barca': 529, 'madrid': 541, 'juve': 496,
        'man united': 33, 'man city': 50, 'spurs': 47,
        'bayern': 157, 'dortmund': 165, 'bvb': 165,
        'psg': 85, 'paris': 85,
    }
    
    # Manuel + otomatik mapping'leri birleştir
    combined_mapping = {**mapping_dict, **manual_mappings}
    
    # Sıralı string oluştur
    lines = []
    lines.append("        team_mappings = {")
    
    # Manuel eklenenleri önce, sonra alfabetik
    manual_keys = sorted(manual_mappings.keys())
    auto_keys = sorted([k for k in combined_mapping.keys() if k not in manual_mappings])
    
    lines.append("            # Manual/Popular mappings")
    for key in manual_keys:
        lines.append(f"            '{key}': {manual_mappings[key]},")
    
    lines.append("            # Auto-generated mappings")
    for key in auto_keys[:2000]:  # İlk 2000 mapping (dosya boyutu için)
        lines.append(f"            '{key}': {combined_mapping[key]},")
    
    lines.append("        }")
    
    new_mapping_code = '\n'.join(lines)
    
    # Dosyayı oku
    with open('api_utils.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # team_mappings bölümünü değiştir
    import re
    pattern = r'(team_mappings = \{.*?\n        \})'
    
    if re.search(pattern, content, re.DOTALL):
        new_content = re.sub(pattern, new_mapping_code, content, flags=re.DOTALL)
        
        # Dosyaya yaz
        with open('api_utils.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ api_utils.py güncellendi!")
        print(f"📊 Toplam mapping sayısı: {len(combined_mapping)}")
    else:
        print(f"❌ team_mappings bölümü bulunamadı!")

def main():
    print("🌍 COMPREHENSIVE TEAM MAPPING OLUŞTURUCU V2")
    print("=" * 70)
    
    # 1. Liglerden takımları çek
    teams = fetch_teams_by_leagues()
    
    if not teams:
        print("❌ Hiç takım bulunamadı!")
        return
    
    # 2. Akıllı mapping oluştur
    mapping_dict = create_smart_mapping(teams)
    
    # 3. İstatistikleri göster
    countries = {}
    for team in teams:
        country = team.get('country', 'Unknown')
        countries[country] = countries.get(country, 0) + 1
    
    print(f"\n📊 FINAL İSTATİSTİKLER:")
    print("=" * 60)
    print(f"✅ Toplam takım sayısı: {len(teams)}")
    print(f"✅ Toplam mapping sayısı: {len(mapping_dict)}")
    print(f"✅ Ülke sayısı: {len(countries)}")
    
    # En çok takımı olan ülkeler
    top_countries = sorted(countries.items(), key=lambda x: x[1], reverse=True)[:10]
    print(f"\n🏆 EN ÇOK TAKIMI OLAN ÜLKELER:")
    for country, count in top_countries:
        print(f"  {country}: {count} takım")
    
    # 4. api_utils.py'ı güncelle
    update_api_utils_mapping(mapping_dict)
    
    # 5. JSON backup kaydet
    backup_data = {
        'teams': teams,
        'mappings': mapping_dict,
        'countries': countries
    }
    
    with open('comprehensive_teams_backup.json', 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n🎉 BAŞARILI! Comprehensive mapping oluşturuldu!")
    print(f"📁 Backup dosyası: comprehensive_teams_backup.json")

if __name__ == "__main__":
    main()