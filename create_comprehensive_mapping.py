#!/usr/bin/env python3
"""
API'den TÜM takımları çekip comprehensive mapping oluşturan script
"""

from api_utils import make_api_request
import json
import time
import re

def fetch_all_teams():
    API_KEY = '6336fb21e17dea87880d3b133132a13f'
    BASE_URL = 'https://v3.football.api-sports.io'
    
    print("🌍 API'DEN TÜM TAKIMLAR ÇEKİLİYOR...")
    print("=" * 60)
    
    all_teams = []
    page = 1
    
    while True:
        try:
            print(f"📄 Sayfa {page} getiriliyor...")
            
            # Her sayfadan 20 takım gelir (API default)
            response, error = make_api_request(
                API_KEY, BASE_URL, "teams", 
                {'page': page}, 
                skip_limit=True
            )
            
            if error:
                print(f"❌ API Error: {error}")
                break
                
            if not response or len(response) == 0:
                print(f"📋 Sayfa {page} boş - toplam takım sayısı: {len(all_teams)}")
                break
            
            # Takımları ekle
            for team_data in response:
                team_info = team_data.get('team', {})
                if team_info:
                    all_teams.append({
                        'id': team_info.get('id'),
                        'name': team_info.get('name'),
                        'code': team_info.get('code'),
                        'country': team_info.get('country'),
                        'founded': team_info.get('founded'),
                        'logo': team_info.get('logo')
                    })
            
            print(f"✅ Sayfa {page}: {len(response)} takım eklendi (Toplam: {len(all_teams)})")
            
            # Eğer sayfada 20'den az takım varsa son sayfadayız
            if len(response) < 20:
                print(f"📋 Son sayfa - toplam takım sayısı: {len(all_teams)}")
                break
            
            page += 1
            time.sleep(0.5)  # Rate limit için bekleme
            
            # Güvenlik için maksimum 100 sayfa
            if page > 100:
                print("⚠️ Maksimum sayfa sınırına ulaşıldı")
                break
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            break
    
    return all_teams

def create_comprehensive_mapping(teams):
    """Tüm takımlar için comprehensive mapping oluştur"""
    print(f"\n🔧 {len(teams)} TAKIM İÇİN MAPPING OLUŞTURULUYOR...")
    print("=" * 60)
    
    # Mapping dictionary'si
    mapping_dict = {}
    
    # Ülkelere göre gruplama
    countries = {}
    
    for team in teams:
        team_name = team.get('name', '')
        team_id = team.get('id')
        team_country = team.get('country', 'Unknown')
        
        if not team_name or not team_id:
            continue
        
        # Ülke gruplarına ekle
        if team_country not in countries:
            countries[team_country] = []
        countries[team_country].append(team)
        
        # Temiz isim oluştur (mapping key için)
        clean_name = re.sub(r'[^\w\s]', '', team_name.lower())
        clean_name = re.sub(r'\s+', ' ', clean_name).strip()
        
        # Farklı varyasyonlar oluştur
        variations = set([
            clean_name,
            clean_name.replace(' ', ''),  # Boşluksuz
            clean_name.replace(' ', '_'),  # Alt çizgi ile
        ])
        
        # Kısaltmalar ekle
        words = clean_name.split()
        if len(words) >= 2:
            # İlk harfleri birleştir (örn: "real madrid" -> "rm")
            acronym = ''.join([word[0] for word in words if word])
            variations.add(acronym)
            
        # FC, AC, SC gibi prefix'leri kaldır
        prefixes = ['fc', 'ac', 'sc', 'cf', 'cd', 'ca', 'club', 'sporting']
        for prefix in prefixes:
            if clean_name.startswith(prefix + ' '):
                variations.add(clean_name[len(prefix)+1:])
        
        # Her varyasyon için mapping ekle
        for variation in variations:
            if variation and len(variation) >= 2:  # En az 2 karakter
                mapping_dict[variation] = team_id
    
    return mapping_dict, countries

def generate_mapping_code(mapping_dict):
    """Mapping dictionary'sini Python kod formatında üret"""
    
    print(f"\n📝 {len(mapping_dict)} MAPPING ENTRY OLUŞTURULUYOR...")
    
    # Ülkelere göre sırala
    lines = []
    lines.append("        team_mappings = {")
    
    # Alfabetik sıralama
    sorted_items = sorted(mapping_dict.items())
    
    for key, value in sorted_items:
        lines.append(f"            '{key}': {value},")
    
    lines.append("        }")
    
    return '\n'.join(lines)

def save_mapping_to_file(mapping_dict, countries, teams):
    """Mapping'i dosyaya kaydet"""
    
    # JSON formatında kaydet
    mapping_data = {
        'total_teams': len(teams),
        'total_mappings': len(mapping_dict),
        'countries': {country: len(team_list) for country, team_list in countries.items()},
        'mappings': mapping_dict,
        'teams': teams
    }
    
    with open('comprehensive_team_mapping.json', 'w', encoding='utf-8') as f:
        json.dump(mapping_data, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Mapping JSON dosyasına kaydedildi: comprehensive_team_mapping.json")
    
    # Python kodu oluştur
    python_code = generate_mapping_code(mapping_dict)
    
    with open('team_mapping_code.py', 'w', encoding='utf-8') as f:
        f.write("# Comprehensive Team Mapping - Auto Generated\n\n")
        f.write("def get_comprehensive_team_mapping():\n")
        f.write(f"    # Total teams: {len(teams)}\n")
        f.write(f"    # Total mappings: {len(mapping_dict)}\n")
        f.write(f"    # Countries: {len(countries)}\n\n")
        f.write(python_code)
        f.write("\n    return team_mappings\n")
    
    print(f"🐍 Python kodu oluşturuldu: team_mapping_code.py")

def main():
    print("🚀 COMPREHENSIVE TEAM MAPPING OLUŞTURUCU")
    print("=" * 60)
    
    # 1. Tüm takımları çek
    teams = fetch_all_teams()
    
    if not teams:
        print("❌ Hiç takım bulunamadı!")
        return
    
    # 2. Mapping oluştur
    mapping_dict, countries = create_comprehensive_mapping(teams)
    
    # 3. İstatistikleri göster
    print(f"\n📊 İSTATİSTİKLER:")
    print("=" * 60)
    print(f"✅ Toplam takım sayısı: {len(teams)}")
    print(f"✅ Toplam mapping sayısı: {len(mapping_dict)}")
    print(f"✅ Ülke sayısı: {len(countries)}")
    
    # En çok takımı olan ülkeler
    top_countries = sorted(countries.items(), key=lambda x: len(x[1]), reverse=True)[:10]
    print(f"\n🏆 EN ÇOK TAKIMI OLAN ÜLKELER:")
    for country, team_list in top_countries:
        print(f"  {country}: {len(team_list)} takım")
    
    # 4. Dosyalara kaydet
    save_mapping_to_file(mapping_dict, countries, teams)
    
    print(f"\n🎉 BAŞARILI! Comprehensive mapping oluşturuldu!")
    print(f"📁 Dosyalar: comprehensive_team_mapping.json, team_mapping_code.py")

if __name__ == "__main__":
    main()