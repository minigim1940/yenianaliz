#!/usr/bin/env python3
"""
Bilinen büyük liglerden TÜM takımları çeken ve comprehensive mapping oluşturan script
"""

from api_utils import make_api_request
import json
import time
import re

def fetch_teams_from_major_leagues():
    API_KEY = '6336fb21e17dea87880d3b133132a13f'
    BASE_URL = 'https://v3.football.api-sports.io'
    
    # Büyük liglerin bilinen ID'leri
    major_leagues = [
        # Top 5 European Leagues
        (39, 2024, 'Premier League'),         # England
        (140, 2024, 'La Liga'),               # Spain
        (135, 2024, 'Serie A'),               # Italy
        (78, 2024, 'Bundesliga'),             # Germany
        (61, 2024, 'Ligue 1'),                # France
        
        # Other Major European Leagues
        (94, 2024, 'Primeira Liga'),          # Portugal
        (88, 2024, 'Eredivisie'),             # Netherlands
        (144, 2024, 'Jupiler Pro League'),    # Belgium
        (203, 2024, 'Süper Lig'),             # Turkey
        (197, 2024, 'Greek Super League'),    # Greece
        
        # Champions League & Europa League
        (2, 2024, 'Champions League'),
        (3, 2024, 'Europa League'),
        (848, 2024, 'Conference League'),
        
        # Major South American Leagues
        (71, 2024, 'Serie A Brasil'),         # Brazil
        (128, 2024, 'Primera División'),      # Argentina
        
        # Other Top Leagues
        (253, 2024, 'MLS'),                   # USA
        (262, 2024, 'Liga MX'),               # Mexico
        (188, 2024, 'Scottish Premiership'),  # Scotland
        (179, 2024, 'Championship'),          # England 2nd tier
        (136, 2024, 'Serie B'),               # Italy 2nd tier
        
        # Asian Leagues
        (98, 2024, 'J1 League'),              # Japan
        (292, 2024, 'K League 1'),            # South Korea
        (169, 2024, 'Super League'),          # China
        
        # Additional European Leagues
        (218, 2024, '2. Bundesliga'),         # Germany 2nd
        (344, 2024, 'La Liga 2'),             # Spain 2nd
        (62, 2024, 'Ligue 2'),                # France 2nd
        (119, 2024, 'Superligaen'),           # Denmark
        (103, 2024, 'Eliteserien'),           # Norway
        (113, 2024, 'Allsvenskan'),           # Sweden
    ]
    
    print(f"🌍 {len(major_leagues)} BÜYÜK LİGDEN TAKIMLAR ÇEKİLİYOR...")
    print("=" * 60)
    
    all_teams = {}  # ID bazlı dedup
    
    for league_id, season, league_name in major_leagues:
        try:
            print(f"\n🏆 {league_name} (ID: {league_id}, Season: {season})")
            
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
                
                # Lig bilgisini ekle
                if team_id in all_teams:
                    all_teams[team_id]['leagues'].append({
                        'league_name': league_name,
                        'league_id': league_id,
                        'season': season
                    })
            
            print(f"  ✅ {len(response)} takım, {league_team_count} yeni takım eklendi")
            print(f"  📊 Toplam benzersiz takım: {len(all_teams)}")
            
            time.sleep(0.3)  # Rate limit koruması
            
        except Exception as e:
            print(f"  ❌ Exception: {e}")
            continue
    
    return list(all_teams.values())

def create_comprehensive_mapping(teams):
    """Comprehensive mapping oluştur"""
    print(f"\n🔧 {len(teams)} TAKIM İÇİN COMPREHENSIVE MAPPING...")
    print("=" * 60)
    
    mapping_dict = {}
    
    for team in teams:
        team_name = team.get('name', '')
        team_id = team.get('id')
        
        if not team_name or not team_id:
            continue
        
        # Temiz isim oluştur
        clean_name = re.sub(r'[^\w\s]', '', team_name.lower())
        clean_name = re.sub(r'\s+', ' ', clean_name).strip()
        
        # Ana mapping
        if clean_name and len(clean_name) >= 2:
            mapping_dict[clean_name] = team_id
        
        # Boşluksuz versiyon
        no_space = clean_name.replace(' ', '')
        if len(no_space) >= 3:
            mapping_dict[no_space] = team_id
        
        # Kısaltmalar
        words = clean_name.split()
        if len(words) >= 2:
            acronym = ''.join([w[0] for w in words if w])
            if len(acronym) >= 2:
                mapping_dict[acronym] = team_id
        
        # Özel durumlar
        special_mappings = {
            'fc barcelona': 'barca',
            'real madrid cf': 'madrid',
            'manchester united': 'manutd',
            'manchester city': 'mancity',
            'paris saint germain': 'psg',
            'bayern munich': 'bayern',
            'borussia dortmund': 'dortmund',
            'atletico madrid': 'atletico',
            'tottenham hotspur': 'spurs',
            'juventus': 'juve',
            'ac milan': 'milan',
            'internazionale': 'inter',
            'galatasaray sk': 'gala',
            'fenerbahce sk': 'fener',
            'besiktas jk': 'bjk',
        }
        
        for full_name, short_name in special_mappings.items():
            if full_name in clean_name:
                mapping_dict[short_name] = team_id
        
        # Prefix kaldırma (fc, ac, sc vb.)
        prefixes = ['fc', 'ac', 'sc', 'cf', 'cd', 'ca', 'club', 'sporting', 'sk', 'jk']
        for prefix in prefixes:
            if clean_name.startswith(prefix + ' '):
                short_name = clean_name[len(prefix)+1:].strip()
                if len(short_name) >= 3:
                    mapping_dict[short_name] = team_id
    
    return mapping_dict

def update_api_utils_with_comprehensive_mapping(mapping_dict):
    """api_utils.py'ı yeni comprehensive mapping ile güncelle"""
    
    print(f"\n🔧 API_UTILS.PY KAPSAMLI GÜNCELLENİYOR...")
    print("=" * 60)
    
    # Mevcut özel mapping'leri koru
    priority_mappings = {
        # Turkish teams (verified IDs)
        'galatasaray': 645, 'gala': 645, 'gs': 645,
        'fenerbahce': 611, 'fenerbahçe': 611, 'fener': 611, 'fb': 611,
        'besiktas': 549, 'beşiktaş': 549, 'bjk': 549,
        'trabzonspor': 998, 'trabzon': 998,
        
        # Popular shortcuts (verified)
        'barca': 529, 'madrid': 541, 'juve': 496,
        'man united': 33, 'man city': 50, 'city': 50,
        'spurs': 47, 'bayern': 157, 'dortmund': 165, 'bvb': 165,
        'psg': 85, 'paris': 85, 'milan': 489, 'inter': 505,
        'arsenal': 42, 'chelsea': 49, 'liverpool': 40,
    }
    
    # Öncelikli + comprehensive mapping birleştir
    final_mapping = {**mapping_dict, **priority_mappings}
    
    # Mapping code oluştur
    lines = []
    lines.append("        team_mappings = {")
    
    # Öncelikli mapping'ler önce
    lines.append("            # Priority/Manual mappings")
    for key in sorted(priority_mappings.keys()):
        lines.append(f"            '{key}': {priority_mappings[key]},")
    
    lines.append("            # Comprehensive auto-generated mappings")
    auto_keys = [k for k in sorted(final_mapping.keys()) if k not in priority_mappings]
    
    # İlk 3000 mapping (dosya boyutu için sınır)
    for key in auto_keys[:3000]:
        lines.append(f"            '{key}': {final_mapping[key]},")
    
    lines.append("        }")
    
    new_mapping_code = '\n'.join(lines)
    
    # api_utils.py'ı güncelle
    try:
        with open('api_utils.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # team_mappings bölümünü bul ve değiştir
        import re
        pattern = r'(team_mappings = \{[^}]*\n        \})'
        
        if re.search(pattern, content, re.DOTALL):
            new_content = re.sub(pattern, new_mapping_code, content, flags=re.DOTALL)
            
            with open('api_utils.py', 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"✅ api_utils.py başarıyla güncellendi!")
            print(f"📊 Toplam mapping: {len(final_mapping)} (Priority: {len(priority_mappings)}, Auto: {len(auto_keys[:3000])})")
            
        else:
            print(f"❌ team_mappings bölümü bulunamadı!")
            
    except Exception as e:
        print(f"❌ Dosya güncellenirken hata: {e}")

def main():
    print("🚀 COMPREHENSIVE TEAM MAPPING OLUŞTURUCU - FINAL VERSION")
    print("=" * 70)
    
    # 1. Büyük liglerden takımları çek
    teams = fetch_teams_from_major_leagues()
    
    if not teams:
        print("❌ Hiç takım bulunamadı!")
        return
    
    # 2. Comprehensive mapping oluştur
    mapping_dict = create_comprehensive_mapping(teams)
    
    # 3. İstatistikler
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
    top_countries = sorted(countries.items(), key=lambda x: x[1], reverse=True)[:15]
    print(f"\n🏆 EN ÇOK TAKIMI OLAN ÜLKELER:")
    for country, count in top_countries:
        print(f"  {country}: {count} takım")
    
    # 4. api_utils.py'ı güncelle
    update_api_utils_with_comprehensive_mapping(mapping_dict)
    
    # 5. Backup kaydet
    backup_data = {
        'total_teams': len(teams),
        'total_mappings': len(mapping_dict),
        'countries': countries,
        'teams': teams,
        'mappings': dict(sorted(mapping_dict.items()))
    }
    
    with open('comprehensive_teams_final.json', 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n🎉 BAŞARILI! Comprehensive mapping tamamlandı!")
    print(f"📁 Backup: comprehensive_teams_final.json")
    print(f"🔥 Artık {len(mapping_dict)}+ takım için instant arama mevcut!")

if __name__ == "__main__":
    main()