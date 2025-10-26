# -*- coding: utf-8 -*-
# api_utils.py

import requests
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, date
import json
import os
import yaml

# Streamlit compatibility check
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    # No-op decorator for non-Streamlit environments
    class st:
        @staticmethod
        def cache_data(ttl=None, show_spinner=None):
            def decorator(func):
                return func
            return decorator

# Streamlit'i optional yap (GitHub Actions için)
try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False
    # Dummy cache decorator for non-streamlit environments
    def cache_data(ttl=None):
        def decorator(func):
            return func
        return decorator
    
    class st:
        cache_data = staticmethod(cache_data)
        session_state = {}

# --- API LİMİT KONTROL MEKANİZMASI ---

USAGE_FILE = 'user_usage.json'
TIER_LIMITS = {
    'ücretli': 1500,
    'ücretsiz': 150,
    'admin': 999999,
    'dev': 999999
}

# Admin action log is stored inside the usage file under the key '_admin_log' as a list of entries
ADMIN_LOG_KEY = '_admin_log'

def get_api_limit_for_user(tier: str) -> int:
    """Kullanıcının seviyesine göre API limitini döner."""
    # Development user için sınırsız erişim
    try:
        if HAS_STREAMLIT and hasattr(st, 'session_state') and st.session_state.get('username') == 'dev_user':
            return 999999
    except Exception:
        pass
    
    # Varsayılan olarak bilinmeyen bir tier için ücretsiz tier limiti uygulanır
    return TIER_LIMITS.get(tier, TIER_LIMITS['ücretsiz'])

def get_current_usage(username: str) -> Dict[str, Any]:
    """
    Kullanıcının mevcut API kullanım verisini dosyadan okur. CACHE YOK - Her zaman güncel veri.
    
    ÖNEMLİ: Aylık sayaç ASLA otomatik sıfırlanmaz - sadece admin manuel olarak sıfırlayabilir.
    Günlük sayaç her gün otomatik sıfırlanır (tarih değiştiğinde).
    """
    today_str = str(date.today())
    month_str = date.today().strftime('%Y-%m')
    if not os.path.exists(USAGE_FILE):
        return {'date': today_str, 'count': 0, 'month': month_str, 'monthly_count': 0}

    try:
        with open(USAGE_FILE, 'r', encoding='utf-8') as f:
            usage_data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        usage_data = {}

    user_data = usage_data.get(username, {})

    # Tarih değişti mi kontrol et (gece 00:00'da günlük sayacı reset)
    if user_data.get('date') != today_str:
        # SADECE günlük sayacı sıfırla - aylık sayacı KORUMA
        user_data['date'] = today_str
        user_data['count'] = 0
        # monthly_count korunur - değişmez
        usage_data[username] = user_data
        _write_usage_file(usage_data)

    # Ay bilgisini güncelle ama aylık sayacı SIFIRLAMAYI KALDIR
    if user_data.get('month') != month_str:
        # Sadece ay bilgisini güncelle, monthly_count'u KORUMA
        user_data['month'] = month_str
        # AYLUK SAYAÇ KORUNUR - ASLA OTOMATİK SIFIRLANMAZ
        # Admin manuel olarak sıfırlamalı
        usage_data[username] = user_data
        _write_usage_file(usage_data)

    user_data.setdefault('count', 0)
    user_data.setdefault('monthly_count', 0)
    user_data.setdefault('month', month_str)

    return user_data

def update_usage(username: str, current_data: Dict[str, Any]):
    """Kullanıcının API kullanım sayacını günceller ve dosyaya yazar."""
    try:
        with open(USAGE_FILE, 'r', encoding='utf-8') as f:
            usage_data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        usage_data = {}

    # Preserve limit overrides containers if present
    limits = usage_data.get('_limits', {})
    monthly_limits = usage_data.get('_monthly_limits', {})

    usage_data[username] = current_data
    if limits:
        usage_data['_limits'] = limits
    if monthly_limits:
        usage_data['_monthly_limits'] = monthly_limits

    with open(USAGE_FILE, 'w', encoding='utf-8') as f:
        json.dump(usage_data, f, indent=4, ensure_ascii=False)


def _read_usage_file() -> Dict[str, Any]:
    try:
        with open(USAGE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def _write_usage_file(data: Dict[str, Any]):
    with open(USAGE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def get_pending_notification(username: str) -> Optional[Dict[str, str]]:
    """Kullanıcının bekleyen bildirimini getirir."""
    try:
        data = _read_usage_file()
        notifications = data.get('_pending_notifications', {})
        return notifications.get(username)
    except Exception:
        return None


def clear_pending_notification(username: str):
    """Kullanıcının bildirimini temizler."""
    try:
        data = _read_usage_file()
        notifications = data.get('_pending_notifications', {})
        if username in notifications:
            del notifications[username]
            data['_pending_notifications'] = notifications
            _write_usage_file(data)
    except Exception:
        pass


def ensure_user_limits(username: str, tier: str):
    """Ensure that a user has an explicit per-user daily limit in the usage file.
    If not present, set it to the tier default (ücretsiz/ücretli).
    Returns the effective daily limit that was set or already present.
    """
    data = _read_usage_file()
    limits = data.get('_limits', {})
    if username in limits:
        return limits[username]
    # assign default based on tier
    default = get_api_limit_for_user(tier)
    limits[username] = int(default)
    data['_limits'] = limits
    # ensure a usage record exists for the user so UI can show counts
    user = data.get(username, {})
    user.setdefault('date', str(date.today()))
    user.setdefault('count', 0)
    user.setdefault('month', date.today().strftime('%Y-%m'))
    user.setdefault('monthly_count', 0)
    data[username] = user
    _write_usage_file(data)
    return default


def set_user_daily_limit(username: str, limit: int):
    data = _read_usage_file()
    limits = data.get('_limits', {})
    prev_limit = limits.get(username)
    limits[username] = int(limit)
    data['_limits'] = limits
    
    # Kullanıcıya pending notification ekle
    if '_pending_notifications' not in data:
        data['_pending_notifications'] = {}
    data['_pending_notifications'][username] = {
        'message': f'⚠️ API haklarınızda değişiklik yapıldı! Yeni günlük limitiniz: {int(limit)}. Lütfen çıkış yapıp yeniden giriş yapın.',
        'type': 'limit_change'
    }
    
    # Eğer mevcut günlük sayaç limitin üzerinde ise clamp et
    user = data.get(username, {})
    if user:
        try:
            current_count = int(user.get('count', 0))
            if current_count > int(limit):
                user['count'] = int(limit)
                data[username] = user
        except Exception:
            pass
    _write_usage_file(data)
    # Log admin action (best-effort). If running inside Streamlit, read current admin username.
    try:
        admin_user = st.session_state.get('username') if HAS_STREAMLIT and hasattr(st, 'session_state') else 'system'
    except Exception:
        admin_user = 'system'
    try:
        log_admin_action(admin_user, 'set_user_daily_limit', username, {'prev_limit': prev_limit, 'new_limit': int(limit)})
    except Exception:
        pass


def set_user_monthly_limit(username: str, limit: int):
    data = _read_usage_file()
    mlimits = data.get('_monthly_limits', {})
    prev_mlimit = mlimits.get(username)
    mlimits[username] = int(limit)
    data['_monthly_limits'] = mlimits
    
    # Kullanıcıya pending notification ekle
    if '_pending_notifications' not in data:
        data['_pending_notifications'] = {}
    data['_pending_notifications'][username] = {
        'message': f'⚠️ API haklarınızda değişiklik yapıldı! Yeni aylık limitiniz: {int(limit)}. Lütfen çıkış yapıp yeniden giriş yapın.',
        'type': 'limit_change'
    }
    
    # Eğer mevcut aylık sayaç limitin üzerinde ise clamp et
    user = data.get(username, {})
    if user:
        try:
            current_monthly = int(user.get('monthly_count', 0))
            if current_monthly > int(limit):
                user['monthly_count'] = int(limit)
                data[username] = user
        except Exception:
            pass
    _write_usage_file(data)
    try:
        admin_user = st.session_state.get('username') if HAS_STREAMLIT and hasattr(st, 'session_state') else 'system'
    except Exception:
        admin_user = 'system'
    try:
        log_admin_action(admin_user, 'set_user_monthly_limit', username, {'prev_limit': prev_mlimit, 'new_limit': int(limit)})
    except Exception:
        pass


def log_admin_action(admin: str, action: str, target: str, details: Optional[Dict[str, Any]] = None):
    """Append an admin action entry into the usage file under '_admin_log'.
    Entry fields: ts (UTC iso), admin, action, target, details
    """
    try:
        data = _read_usage_file()
        log = data.get(ADMIN_LOG_KEY, [])
        entry = {
            'ts': datetime.utcnow().isoformat() + 'Z',
            'admin': admin or 'system',
            'action': action,
            'target': target,
            'details': details or {}
        }
        # prepend newest first
        log.insert(0, entry)
        data[ADMIN_LOG_KEY] = log
        _write_usage_file(data)
    except Exception:
        # Best-effort; ignore logging failures
        pass


def get_admin_log(limit: int = 50) -> List[Dict[str, Any]]:
    """Admin log'unu döner. Cache YOK."""
    data = _read_usage_file()
    log = data.get(ADMIN_LOG_KEY, [])
    return log[:limit]


def reset_daily_usage(username: str = None):
    """Sadece belirtilen kullanıcı için veya tüm kullanıcılar için günlük sayacı sıfırlar. Cache YOK."""
    data = _read_usage_file()
    today_str = str(date.today())
    if username:
        u = data.get(username, {})
        u['date'] = today_str
        u['count'] = 0
        data[username] = u
    else:
        for k, v in list(data.items()):
            if k.startswith('_'):
                continue
            v['date'] = today_str
            v['count'] = 0
            data[k] = v
    _write_usage_file(data)


def get_usage_summary() -> Dict[str, Dict[str, Any]]:
    """Tüm kullanıcıların günlük ve aylık kullanım özetini döner. Cache YOK - Her zaman güncel."""
    data = _read_usage_file()
    summary = {}
    for k, v in data.items():
        if k.startswith('_'):
            continue
        summary[k] = {
            'date': v.get('date'),
            'count': v.get('count', 0),
            'month': v.get('month'),
            'monthly_count': v.get('monthly_count', 0),
            'daily_limit': data.get('_limits', {}).get(k, None),
            'monthly_limit': data.get('_monthly_limits', {}).get(k, None),
        }
    return summary


def _get_ip_assignments() -> Dict[str, str]:
    """Return the mapping of IP -> username from the usage file (best-effort)."""
    data = _read_usage_file()
    return data.get('_ip_assignments', {})


def _set_ip_assignment(ip: str, username: str):
    """Assign an IP to a username (overwrites existing assignment)."""
    data = _read_usage_file()
    ipmap = data.get('_ip_assignments', {})
    ipmap[ip] = username
    data['_ip_assignments'] = ipmap
    _write_usage_file(data)


def register_ip_assignment(username: str, tier: str, ip: str) -> Tuple[bool, Optional[str]]:
    """Try to assign API access for `username` tied to `ip`."""
    if not ip:
        return False, 'IP belirtilmediği için atama yapılamadı.'
    data = _read_usage_file()
    ipmap = data.get('_ip_assignments', {})
    existing = ipmap.get(ip)
    if existing and existing != username:
        return False, f"Bu IP zaten '{existing}' kullanıcısına ait."
    # assign and ensure user has limits
    ipmap[ip] = username
    data['_ip_assignments'] = ipmap
    try:
        ensure_user_limits(username, tier)
    except Exception:
        pass
    _write_usage_file(data)
    return True, None


def get_client_ip() -> str:
    """Best-effort client IP detection."""
    try:
        import streamlit as _st
        qp = getattr(_st, 'query_params', None)
        if qp:
            v = qp.get('client_ip', [''])[0]
            if v:
                return v
    except Exception:
        pass

    for key in ('HTTP_X_FORWARDED_FOR', 'X_FORWARDED_FOR', 'HTTP_CLIENT_IP', 'REMOTE_ADDR'):
        v = os.environ.get(key) or os.environ.get(key.lower())
        if v:
            return v.split(',')[0].strip()

    try:
        r = requests.get('https://api.ipify.org?format=json', timeout=3)
        j = r.json()
        return j.get('ip', '')
    except Exception:
        return ''

def set_user_tier(username: str, tier: str) -> Tuple[bool, Optional[str]]:
    """
    Kullanıcının seviyesini (tier) hem config.yaml'de hem de günlük limitini user_usage.json'da günceller.
    """
    if tier not in TIER_LIMITS:
        return False, f"Geçersiz seviye: {tier}. Sadece 'ücretli' veya 'ücretsiz' olabilir."

    # Adım 1: config.yaml dosyasındaki tier'ı güncelle
    try:
        config_path = 'config.yaml'
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if username in config['credentials']['usernames']:
            config['credentials']['usernames'][username]['tier'] = tier
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True)
        else:
            return False, f"Kullanıcı '{username}' config.yaml'de bulunamadı."
    except Exception as e:
        return False, f"config.yaml güncellenirken hata oluştu: {e}"

    # Adım 2: user_usage.json dosyasındaki günlük limiti yeni seviyeye göre ayarla
    try:
        new_limit = TIER_LIMITS[tier]
        set_user_daily_limit(username, new_limit)
    except Exception as e:
        return False, f"Günlük limit ayarlanırken hata oluştu: {e}"

    return True, f"Kullanıcı {username} başarıyla {tier} seviyesine geçirildi ve limiti {new_limit} olarak ayarlandı."

def check_api_limit() -> Tuple[bool, Optional[str]]:
    """API isteği yapmadan önce limiti kontrol eder. SAYACI ARTIRMAZ - sadece kontrol eder."""
    try:
        if not HAS_STREAMLIT:
            return True, None  # GitHub Actions için bypass
        
        # Localhost development mode bypass
        import os
        if os.getenv('STREAMLIT_SERVER_ADDRESS') == 'localhost' or 'localhost' in os.environ.get('STREAMLIT_SERVER_ADDRESS', ''):
            return True, None  # Localhost için bypass
            
        if "authentication_status" not in st.session_state or not st.session_state["authentication_status"]:
            return False, "API isteği yapmak için giriş yapmalısınız."
    except Exception:
        # Eğer session_state erişimi başarısız olursa (ön yükleme sırasında), isteği geçir
        return True, None

    username = st.session_state.get('username')
    admin_users = st.session_state.get('admin_users', [])
    
    # Development user için sınırsız API erişimi
    if username == 'dev_user':
        return True, None
    
    # Admin kullanıcılar için sınırsız erişim
    if username and username in admin_users:
        return True, None
    
    tier = st.session_state.get('tier', 'ücretsiz')
    
    data = _read_usage_file()
    per_user_limit = data.get('_limits', {}).get(username)
    
    # Eğer per_user_limit 0 ise varsayılana dön, değilse kullan
    if per_user_limit is not None and per_user_limit > 0:
        limit = per_user_limit
    else:
        limit = get_api_limit_for_user(tier)

    monthly_limit = data.get('_monthly_limits', {}).get(username)
    if monthly_limit is not None and monthly_limit == 0:
        monthly_limit = None  # 0 = limitsiz

    user_usage = get_current_usage(username)

    if user_usage['count'] >= limit:
        return False, f"Günlük API istek limitinize ({limit}) ulaştınız. Yarın tekrar deneyin."

    if monthly_limit is not None and user_usage.get('monthly_count', 0) >= monthly_limit:
        return False, f"Aylık API istek limitinize ({monthly_limit}) ulaştınız. Sonraki ay tekrar deneyin."

    # SADECE KONTROL ET, ARTIRMA!
    return True, None

def increment_api_usage() -> None:
    """API kullanım sayacını artırır - sadece gerçek HTTP isteği yapıldığında çağrılmalı."""
    try:
        if not HAS_STREAMLIT:
            return  # GitHub Actions için bypass
        if "authentication_status" not in st.session_state or not st.session_state["authentication_status"]:
            return
    except Exception:
        return

    username = st.session_state.get('username')
    admin_users = st.session_state.get('admin_users', [])
    
    # Development user için sayaç artırma - sınırsız kullanım
    if username == 'dev_user':
        return
    
    # Admin için de sayacı artır ama limit kontrolü yapma
    if username:
        # Önce mevcut kullanımı al (tarih kontrolü yapılacak)
        user_usage = get_current_usage(username)
        
        # Sayacı artır
        user_usage['count'] = user_usage.get('count', 0) + 1
        user_usage['monthly_count'] = user_usage.get('monthly_count', 0) + 1
        
        # Dosyaya yaz
        update_usage(username, user_usage)
        
        # Debug: Konsola yazdır
        print(f"[API USAGE] {username}: Günlük={user_usage['count']}, Aylık={user_usage['monthly_count']}")

def make_api_request(api_key: str, base_url: str, endpoint: str, params: Dict[str, Any], skip_limit: bool = False) -> Tuple[Optional[Any], Optional[str]]:
    # Development user için otomatik skip_limit
    try:
        if HAS_STREAMLIT and hasattr(st, 'session_state') and st.session_state.get('username') == 'dev_user':
            skip_limit = True
    except Exception:
        pass
    
    if not skip_limit:
        can_request, error_message = check_api_limit()
        if not can_request:
            return None, error_message

    headers = {'x-rapidapi-key': api_key, 'x-rapidapi-host': "v3.football.api-sports.io"}
    url = f"{base_url}/{endpoint}"
    try:
        response = requests.get(url, headers=headers, params=params, timeout=20)
        
        # GERÇEK HTTP İSTEĞİ YAPILDI - SAYACI ARTIR
        if not skip_limit:
            increment_api_usage()
        
        response.raise_for_status()
        api_data = response.json()
        if api_data.get('errors') and (isinstance(api_data['errors'], dict) and api_data['errors']) or (isinstance(api_data['errors'], list) and len(api_data['errors']) > 0):
            return None, f"API Hatası: {api_data['errors']}"
        return api_data.get('response', []), None
    except requests.exceptions.HTTPError as http_err:
        return None, f"HTTP Hatası: {http_err}. API Anahtarınızı veya aboneliğinizi kontrol edin."
    except requests.exceptions.RequestException as req_err:
        return None, f"Bağlantı Hatası: {req_err}"

@st.cache_data(ttl=86400)
def get_player_stats(api_key: str, base_url: str, player_id: int, season: int) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
    return make_api_request(api_key, base_url, "players", {'id': player_id, 'season': season})

@st.cache_data(ttl=86400)
def get_fixture_details(api_key: str, base_url: str, fixture_id: int) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    response, error = make_api_request(api_key, base_url, "fixtures", {'id': fixture_id})
    if error:
        return None, error
    return (response[0], None) if response else (None, "Maç detayı bulunamadı.")

@st.cache_data(ttl=86400)
def get_referee_stats(api_key: str, base_url: str, referee_id: int, season: int) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    response, error = make_api_request(api_key, base_url, "referees", {'id': referee_id, 'season': season})
    if error:
        return None, error
    return (response[0], None) if response else (None, "Hakem istatistiği bulunamadı.")

@st.cache_data(ttl=86400)
def get_team_statistics(api_key: str, base_url: str, team_id: int, league_id: int, season: int, skip_limit: bool = False) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Takım istatistiklerini getirir.
    NOT: skip_limit parametresi cache key'ine dahildir. Eğer skip_limit=True ve skip_limit=False 
    için farklı cache oluşmasını istemiyorsanız, SADECE bir değerle çağırın.
    """
    params = {'team': team_id, 'league': league_id, 'season': season}
    return make_api_request(api_key, base_url, "teams/statistics", params, skip_limit=skip_limit)

@st.cache_data(ttl=3600)
def get_team_last_matches_stats(api_key: str, base_url: str, team_id: int, limit: int = 10, skip_limit: bool = False) -> Optional[List[Dict]]:
    """
    Takımın son maçlarını çeker (sadece gol verileri).
    NOT: API-Football /fixtures endpoint'i statistics döndürmüyor,
    bu yüzden korner/kart verileri None kalır ve formül kullanılır.
    """
    params = {'team': team_id, 'last': limit, 'status': 'FT'}
    matches, error = make_api_request(api_key, base_url, "fixtures", params, skip_limit=skip_limit)
    if error or not matches:
        return None
    stats_list = []
    # API'den en yeni maçlar başta gelir, reversed() KULLANMA
    for match in matches:
        try:
            is_home = match['teams']['home']['id'] == team_id
            score_for = match['score']['fulltime']['home' if is_home else 'away']
            score_against = match['score']['fulltime']['away' if is_home else 'home']
            if score_for is None or score_against is None: 
                continue
            
            # Korner ve kart verileri - API'den gelmiyor, None bırak
            # Formül kullanarak hesaplanacak
            stats_list.append({
                'location': 'home' if is_home else 'away',
                'goals_for': score_for,
                'goals_against': score_against,
                'corners_for': None,
                'corners_against': None,
                'yellow_cards': None,
                'red_cards': None
            })
        except (KeyError, TypeError):
            continue
    
    return stats_list

@st.cache_data(ttl=3600)
def get_fixture_odds(api_key: str, base_url: str, fixture_id: int) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
    """1X2 oranlarını (Match Winner) çeker"""
    params = {'fixture': fixture_id, 'bet': 1}
    return make_api_request(api_key, base_url, "odds", params)

@st.cache_data(ttl=3600)
def get_fixture_detailed_odds(api_key: str, base_url: str, fixture_id: int) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Tüm bahis türlerini çeker ve kategorize eder.
    Returns: {
        'match_winner': [...],  # 1X2
        'over_under': [...],    # 2.5 Üst/Alt
        'btts': [...],          # Karşılıklı Gol
        'handicap': [...],      # Handikap
        'first_half': [...],    # İlk Yarı
        'corners': [...],       # Kornerler
        'cards': [...]          # Kartlar
    }
    """
    # Tüm bahis türlerini çek (bet parametresi olmadan)
    params = {'fixture': fixture_id}
    response, error = make_api_request(api_key, base_url, "odds", params)
    
    if error:
        return None, f"API hatası: {error}"
    
    if not response:
        return None, "Bu maç için hiçbir bahis oranı bulunamadı."
    
    categorized_odds = {
        'match_winner': [],
        'over_under': [],
        'btts': [],
        'handicap': [],
        'first_half': [],
        'corners': [],
        'cards': []
    }
    
    try:
        if not response[0].get('bookmakers'):
            return None, "Bahis şirketleri verisi bulunamadı."
        
        bookmakers = response[0].get('bookmakers', [])
        total_bets_found = 0
        
        for bookmaker in bookmakers:
            bets = bookmaker.get('bets', [])
            
            for bet in bets:
                bet_name = bet.get('name', '').lower()
                total_bets_found += 1
                
                # Kategorizasyon (daha geniş pattern matching)
                if 'match winner' in bet_name or ('winner' in bet_name and 'half' not in bet_name):
                    categorized_odds['match_winner'].append({
                        'bookmaker': bookmaker.get('name'),
                        'bet_name': bet.get('name'),
                        'values': bet.get('values', [])
                    })
                elif 'over/under' in bet_name or 'goals over/under' in bet_name or 'total goals' in bet_name:
                    categorized_odds['over_under'].append({
                        'bookmaker': bookmaker.get('name'),
                        'bet_name': bet.get('name'),
                        'values': bet.get('values', [])
                    })
                elif 'both teams score' in bet_name or 'btts' in bet_name or 'gg/ng' in bet_name:
                    categorized_odds['btts'].append({
                        'bookmaker': bookmaker.get('name'),
                        'bet_name': bet.get('name'),
                        'values': bet.get('values', [])
                    })
                elif 'handicap' in bet_name or 'spread' in bet_name or 'asian handicap' in bet_name:
                    categorized_odds['handicap'].append({
                        'bookmaker': bookmaker.get('name'),
                        'bet_name': bet.get('name'),
                        'values': bet.get('values', [])
                    })
                elif '1st half' in bet_name or 'first half' in bet_name or 'half time' in bet_name or 'ht' in bet_name:
                    categorized_odds['first_half'].append({
                        'bookmaker': bookmaker.get('name'),
                        'bet_name': bet.get('name'),
                        'values': bet.get('values', [])
                    })
                elif 'corner' in bet_name:
                    categorized_odds['corners'].append({
                        'bookmaker': bookmaker.get('name'),
                        'bet_name': bet.get('name'),
                        'values': bet.get('values', [])
                    })
                elif 'card' in bet_name or 'yellow' in bet_name or 'booking' in bet_name:
                    categorized_odds['cards'].append({
                        'bookmaker': bookmaker.get('name'),
                        'bet_name': bet.get('name'),
                        'values': bet.get('values', [])
                    })
        
        # Debug bilgisi için
        debug_msg = f"Toplam {total_bets_found} bahis türü bulundu. "
        debug_msg += f"Kategoriler: "
        for cat, data in categorized_odds.items():
            if data:
                debug_msg += f"{cat}({len(data)}), "
        
        return categorized_odds, None
    
    except (KeyError, IndexError, TypeError) as e:
        return None, f"Oran verisi işlenirken hata: {str(e)}"

@st.cache_data(ttl=86400) 
def get_fixture_injuries(api_key: str, base_url: str, fixture_id: int) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
    return make_api_request(api_key, base_url, "injuries", {'fixture': fixture_id})

@st.cache_data(ttl=86400)
def get_squad_player_stats(api_key: str, base_url: str, team_id: int, season: int) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
    return make_api_request(api_key, base_url, "players", {'team': team_id, 'season': season})

@st.cache_data(ttl=86400)
def get_league_standings(api_key: str, base_url: str, league_id: int, season: int) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
    response, error = make_api_request(api_key, base_url, "standings", {'league': league_id, 'season': season})
    if error: return None, error
    if response and response[0]['league']['standings']:
        return response[0]['league']['standings'][0], None
    return None, None

@st.cache_data(ttl=86400)
def get_all_current_leagues(api_key: str, base_url: str) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    response, error = make_api_request(api_key, base_url, "leagues", {'current': 'true'}, skip_limit=True)
    if error or not response:
        return [], error

    leagues: List[Dict[str, Any]] = []
    seen_ids = set()
    for item in response:
        try:
            league_info = item.get('league') or {}
            league_id = league_info.get('id')
            league_name = league_info.get('name')
            if not league_id or not league_name or league_id in seen_ids:
                continue

            seasons = item.get('seasons') or []
            current_season = next((s.get('year') for s in seasons if s.get('current')), None)
            country_info = item.get('country') or {}
            country_name = country_info.get('name') or 'Uluslararası'

            leagues.append({
                'id': league_id,
                'name': league_name,
                'country': country_name,
                'type': league_info.get('type'),
                'season': current_season,
                'display': f"{country_name} - {league_name}"
            })
            seen_ids.add(league_id)
        except Exception:
            continue

    leagues.sort(key=lambda l: (l.get('country') or '', l.get('name') or ''))
    return leagues, None

@st.cache_data(ttl=86400)
def get_h2h_matches(api_key: str, base_url: str, team_a_id: int, team_b_id: int, limit: int) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
    return make_api_request(api_key, base_url, "fixtures/headtohead", {'h2h': f"{team_a_id}-{team_b_id}", 'last': limit})

@st.cache_data(ttl=604800)
def get_teams_by_league(api_key: str, base_url: str, league_id: int, season: int) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
    return make_api_request(api_key, base_url, "teams", {'league': league_id, 'season': season})

@st.cache_data(ttl=86400)
def get_team_form_sequence(api_key: str, base_url: str, team_id: int, limit: int = 10) -> Optional[List[Dict[str, str]]]:
    matches, error = make_api_request(api_key, base_url, "fixtures", {'team': team_id, 'last': limit, 'status': 'FT'})
    if error or not matches:
        return None
    form_data = []
    for match in reversed(matches):
        try:
            score_home = match['score']['fulltime']['home']
            score_away = match['score']['fulltime']['away']
            if score_home is None or score_away is None: continue
            is_home_team = match['teams']['home']['id'] == team_id
            opponent_name = match['teams']['away']['name'] if is_home_team else match['teams']['home']['name']
            score_str = f"{score_home}-{score_away}" if is_home_team else f"{score_away}-{score_home}"
            result = 'B'
            if (is_home_team and score_home > score_away) or (not is_home_team and score_away > score_home):
                result = 'G'
            elif (is_home_team and score_home < score_away) or (not is_home_team and score_away < score_home):
                result = 'M'
            form_data.append({'result': result, 'opponent': opponent_name, 'score': score_str})
        except (KeyError, TypeError):
            continue
    return form_data

@st.cache_data(ttl=86400)
def get_team_league_info(api_key: str, base_url: str, team_id: int, skip_limit: bool = False) -> Optional[Dict[str, Any]]:
    response, error = make_api_request(api_key, base_url, "leagues", {'team': team_id, 'current': 'true'}, skip_limit=skip_limit)
    if error or not response: return None
    league, seasons = response[0]['league'], response[0]['seasons']
    season = next((s['year'] for s in seasons if s['current']), seasons[-1]['year'])
    return {'league_id': league['id'], 'season': season}

def find_upcoming_fixture(api_key: str, base_url: str, team_a_id: int, team_b_id: int, season: int) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    fixtures, error = make_api_request(api_key, base_url, "fixtures", {'team': team_a_id, 'season': season, 'status': 'NS'})
    if error: return None, error
    if fixtures:
        for f in fixtures:
            if f['teams']['home']['id'] == team_b_id or f['teams']['away']['id'] == team_b_id:
                return f, None
    return None, None
    
def get_next_team_fixture(api_key: str, base_url: str, team_id: int) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Belirtilen takımın sıradaki ilk maçını getirir."""
    # Önce next parametresi ile dene
    response, error = make_api_request(api_key, base_url, "fixtures", {'team': team_id, 'next': 1})
    if not error and response:
        return (response[0], None) if response else (None, "Takımın yaklaşan maçı bulunamadı.")
    
    # Next çalışmazsa alternatif yöntem: tarih aralığı ile
    from datetime import datetime, timedelta
    today = datetime.now()
    end_date = today + timedelta(days=60)  # 60 gün sonrasına kadar ara
    
    params = {
        'team': team_id,
        'from': today.strftime('%Y-%m-%d'),
        'to': end_date.strftime('%Y-%m-%d'),
        'status': 'NS'  # Not Started
    }
    
    response2, error2 = make_api_request(api_key, base_url, "fixtures", params)
    if not error2 and response2:
        return (response2[0], None) if response2 else (None, "Takımın yaklaşan maçı bulunamadı.")
    
    # Son çare: Sample data kullan (API limiti aşıldıysa)
    if "429" in str(error) or "limit" in str(error):
        from sample_data import get_sample_fixture
        sample_fixture = get_sample_fixture(team_id)
        if sample_fixture:
            print(f"API limit - using sample fixture data for team {team_id}")
            return (sample_fixture, None)
    
    return None, error or error2 or "Takımın yaklaşan maçı bulunamadı."

@st.cache_data(ttl=1800)  # 30 dakika cache
def get_team_upcoming_fixtures(api_key: str, base_url: str, team_id: int, limit: int = 5) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
    """Takımın yaklaşan birkaç maçını getirir - daha geniş arama."""
    try:
        # Önce next parametresi ile dene
        response, error = make_api_request(api_key, base_url, "fixtures", {'team': team_id, 'next': limit})
        if not error and response:
            return response, None
        
        # Next parametresi çalışmazsa tarih aralığı ile dene
        from datetime import datetime, timedelta
        today = datetime.now()
        end_date = today + timedelta(days=30)  # 30 gün sonrasına kadar
        
        params = {
            'team': team_id,
            'from': today.strftime('%Y-%m-%d'),
            'to': end_date.strftime('%Y-%m-%d'),
            'status': 'NS'  # Not Started
        }
        
        response, error = make_api_request(api_key, base_url, "fixtures", params)
        if not error and response:
            return response[:limit], None
        
        # Son çare: sadece takım ID ile arama
        response, error = make_api_request(api_key, base_url, "fixtures", {'team': team_id})
        if not error and response:
            # Gelecekteki maçları filtrele
            upcoming = [f for f in response if f.get('fixture', {}).get('status', {}).get('short') == 'NS']
            return upcoming[:limit] if upcoming else None, None
        
        return None, error or "Takımın yaklaşan maçı bulunamadı."
    
    except Exception as e:
        return None, f"Arama sırasında hata: {str(e)}"

@st.cache_data(ttl=1800)  # 30 dakika cache  
def search_team_fixtures_advanced(api_key: str, base_url: str, team_name: str) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
    """Takım adından gelişmiş maç arama."""
    try:
        # Önce takımı bul
        team_data = get_team_id(api_key, base_url, team_name)
        if not team_data:
            return None, f"'{team_name}' takımı bulunamadı."
        
        team_id = team_data['id']
        
        # Yaklaşan maçları ara
        fixtures, error = get_team_upcoming_fixtures(api_key, base_url, team_id, limit=10)
        if fixtures:
            return fixtures, None
        
        # Hata durumunda detaylı bilgi ver
        error_msg = f"'{team_name}' takımının yaklaşan maçı bulunamadı."
        if error:
            error_msg += f" API Hatası: {error}"
        
        return None, error_msg
    
    except Exception as e:
        return None, f"Arama sırasında hata: {str(e)}"

@st.cache_data(ttl=3600)  # 1 saat cache - aynı gün içinde tekrar API çağrısı yapma
def get_fixtures_by_date(api_key: str, base_url: str, selected_league_ids: List[int], selected_date: date, bypass_limit_check: bool = False) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    all_fixtures, error_messages = [], []
    date_str = selected_date.strftime('%Y-%m-%d')
    season = selected_date.year if selected_date.month > 6 else selected_date.year - 1
    
    # Rate limit önleme: Çok fazla lig seçilmişse istekler arasında gecikme ekle
    import time
    num_leagues = len(selected_league_ids)
    
    # Agresif gecikme stratejisi - API rate limit'ini aşmamak için
    if num_leagues > 20:
        delay_between_requests = 1.0  # 1 saniye (çok fazla lig için)
    elif num_leagues > 15:
        delay_between_requests = 0.7  # 0.7 saniye
    elif num_leagues > 10:
        delay_between_requests = 0.5  # 0.5 saniye
    elif num_leagues > 5:
        delay_between_requests = 0.2  # 0.2 saniye
    else:
        delay_between_requests = 0  # Gecikme yok
    
    successful_leagues = 0
    rate_limit_hit = False
    
    for idx, league_id in enumerate(selected_league_ids):
        # Rate limit önleme gecikmesi
        if idx > 0 and delay_between_requests > 0:
            time.sleep(delay_between_requests)
        
        # Eğer rate limit'e takıldıysak, daha uzun bekle
        if rate_limit_hit:
            time.sleep(2.0)  # 2 saniye bekle
            rate_limit_hit = False
        
        # Status filtresi kullanma - sadece tarih ve lig bazlı çek
        params = {'date': date_str, 'league': league_id, 'season': season}
        response, error = make_api_request(api_key, base_url, "fixtures", params, skip_limit=bypass_limit_check)
        
        if error:
            # Rate limit hatası mı kontrol et
            if 'rate limit' in error.lower() or 'too many requests' in error.lower():
                error_messages.append(f"⚠️ API Rate Limit - Lig {league_id} atlandı")
                rate_limit_hit = True
                continue
            else:
                error_messages.append(f"Lig ID {league_id}: {error}")
            continue
        
        if response:
            successful_leagues += 1
            for f in response:
                try:
                    fixture_status = f['fixture']['status']['short']
                    
                    # ORIGINAL API FORMAT - enhanced_analysis.py için
                    # Tam API response formatını koruyalım
                    all_fixtures.append(f)
                except (KeyError, TypeError): 
                    continue
    
    # Hata mesajlarını hazırla (başarı mesajı olmadan)
    final_error = "\n".join(error_messages) if error_messages else None
    
    # Başarı bilgisi ayrı olarak logla (hata değil)
    if successful_leagues > 0 and successful_leagues < num_leagues:
        success_msg = f"ℹ️ {successful_leagues}/{num_leagues} lig başarıyla yüklendi"
        print(success_msg)  # Console'a yazdır, error olarak dönme
    
    # Sort by league name and fixture time using API format
    try:
        sorted_fixtures = sorted(all_fixtures, key=lambda x: (
            x.get('league', {}).get('name', ''), 
            x.get('fixture', {}).get('timestamp', 0)
        ))
    except:
        sorted_fixtures = all_fixtures  # Fallback if sorting fails
    
    return sorted_fixtures, final_error

def get_team_id(api_key: str, base_url: str, team_input: str, season: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """
    Main team search function for homepage - simplified and working
    """
    try:
        # Strategy 1: Direct mapping for popular teams (fastest)
        team_mappings = {
            # Priority/Manual mappings
            'arsenal': 42,
            'barca': 529,
            'bayern': 157,
            'besiktas': 549,
            'beşiktaş': 549,
            'bjk': 549,
            'bvb': 165,
            'chelsea': 49,
            'city': 50,
            'dortmund': 165,
            'fb': 611,
            'fener': 611,
            'fenerbahce': 611,
            'fenerbahçe': 611,
            'gala': 645,
            'galatasaray': 645,
            'gs': 645,
            'inter': 505,
            'juve': 496,
            'liverpool': 40,
            'madrid': 541,
            'man city': 50,
            'man united': 33,
            'milan': 489,
            'paris': 85,
            'psg': 85,
            'spurs': 47,
            'trabzon': 998,
            'trabzonspor': 998,
            # Comprehensive auto-generated mappings
            '1 fc heidenheim': 180,
            '1899 hoffenheim': 167,
            '1899hoffenheim': 167,
            '1fcheidenheim': 180,
            '1fh': 180,
            '1h': 167,
            'aa': 201,
            'aaf': 575,
            'aalborg': 402,
            'aarhus': 406,
            'aberdeen': 252,
            'ac': 531,
            'ac milan': 489,
            'acd': 3345,
            'acf': 419,
            'acmilan': 489,
            'ad': 3563,
            'adana demirspor': 3563,
            'adanademirspor': 3563,
            'adelaide united': 948,
            'adelaideunited': 948,
            'adh': 198,
            'ado den haag': 198,
            'adodenhaag': 198,
            'aek athens fc': 575,
            'aek larnaca': 614,
            'aekathensfc': 575,
            'aeklarnaca': 614,
            'af': 316,
            'ag': 144,
            'aik stockholm': 377,
            'aikstockholm': 377,
            'aj': 458,
            'ajaccio': 98,
            'ajax': 194,
            'ak': 1405,
            'aktobe': 4563,
            'al': 614,
            'alanyaspor': 996,
            'alaves': 542,
            'albirex niigata': 311,
            'albirexniigata': 311,
            'almere city fc': 419,
            'almerecityfc': 419,
            'always ready': 3700,
            'alwaysready': 3700,
            'am': 2753,
            'america': 2287,
            'amiens': 87,
            'an': 311,
            'anderlecht': 554,
            'angers': 77,
            'annecy': 3012,
            'antalyaspor': 1005,
            'antwerp': 740,
            'ap': 134,
            'apoel nicosia': 2247,
            'apoelnicosia': 2247,
            'ar': 3700,
            'araratarmenia': 3683,
            'argentinos jrs': 458,
            'argentinosjrs': 458,
            'aris thessalonikis': 1123,
            'aristhessalonikis': 1123,
            'arouca': 240,
            'as': 377,
            'as roma': 497,
            'asan mugunghwa': 2753,
            'asanmugunghwa': 2753,
            'asl': 2314,
            'asroma': 497,
            'astana': 562,
            'asteras tripolis': 955,
            'asterastripolis': 955,
            'aston villa': 66,
            'astonvilla': 66,
            'at': 455,
            'atalanta': 499,
            'athletic club': 531,
            'athleticclub': 531,
            'atlanta united fc': 1608,
            'atlantaunitedfc': 1608,
            'atlas': 2283,
            'atletico': 530,
            'atletico goianiense': 144,
            'atletico madrid': 530,
            'atletico paranaense': 134,
            'atletico san luis': 2314,
            'atletico tucuman': 455,
            'atleticogoianiense': 144,
            'atleticomadrid': 530,
            'atleticomg': 1062,
            'atleticoparanaense': 134,
            'atleticosanluis': 2314,
            'atleticotucuman': 455,
            'atlètic club descaldes': 3345,
            'atlèticclubdescaldes': 3345,
            'atromitos': 12260,
            'au': 1387,
            'auckland': 24608,
            'auda': 4135,
            'auf': 1608,
            'augsburg': 170,
            'aurora': 3637,
            'austin': 16489,
            'austria klagenfurt': 1405,
            'austria vienna': 601,
            'austriaklagenfurt': 1405,
            'austriavienna': 601,
            'auxerre': 108,
            'av': 601,
            'avispa fukuoka': 316,
            'avispafukuoka': 316,
            'avs': 21595,
            'ayr utd': 1387,
            'ayrutd': 1387,
            'az alkmaar': 201,
            'azalkmaar': 201,
            'b36 torshavn': 678,
            'b36torshavn': 678,
            'bahia': 118,
            'bala town': 352,
            'balatown': 352,
            'ballkani': 12733,
            'banfield': 449,
            'baník ostrava': 3713,
            'baníkostrava': 3713,
            'barcelona': 529,
            'bari': 508,
            'barracas central': 2432,
            'barracascentral': 2432,
            'bastia': 1305,
            'bayer leverkusen': 168,
            'bayerleverkusen': 168,
            'bayern münchen': 157,
            'bayernmünchen': 157,
            'bb': 3583,
            'bb bodrumspor': 3583,
            'bbbodrumspor': 3583,
            'bbl': 3364,
            'bc': 2432,
            'bd': 165,
            'beerschot wilrijk': 263,
            'beerschotwilrijk': 263,
            'beijing guoan': 830,
            'beijingguoan': 830,
            'belgrano cordoba': 440,
            'belgranocordoba': 440,
            'benfica': 211,
            'bg': 830,
            'bh': 367,
            'bj': 451,
            'bk hacken': 367,
            'bkhacken': 367,
            'bl': 168,
            'blooming': 3701,
            'bm': 163,
            'bo': 3713,
            'boavista': 222,
            'boca juniors': 451,
            'bocajuniors': 451,
            'bodoglimt': 327,
            'bologna': 500,
            'bolívar': 3702,
            'borac banja luka': 3364,
            'boracbanjaluka': 3364,
            'borussia dortmund': 165,
            'borussia mönchengladbach': 163,
            'borussiadortmund': 165,
            'borussiamönchengladbach': 163,
            'botafogo': 120,
            'botev plovdiv': 634,
            'botevplovdiv': 634,
            'boulogne': 1299,
            'bournemouth': 35,
            'bp': 579,
            'br': 947,
            'braga': 217,
            'brann': 319,
            'bravo': 4359,
            'breidablik': 276,
            'brentford': 55,
            'brescia': 518,
            'brighton': 51,
            'brisbane roar': 947,
            'brisbaneroar': 947,
            'brondby': 407,
            'brugge kv': 569,
            'bsc young boys': 565,
            'bscyoungboys': 565,
            'bt': 678,
            'buducnost podgorica': 579,
            'buducnostpodgorica': 579,
            'bw': 263,
            'bw linz': 1394,
            'byb': 565,
            'c1': 1426,
            'c1c': 2246,
            'ca': 2295,
            'caen': 88,
            'caernarfon town': 356,
            'caernarfontown': 356,
            'cagliari': 490,
            'cambuur': 420,
            'carrarese': 1581,
            'casa pia': 4716,
            'casapia': 4716,
            'catanzaro': 1687,
            'cb': 741,
            'cbc': 5648,
            'cbk': 569,
            'cc': 1613,
            'ccds': 1065,
            'ccm': 941,
            'celje': 4360,
            'celta vigo': 538,
            'celtavigo': 538,
            'celtic': 247,
            'central coast mariners': 941,
            'central cordoba de santiago': 1065,
            'centralcoastmariners': 941,
            'centralcordobadesantiago': 1065,
            'cercle brugge': 741,
            'cerclebrugge': 741,
            'cerezo osaka': 291,
            'cerezoosaka': 291,
            'cesena': 509,
            'cf': 99,
            'cf montreal': 1614,
            'cfmontreal': 1614,
            'cfr 1907 cluj': 2246,
            'cfr1907cluj': 2246,
            'ch': 20034,
            'changchun yatai': 834,
            'changchunyatai': 834,
            'charleroi': 736,
            'charlotte': 18310,
            'chengdu better city': 5648,
            'chengdubettercity': 5648,
            'cherno more varna': 851,
            'chernomorevarna': 851,
            'chicago fire': 1607,
            'chicagofire': 1607,
            'cincinnati': 2242,
            'cittadella': 510,
            'clermont foot': 99,
            'clermontfoot': 99,
            'cliftonville fc': 2266,
            'cliftonvillefc': 2266,
            'club america': 2287,
            'club brugge kv': 569,
            'club queretaro': 2290,
            'club tijuana': 2280,
            'clubamerica': 2287,
            'clubbruggekv': 569,
            'clubqueretaro': 2290,
            'clubtijuana': 2280,
            'cm': 1614,
            'cmv': 851,
            'co': 291,
            'colorado rapids': 1610,
            'coloradorapids': 1610,
            'columbus crew': 1613,
            'columbuscrew': 1613,
            'como': 895,
            'consadole sapporo': 279,
            'consadolesapporo': 279,
            'copenhagen': 400,
            'corinthians': 131,
            'corvinul hunedoara': 20034,
            'corvinulhunedoara': 20034,
            'cosenza': 10137,
            'cp': 4716,
            'cq': 2290,
            'cr': 1610,
            'cremonese': 520,
            'criciuma': 140,
            'crusaders fc': 697,
            'crusadersfc': 697,
            'cruz azul': 2295,
            'cruzazul': 2295,
            'cruzeiro': 135,
            'crystal palace': 52,
            'crystalpalace': 52,
            'cs': 279,
            'cska 1948': 1426,
            'cska1948': 1426,
            'ct': 2280,
            'cuiaba': 1193,
            'cv': 538,
            'cy': 834,
            'daegu fc': 2747,
            'daegufc': 2747,
            'daejeon citizen': 2750,
            'daejeoncitizen': 2750,
            'dallas': 1597,
            'db': 705,
            'dc': 2750,
            'dc united': 1615,
            'dcunited': 1615,
            'de graafschap': 199,
            'defensa y justicia': 442,
            'defensayjusticia': 442,
            'degraafschap': 199,
            'den bosch': 421,
            'denbosch': 421,
            'dender': 6215,
            'deportivo riestra': 476,
            'deportivoriestra': 476,
            'derry city': 670,
            'derrycity': 670,
            'dečić': 3745,
            'df': 2747,
            'dg': 199,
            'di': 364,
            'differdange 03': 684,
            'dinamo batumi': 705,
            'dinamo minsk': 394,
            'dinamo tbilisi': 2262,
            'dinamo zagreb': 620,
            'dinamobatumi': 705,
            'dinamominsk': 394,
            'dinamotbilisi': 2262,
            'dinamozagreb': 620,
            'djurgardens if': 364,
            'djurgardensif': 364,
            'dk': 572,
            'dm': 394,
            'dnipro1': 3623,
            'dordrecht': 409,
            'dr': 476,
            'drita': 14281,
            'ds': 2257,
            'dt': 2262,
            'du': 1386,
            'dunajska streda': 2257,
            'dunajskastreda': 2257,
            'dundee': 253,
            'dundee utd': 1386,
            'dundeeutd': 1386,
            'dunkerque': 1304,
            'dyj': 442,
            'dynamo kyiv': 572,
            'dynamokyiv': 572,
            'dz': 620,
            'ef': 169,
            'egnatia rrogozhinë': 3327,
            'egnatiarrogozhinë': 3327,
            'eintracht frankfurt': 169,
            'eintrachtfrankfurt': 169,
            'el': 450,
            'empoli': 511,
            'er': 3327,
            'espanyol': 540,
            'estac troyes': 110,
            'estactroyes': 110,
            'estoril': 230,
            'estrela': 15130,
            'estudiantes lp': 450,
            'estudianteslp': 450,
            'et': 110,
            'everton': 45,
            'eyüpspor': 3588,
            'f91 dudelange': 578,
            'f91dudelange': 578,
            'fa': 562,
            'famalicao': 242,
            'farense': 231,
            'fbl': 1394,
            'fc': 2242,
            'fc astana': 562,
            'fc augsburg': 170,
            'fc bw linz': 1394,
            'fc cincinnati': 2242,
            'fc copenhagen': 400,
            'fc dallas': 1597,
            'fc differdange 03': 684,
            'fc isloch minsk r': 391,
            'fc juarez': 2298,
            'fc levadia tallinn': 2273,
            'fc lugano': 606,
            'fc midtjylland': 397,
            'fc noah': 3684,
            'fc nordsjaelland': 398,
            'fc porto': 212,
            'fc seoul': 2766,
            'fc st gallen': 1011,
            'fc st pauli': 186,
            'fc tokyo': 292,
            'fc urartu': 2276,
            'fc vaduz': 660,
            'fc zurich': 783,
            'fcastana': 562,
            'fcaugsburg': 170,
            'fcbwlinz': 1394,
            'fccincinnati': 2242,
            'fccopenhagen': 400,
            'fcdallas': 1597,
            'fcdifferdange03': 684,
            'fcislochminskr': 391,
            'fcjuarez': 2298,
            'fclevadiatallinn': 2273,
            'fclugano': 606,
            'fcmidtjylland': 397,
            'fcnoah': 3684,
            'fcnordsjaelland': 398,
            'fcporto': 212,
            'fcsb': 559,
            'fcseoul': 2766,
            'fcstgallen': 1011,
            'fcstpauli': 186,
            'fctokyo': 292,
            'fcurartu': 2276,
            'fcvaduz': 660,
            'fcz': 598,
            'fczurich': 783,
            'fd': 1597,
            'fd0': 684,
            'fe': 154,
            'fehérvár fc': 610,
            'fehérvárfc': 610,
            'ferencvarosi tc': 651,
            'ferencvarositc': 651,
            'feyenoord': 209,
            'ff': 610,
            'fimr': 391,
            'fiorentina': 502,
            'fj': 2298,
            'fk crvena zvezda': 598,
            'fk liepaja': 661,
            'fk partizan': 573,
            'fk sarajevo': 679,
            'fk tobol kostanay': 2259,
            'fk zalgiris vilnius': 586,
            'fkcrvenazvezda': 598,
            'fkliepaja': 661,
            'fkpartizan': 573,
            'fksarajevo': 679,
            'fktobolkostanay': 2259,
            'fkzalgirisvilnius': 586,
            'fl': 661,
            'flamengo': 127,
            'flora tallinn': 687,
            'floratallinn': 687,
            'floriana': 4625,
            'flt': 2273,
            'fluminense': 124,
            'fm': 397,
            'fm0': 164,
            'fn': 398,
            'fortaleza ec': 154,
            'fortalezaec': 154,
            'fortuna sittard': 205,
            'fortunasittard': 205,
            'fp': 573,
            'fredrikstad': 2149,
            'freiburg': 160,
            'frosinone': 512,
            'fs': 2766,
            'fsg': 1011,
            'fsp': 186,
            'fsv mainz 05': 164,
            'fsvmainz05': 164,
            'ft': 292,
            'ftk': 2259,
            'fu': 2276,
            'fulham': 36,
            'fv': 660,
            'fz': 783,
            'fzv': 586,
            'ga': 4256,
            'gae': 410,
            'gais': 2170,
            'gamba osaka': 293,
            'gambaosaka': 293,
            'gangwon fc': 2746,
            'gangwonfc': 2746,
            'gap connah s quay fc': 357,
            'gapconnahsquayfc': 357,
            'gazişehir gaziantep': 3573,
            'gazişehirgaziantep': 3573,
            'gc': 2278,
            'gcsqf': 357,
            'genk': 742,
            'genoa': 495,
            'gent': 631,
            'getafe': 546,
            'gf': 2759,
            'gg': 3573,
            'gil vicente': 762,
            'gilvicente': 762,
            'gimcheon sangmu fc': 2768,
            'gimcheonsangmufc': 2768,
            'gimnasia lp': 434,
            'gimnasialp': 434,
            'girona': 547,
            'gl': 434,
            'go': 293,
            'go ahead eagles': 410,
            'goaheadeagles': 410,
            'godoy cruz': 439,
            'godoycruz': 439,
            'goztepe': 994,
            'grazer ak': 4256,
            'grazerak': 4256,
            'gremio': 130,
            'grenoble': 101,
            'groningen': 202,
            'gsf': 2768,
            'guabirá': 3704,
            'guadalajara chivas': 2278,
            'guadalajarachivas': 2278,
            'gualberto villarroel sj': 22266,
            'gualbertovillarroelsj': 22266,
            'guimaraes': 224,
            'guingamp': 90,
            'gv': 762,
            'gvs': 22266,
            'gwangju fc': 2759,
            'gwangjufc': 2759,
            'halmstad': 766,
            'hamkam': 2159,
            'hammarby ff': 363,
            'hammarbyff': 363,
            'hamrun spartans': 4626,
            'hamrunspartans': 4626,
            'hangzhou greentown': 848,
            'hangzhougreentown': 848,
            'hapoel beer sheva': 563,
            'hapoelbeersheva': 563,
            'hatayspor': 3575,
            'haugesund': 328,
            'hb': 4133,
            'hbs': 563,
            'hd': 1600,
            'heart of midlothian': 254,
            'heartofmidlothian': 254,
            'heerenveen': 210,
            'henan jianye': 840,
            'henanjianye': 840,
            'heracles': 206,
            'hf': 363,
            'hg': 848,
            'hh': 649,
            'hhs': 608,
            'hibernian': 249,
            'hj': 840,
            'hjk helsinki': 649,
            'hjkhelsinki': 649,
            'hk': 191,
            'hnk hajduk split': 608,
            'hnk rijeka': 561,
            'hnkhajduksplit': 608,
            'hnkrijeka': 561,
            'holstein kiel': 191,
            'holsteinkiel': 191,
            'hom': 254,
            'houston dynamo': 1600,
            'houstondynamo': 1600,
            'hr': 561,
            'hs': 4626,
            'huracan': 445,
            'ib': 371,
            'ic': 478,
            'icd': 3342,
            'ie': 372,
            'if brommapojkarna': 371,
            'if elfsborg': 372,
            'ifbrommapojkarna': 371,
            'ifelfsborg': 372,
            'ifk goteborg': 366,
            'ifk norrkoping': 378,
            'ifk varnamo': 2163,
            'ifkgoteborg': 366,
            'ifknorrkoping': 378,
            'ifkvarnamo': 2163,
            'ig': 366,
            'ilves': 1163,
            'im': 9568,
            'in': 378,
            'incheon united': 2763,
            'incheonunited': 2763,
            'independ rivadavia': 473,
            'independiente': 453,
            'independiente petrolero': 15702,
            'independientepetrolero': 15702,
            'independrivadavia': 473,
            'instituto cordoba': 478,
            'institutocordoba': 478,
            'inter club descaldes': 3342,
            'inter miami': 9568,
            'interclubdescaldes': 3342,
            'intermiami': 9568,
            'internacional': 119,
            'ip': 15702,
            'ipswich': 57,
            'ir': 473,
            'isloch minsk r': 391,
            'istanbul basaksehir': 564,
            'istanbulbasaksehir': 564,
            'iu': 2763,
            'iv': 2163,
            'jagiellonia': 336,
            'jeju united fc': 2761,
            'jejuunitedfc': 2761,
            'jeonbuk motors': 2762,
            'jeonbukmotors': 2762,
            'ji': 280,
            'jm': 2762,
            'jorge wilstermann': 3705,
            'jorgewilstermann': 3705,
            'js': 863,
            'juarez': 2298,
            'jubilo iwata': 280,
            'jubiloiwata': 280,
            'juf': 2761,
            'juve stabia': 863,
            'juventude': 152,
            'juventus': 496,
            'juvestabia': 863,
            'jw': 3705,
            'kallithea': 2095,
            'kalmar ff': 374,
            'kalmarff': 374,
            'kansas city': 1611,
            'kashima': 290,
            'kashiwa reysol': 281,
            'kashiwareysol': 281,
            'kasimpasa': 1004,
            'kawasaki frontale': 294,
            'kawasakifrontale': 294,
            'kayserispor': 1001,
            'kb': 320,
            'kf': 374,
            'kfum oslo': 2143,
            'kfumoslo': 2143,
            'ki klaksvik': 701,
            'kiklaksvik': 701,
            'kilmarnock': 250,
            'kk': 6489,
            'km': 266,
            'ko': 2143,
            'konyaspor': 607,
            'kortrijk': 734,
            'kr': 281,
            'kristiansund bk': 320,
            'kristiansundbk': 320,
            'kryvbas kr': 6489,
            'kryvbaskr': 6489,
            'ks': 302,
            'kups': 1165,
            'kv mechelen': 266,
            'kvc westerlo': 261,
            'kvcwesterlo': 261,
            'kvmechelen': 266,
            'kw': 261,
            'kyoto sanga': 302,
            'kyotosanga': 302,
            'la fiorita': 2249,
            'laf': 1616,
            'lafiorita': 2249,
            'lag': 1605,
            'lamia': 956,
            'landskrona bois': 2176,
            'landskronabois': 2176,
            'lanus': 446,
            'larne': 5354,
            'las palmas': 534,
            'lask linz': 1026,
            'lasklinz': 1026,
            'laspalmas': 534,
            'laval': 433,
            'lazio': 487,
            'lb': 2176,
            'le havre': 111,
            'lecce': 867,
            'leganes': 537,
            'legia warszawa': 339,
            'legiawarszawa': 339,
            'lehavre': 111,
            'leicester': 46,
            'lens': 116,
            'leon': 2289,
            'levadia tallinn': 2273,
            'levadiakos': 957,
            'lf': 2249,
            'lh': 111,
            'lille': 79,
            'lillestrom': 321,
            'lincoln red imps fc': 667,
            'lincolnredimpsfc': 667,
            'linfield': 583,
            'livingston': 255,
            'll': 1026,
            'llapi': 14395,
            'lorient': 97,
            'los angeles fc': 1616,
            'los angeles galaxy': 1605,
            'losangelesfc': 1616,
            'losangelesgalaxy': 1605,
            'lp': 534,
            'lrif': 667,
            'ludogorets': 566,
            'lugano': 606,
            'lw': 339,
            'lyngby': 625,
            'lyon': 80,
            'ma': 2240,
            'macarthur': 15550,
            'maccabi haifa': 4195,
            'maccabi petah tikva': 4495,
            'maccabi tel aviv': 604,
            'maccabihaifa': 4195,
            'maccabipetahtikva': 4495,
            'maccabitelaviv': 604,
            'machida zelvia': 303,
            'machidazelvia': 303,
            'magpies': 16135,
            'malisheva': 15576,
            'mallorca': 798,
            'malmo ff': 375,
            'malmoff': 375,
            'manchester city': 50,
            'manchester united': 33,
            'manchestercity': 50,
            'manchesterunited': 33,
            'mancity': 50,
            'mantova': 1693,
            'manutd': 33,
            'maribor': 552,
            'marsaxlokk': 14507,
            'marseille': 81,
            'martigues': 3200,
            'mazatlán': 14002,
            'mb': 640,
            'mc': 945,
            'meizhou kejia': 1439,
            'meizhoukejia': 1439,
            'melbourne city': 945,
            'melbourne victory': 944,
            'melbournecity': 945,
            'melbournevictory': 944,
            'metz': 112,
            'mf': 375,
            'mh': 4195,
            'midtjylland': 397,
            'milsami orhei': 691,
            'milsamiorhei': 691,
            'minnesota united fc': 1612,
            'minnesotaunitedfc': 1612,
            'mjallby aif': 2240,
            'mjallbyaif': 2240,
            'mk': 1439,
            'mlada boleslav': 640,
            'mladaboleslav': 640,
            'mo': 691,
            'modena': 899,
            'molde': 329,
            'monaco': 91,
            'monterrey': 2282,
            'montpellier': 82,
            'montreal': 1614,
            'monza': 1579,
            'moreirense': 215,
            'mornar': 3740,
            'moss': 7012,
            'motherwell': 256,
            'mpt': 4495,
            'mta': 604,
            'mu': 33,
            'muf': 1612,
            'mv': 944,
            'mz': 303,
            'nac breda': 203,
            'nacbreda': 203,
            'nacional': 225,
            'nacional potosí': 3706,
            'nacionalpotosí': 3706,
            'nagoya grampus': 288,
            'nagoyagrampus': 288,
            'nantes': 83,
            'nantong zhiyun': 2626,
            'nantongzhiyun': 2626,
            'napoli': 492,
            'nashville sc': 9569,
            'nashvillesc': 9569,
            'nb': 203,
            'nec nijmegen': 413,
            'necaxa': 2288,
            'necnijmegen': 413,
            'neman': 387,
            'ner': 1609,
            'new england revolution': 1609,
            'new york city fc': 1604,
            'new york red bulls': 1602,
            'newcastle': 34,
            'newcastle jets': 946,
            'newcastlejets': 946,
            'newells old boys': 457,
            'newellsoldboys': 457,
            'newenglandrevolution': 1609,
            'newyorkcityfc': 1604,
            'newyorkredbulls': 1602,
            'nf': 65,
            'ng': 288,
            'nice': 84,
            'nj': 946,
            'nk osijek': 616,
            'nkosijek': 616,
            'nn': 413,
            'no': 616,
            'noah': 3684,
            'nob': 457,
            'nordsjaelland': 398,
            'nottingham forest': 65,
            'nottinghamforest': 65,
            'np': 3706,
            'ns': 9569,
            'nycf': 1604,
            'nyrb': 1602,
            'nz': 2626,
            'ob': 330,
            'ocs': 1598,
            'odd ballklubb': 330,
            'oddballklubb': 330,
            'ofi': 1124,
            'oh leuven': 260,
            'ohleuven': 260,
            'ol': 677,
            'olimpija ljubljana': 677,
            'olimpijaljubljana': 677,
            'olympiakos piraeus': 553,
            'olympiakospiraeus': 553,
            'omonia nicosia': 3402,
            'omonianicosia': 3402,
            'on': 3402,
            'op': 3707,
            'ordabasy': 692,
            'oriente petrolero': 3707,
            'orientepetrolero': 3707,
            'orlando city sc': 1598,
            'orlandocitysc': 1598,
            'osasuna': 727,
            'pa': 2391,
            'pachuca': 2292,
            'pafos': 3403,
            'paide': 3528,
            'paks': 2390,
            'palermo': 522,
            'palmeiras': 121,
            'panathinaikos': 617,
            'panetolikos': 949,
            'panevėžys': 3874,
            'panserraikos': 2099,
            'paok': 619,
            'paris fc': 114,
            'paris saint germain': 85,
            'parisfc': 114,
            'parissaintgermain': 85,
            'parma': 523,
            'partick': 901,
            'partizani': 708,
            'patro eisden': 6222,
            'patroeisden': 6222,
            'pau': 1297,
            'pe': 6222,
            'pec zwolle': 193,
            'peczwolle': 193,
            'perth glory': 940,
            'perthglory': 940,
            'petrocub': 2271,
            'pf': 114,
            'pg': 940,
            'philadelphia union': 1599,
            'philadelphiaunion': 1599,
            'pisa': 801,
            'platense': 1064,
            'plzen': 567,
            'pn': 658,
            'pohang steelers': 2764,
            'pohangsteelers': 2764,
            'polessya': 6496,
            'portland timbers': 1617,
            'portlandtimbers': 1617,
            'porto': 212,
            'progres niederkorn': 658,
            'progresniederkorn': 658,
            'ps': 2764,
            'psv eindhoven': 197,
            'psveindhoven': 197,
            'pt': 1617,
            'pu': 1599,
            'puebla': 2291,
            'puskas academy': 2391,
            'puskasacademy': 2391,
            'py': 709,
            'pyunik yerevan': 709,
            'pyunikyerevan': 709,
            'pz': 193,
            'qarabag': 556,
            'qingdao jonoon': 1431,
            'qingdao youth island': 17265,
            'qingdaojonoon': 1431,
            'qingdaoyouthisland': 17265,
            'qj': 1431,
            'queretaro': 2290,
            'qyi': 17265,
            'r1': 2644,
            'ra': 226,
            'racing club': 436,
            'racingclub': 436,
            'radnicki 1923': 2644,
            'radnicki1923': 2644,
            'randers fc': 401,
            'randersfc': 401,
            'rangers': 257,
            'rapid vienna': 781,
            'rapidvienna': 781,
            'rayo vallecano': 728,
            'rayovallecano': 728,
            'rb': 794,
            'rb bragantino': 794,
            'rb leipzig': 173,
            'rbbragantino': 794,
            'rbleipzig': 173,
            'rbs': 571,
            'rc': 902,
            'real betis': 543,
            'real madrid': 541,
            'real oruro': 20252,
            'real salt lake': 1606,
            'real sociedad': 548,
            'real tomayapo': 15708,
            'realbetis': 543,
            'realmadrid': 541,
            'realoruro': 20252,
            'realsaltlake': 1606,
            'realsociedad': 548,
            'realtomayapo': 15708,
            'red bull salzburg': 571,
            'red star fc 93': 104,
            'redbullsalzburg': 571,
            'redstarfc93': 104,
            'reggiana': 880,
            'reims': 93,
            'rennes': 94,
            'rf': 401,
            'riga': 10124,
            'rio ave': 226,
            'rioave': 226,
            'river plate': 435,
            'riverplate': 435,
            'rizespor': 1007,
            'rl': 173,
            'rm': 541,
            'ro': 20252,
            'rodez': 1301,
            'rosario central': 437,
            'rosariocentral': 437,
            'rosenborg': 331,
            'ross county': 902,
            'rosscounty': 902,
            'royal pari': 3709,
            'royalpari': 3709,
            'rp': 3709,
            'rs': 548,
            'rsf9': 104,
            'rsl': 1606,
            'rt': 15708,
            'ružomberok': 3549,
            'rv': 781,
            'rīgas fs': 4160,
            'rīgasfs': 4160,
            's0f': 333,
            'sa': 618,
            'sabah fa': 13976,
            'sabahfa': 13976,
            'sabb': 17760,
            'saburtalo': 3502,
            'sagan tosu': 295,
            'sagantosu': 295,
            'saint etienne': 1063,
            'saintetienne': 1063,
            'salernitana': 514,
            'sampdoria': 498,
            'samsunspor': 3603,
            'san antonio bulo bulo': 17760,
            'san jose earthquakes': 1596,
            'san lorenzo': 460,
            'sanantoniobulobulo': 17760,
            'sandefjord': 332,
            'sanfrecce hiroshima': 282,
            'sanfreccehiroshima': 282,
            'sanjoseearthquakes': 1596,
            'sanlorenzo': 460,
            'santa clara': 227,
            'santa cruz': 12259,
            'santaclara': 227,
            'santacruz': 12259,
            'santos laguna': 2285,
            'santoslaguna': 2285,
            'sao paulo': 126,
            'saopaulo': 126,
            'sarmiento junin': 474,
            'sarmientojunin': 474,
            'sarpsborg 08 ff': 333,
            'sarpsborg08ff': 333,
            'sassuolo': 488,
            'sb': 284,
            'sb2': 106,
            'sc': 12259,
            'sc braga': 217,
            'sc freiburg': 160,
            'scbraga': 217,
            'scf': 2756,
            'scfreiburg': 160,
            'scr altach': 618,
            'scraltach': 618,
            'sd': 550,
            'se': 1063,
            'seattle sounders': 1595,
            'seattlesounders': 1595,
            'sef': 2749,
            'seoul': 2766,
            'seoul eland fc': 2749,
            'seoulelandfc': 2749,
            'servette fc': 2184,
            'servettefc': 2184,
            'sevilla': 536,
            'sf': 13976,
            'sg': 637,
            'sh': 282,
            'shakhtar donetsk': 550,
            'shakhtardonetsk': 550,
            'shamrock rovers': 652,
            'shamrockrovers': 652,
            'shandong luneng': 844,
            'shandongluneng': 844,
            'shanghai shenhua': 833,
            'shanghai sipg': 836,
            'shanghaishenhua': 833,
            'shanghaisipg': 836,
            'shelbourne': 3854,
            'sheriff tiraspol': 568,
            'sherifftiraspol': 568,
            'shijiazhuang y j': 849,
            'shijiazhuangyj': 849,
            'shkendija': 609,
            'shonan bellmare': 284,
            'shonanbellmare': 284,
            'sichuan jiuniu': 5686,
            'sichuanjiuniu': 5686,
            'silkeborg': 2073,
            'sirius': 370,
            'sivasspor': 1002,
            'sj': 5686,
            'sje': 1596,
            'sjsf': 698,
            'skc': 1611,
            'sl': 844,
            'slask wroclaw': 337,
            'slaskwroclaw': 337,
            'slavia praha': 560,
            'slaviapraha': 560,
            'slc': 20787,
            'sliema wanderers': 4628,
            'sliemawanderers': 4628,
            'slovan bratislava': 656,
            'slovanbratislava': 656,
            'sm': 251,
            'sonderjyske': 396,
            'southampton': 41,
            'sp': 126,
            'spa': 3843,
            'sparta praha': 628,
            'sparta rotterdam': 426,
            'spartak trnava': 1120,
            'spartaktrnava': 1120,
            'spartapraha': 628,
            'spartarotterdam': 426,
            'spezia': 515,
            'sporting cp': 228,
            'sporting kansas city': 1611,
            'sportingcp': 228,
            'sportingkansascity': 1611,
            'sr': 652,
            'ss': 836,
            'st': 295,
            'st gallen': 1011,
            'st johnstone': 258,
            'st joseph s fc': 698,
            'st louis city': 20787,
            'st mirren': 251,
            'st patricks athl': 3843,
            'st pauli': 186,
            'st truiden': 735,
            'stade brestois 29': 106,
            'stadebrestois29': 106,
            'standard liege': 733,
            'standardliege': 733,
            'stjarnan': 275,
            'stjohnstone': 258,
            'stjosephsfc': 698,
            'stlouiscity': 20787,
            'stmirren': 251,
            'stpatricksathl': 3843,
            'strasbourg': 95,
            'stromsgodset': 324,
            'struga': 4346,
            'sttruiden': 735,
            'sturm graz': 637,
            'sturmgraz': 637,
            'sudtirol': 1578,
            'sumqayıt': 5503,
            'suwon city fc': 2756,
            'suwoncityfc': 2756,
            'sv elversberg': 1660,
            'svelversberg': 1660,
            'sw': 4628,
            'sydney': 943,
            'syj': 849,
            'talleres cordoba': 456,
            'tallerescordoba': 456,
            'tallinna kalev': 3529,
            'tallinnakalev': 3529,
            'tbt': 2646,
            'tc': 456,
            'telstar': 427,
            'tf': 1601,
            'th': 1072,
            'the new saints': 354,
            'the strongest': 3711,
            'thenewsaints': 354,
            'thestrongest': 3711,
            'tianjin teda': 837,
            'tianjinteda': 837,
            'tigre': 452,
            'tigres uanl': 2279,
            'tigresuanl': 2279,
            'tijuana': 2280,
            'tikveš': 4348,
            'tirana': 694,
            'tk': 3529,
            'tns': 354,
            'tokyo': 292,
            'tokyo verdy': 306,
            'tokyoverdy': 306,
            'toluca': 2281,
            'torino': 503,
            'toronto fc': 1601,
            'torontofc': 1601,
            'torpedo kutaisi': 685,
            'torpedo zhodino': 385,
            'torpedokutaisi': 685,
            'torpedozhodino': 385,
            'tottenham': 47,
            'toulouse': 96,
            'tp': 700,
            'transinvest vilnius': 18878,
            'transinvestvilnius': 18878,
            'tre penne': 700,
            'trepenne': 700,
            'tromso': 325,
            'ts': 3711,
            'tsc backa topola': 2646,
            'tscbackatopola': 2646,
            'tsv hartberg': 1072,
            'tsvhartberg': 1072,
            'tt': 837,
            'tu': 2279,
            'tv': 306,
            'twente': 415,
            'tz': 385,
            'ub': 182,
            'uc': 632,
            'udinese': 494,
            'udv': 17762,
            'ue santa coloma': 703,
            'uesantacoloma': 703,
            'uhf': 2767,
            'ulsan hyundai fc': 2767,
            'ulsanhyundaifc': 2767,
            'una strassen': 2036,
            'unam pumas': 2286,
            'unampumas': 2286,
            'unastrassen': 2036,
            'union berlin': 182,
            'union santa fe': 441,
            'union st gilloise': 1393,
            'unionberlin': 182,
            'unionsantafe': 441,
            'unionstgilloise': 1393,
            'universitario de vinto': 17762,
            'universitariodevinto': 17762,
            'universitatea craiova': 632,
            'universitateacraiova': 632,
            'up': 2286,
            'urartu': 2276,
            'urawa': 287,
            'us': 2036,
            'usc': 703,
            'usf': 441,
            'usg': 1393,
            'utrecht': 207,
            'vaduz': 660,
            'valencia': 532,
            'valladolid': 720,
            'valur reykjavik': 274,
            'valurreykjavik': 274,
            'vancouver whitecaps': 1603,
            'vancouverwhitecaps': 1603,
            'vasco da gama': 133,
            'vascodagama': 133,
            'vasteras sk fk': 2241,
            'vasterasskfk': 2241,
            'vb': 176,
            'vdg': 133,
            'vejle': 395,
            'velez sarsfield': 438,
            'velezsarsfield': 438,
            'velež': 3381,
            'venezia': 517,
            'verona': 504,
            'vfb stuttgart': 172,
            'vfbstuttgart': 172,
            'vfl bochum': 176,
            'vfl wolfsburg': 161,
            'vflbochum': 176,
            'vflwolfsburg': 161,
            'vg': 580,
            'viborg': 2070,
            'viking': 759,
            'vikingur gota': 580,
            'vikingur reykjavik': 278,
            'vikingurgota': 580,
            'vikingurreykjavik': 278,
            'villarreal': 533,
            'virtus': 5308,
            'vissel kobe': 289,
            'visselkobe': 289,
            'vitoria': 136,
            'vizela': 810,
            'vk': 289,
            'vllaznia shkodër': 3339,
            'vllazniashkodër': 3339,
            'vn': 2110,
            'vojvodina': 702,
            'volos nfc': 2110,
            'volosnfc': 2110,
            'vps': 650,
            'vr': 274,
            'vs': 438,
            'vsf': 2241,
            'vw': 1603,
            'wa': 1025,
            'waalwijk': 417,
            'wb': 162,
            'wellington phoenix': 942,
            'wellingtonphoenix': 942,
            'werder bremen': 162,
            'werderbremen': 162,
            'west ham': 48,
            'western sydney wanderers': 939,
            'western united': 7573,
            'westernsydneywanderers': 939,
            'westernunited': 7573,
            'westham': 48,
            'wh': 48,
            'wi': 195,
            'willem ii': 195,
            'willemii': 195,
            'wisla krakow': 338,
            'wislakrakow': 338,
            'wk': 338,
            'wolfsberger ac': 1025,
            'wolfsbergerac': 1025,
            'wolves': 39,
            'wp': 942,
            'wsg wattens': 1398,
            'wsgwattens': 1398,
            'wsw': 939,
            'wtt': 5695,
            'wu': 7573,
            'wuhan three towns': 5695,
            'wuhanthreetowns': 5695,
            'ww': 1398,
            'yfm': 296,
            'yokohama f marinos': 296,
            'yokohamafmarinos': 296,
            'zimbru': 4633,
            'zira': 648,
            'zrinjski': 588,
            'zurich': 783,
            'šiauliai': 3870,
        }
        
        team_lower = team_input.strip().lower()
        
        # Quick lookup first
        if team_lower in team_mappings:
            team_id = team_mappings[team_lower]
            response, error = make_api_request(api_key, base_url, "teams", {'id': team_id}, skip_limit=True)
            # make_api_request zaten response kısmını döndürüyor
            if response and len(response) > 0:
                team_raw = response[0]  # Bu: {'team': {...}, 'venue': {...}}
                team_info = team_raw['team'] if 'team' in team_raw else team_raw
                return format_team_data(team_info)
        
        # Strategy 2: API search by name (with enhanced debugging)
        print(f"🔍 API arama başlatılıyor: '{team_input}'")
        response, error = make_api_request(api_key, base_url, "teams", {'search': team_input}, skip_limit=True)
        
        print(f"📡 API Yanıtı - Error: {error}")
        print(f"📡 API Yanıtı - Response exists: {bool(response)}")
        
        if error and "429" in str(error):
            print("⚠️ API limit reached - trying extended mapping")
            # API limit reached - use extended fallback mapping
            try:
                from extended_team_mapping import get_extended_team_mappings, find_team_in_extended_mapping
                extended_mappings = get_extended_team_mappings()
                fallback_team = find_team_in_extended_mapping(team_lower, extended_mappings)
                if fallback_team:
                    print(f"✅ Cached mapping found for {team_input}")
                    return fallback_team
            except ImportError:
                print("❌ Extended mapping module not found")
        
        if error:
            print(f"❌ API Error: {error}")
            # Try fallback mapping even on other errors
            if team_lower in team_mappings:
                team_id = team_mappings[team_lower]
                print(f"🔄 Using direct mapping fallback for {team_input} -> ID {team_id}")
                return {
                    'id': team_id,
                    'name': team_input.title(),
                    'country': 'Unknown',
                    'logo': None
                }
            return None
        
        if not response:
            print(f"❌ No response for {team_input}")
            return None
        
        # make_api_request zaten response kısmını döndürüyor
        teams = response  # Bu direkt liste: [{'team': {...}, 'venue': {...}}, ...]
        print(f"📊 Found {len(teams)} teams")
        
        if not teams or len(teams) == 0:
            print(f"❌ No teams found for {team_input}")
            # Fallback to direct mapping if available
            if team_lower in team_mappings:
                team_id = team_mappings[team_lower]
                print(f"🔄 Using direct mapping fallback -> ID {team_id}")
                return {
                    'id': team_id,
                    'name': team_input.title(),
                    'country': 'Unknown',  
                    'logo': None
                }
            return None
        
        # Return first result - FIXED based on API test
        team_raw = teams[0]  # This is: {'team': {...}, 'venue': {...}}
        print(f"🎯 Team raw data type: {type(team_raw)}")
        
        # Based on API test, format is: {'team': {...}, 'venue': {...}}
        if isinstance(team_raw, dict) and 'team' in team_raw:
            team_info = team_raw['team']
            print(f"✅ Extracted team_info: {team_info.get('name')} (ID: {team_info.get('id')})")
            return format_team_data(team_info)
        else:
            print(f"❌ Unexpected API response format: {team_raw}")
            return None
        
    except Exception as e:
        print(f"Team search error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def get_extended_team_mappings() -> Dict[str, Dict[str, Any]]:
    """Extended team mappings for fallback when API limit reached"""
    return {
        # Turkish teams
        'galatasaray': {'id': 645, 'name': 'Galatasaray', 'country': 'Turkey'},
        'gala': {'id': 645, 'name': 'Galatasaray', 'country': 'Turkey'},
        'gs': {'id': 645, 'name': 'Galatasaray', 'country': 'Turkey'},
        'fenerbahce': {'id': 646, 'name': 'Fenerbahce', 'country': 'Turkey'},
        'fenerbahçe': {'id': 646, 'name': 'Fenerbahce', 'country': 'Turkey'},
        'fener': {'id': 646, 'name': 'Fenerbahce', 'country': 'Turkey'},
        'fb': {'id': 646, 'name': 'Fenerbahce', 'country': 'Turkey'},
        'besiktas': {'id': 644, 'name': 'Besiktas', 'country': 'Turkey'},
        'beşiktaş': {'id': 644, 'name': 'Besiktas', 'country': 'Turkey'},
        'bjk': {'id': 644, 'name': 'Besiktas', 'country': 'Turkey'},
        'trabzonspor': {'id': 643, 'name': 'Trabzonspor', 'country': 'Turkey'},
        'trabzon': {'id': 643, 'name': 'Trabzonspor', 'country': 'Turkey'},
        'istanbul basaksehir': {'id': 609, 'name': 'Istanbul Basaksehir', 'country': 'Turkey'},
        'basaksehir': {'id': 609, 'name': 'Istanbul Basaksehir', 'country': 'Turkey'},
        'antalyaspor': {'id': 558, 'name': 'Antalyaspor', 'country': 'Turkey'},
        'antalya': {'id': 558, 'name': 'Antalyaspor', 'country': 'Turkey'},
        
        # Major European teams
        'juventus': {'id': 496, 'name': 'Juventus', 'country': 'Italy'},
        'juve': {'id': 496, 'name': 'Juventus', 'country': 'Italy'},
        'barcelona': {'id': 529, 'name': 'Barcelona', 'country': 'Spain'},
        'barca': {'id': 529, 'name': 'Barcelona', 'country': 'Spain'},
        'real madrid': {'id': 541, 'name': 'Real Madrid', 'country': 'Spain'},
        'madrid': {'id': 541, 'name': 'Real Madrid', 'country': 'Spain'},
        'manchester united': {'id': 33, 'name': 'Manchester United', 'country': 'England'},
        'man united': {'id': 33, 'name': 'Manchester United', 'country': 'England'},
        'liverpool': {'id': 40, 'name': 'Liverpool', 'country': 'England'},
        'arsenal': {'id': 42, 'name': 'Arsenal', 'country': 'England'},
        'chelsea': {'id': 49, 'name': 'Chelsea', 'country': 'England'},
        'bayern munich': {'id': 157, 'name': 'Bayern Munich', 'country': 'Germany'},
        'bayern': {'id': 157, 'name': 'Bayern Munich', 'country': 'Germany'},
        'psg': {'id': 85, 'name': 'Paris Saint-Germain', 'country': 'France'},
        'paris': {'id': 85, 'name': 'Paris Saint-Germain', 'country': 'France'},
        'ac milan': {'id': 489, 'name': 'AC Milan', 'country': 'Italy'},
        'milan': {'id': 489, 'name': 'AC Milan', 'country': 'Italy'},
        'inter': {'id': 505, 'name': 'Inter Milan', 'country': 'Italy'},
        'inter milan': {'id': 505, 'name': 'Inter Milan', 'country': 'Italy'},
    }

def find_team_in_extended_mapping(team_lower: str, mappings: Dict[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Find team in extended mapping with fuzzy matching"""
    # Exact match first
    if team_lower in mappings:
        return format_team_data(mappings[team_lower])
    
    # Fuzzy match - check if input contains team name
    for key, data in mappings.items():
        if team_lower in key or key in team_lower:
            return format_team_data(data)
    
    return None

def format_team_data(team_info: Dict[str, Any]) -> Dict[str, Any]:
    """Format team data into consistent structure"""
    return {
        'id': team_info.get('id'),
        'name': team_info.get('name'),
        'logo': team_info.get('logo'),
        'country': team_info.get('country'),
        'founded': team_info.get('founded'),
        'venue_name': team_info.get('venue', {}).get('name') if team_info.get('venue') else None
    }

def format_team_response(team_info: Dict[str, Any]) -> Dict[str, Any]:
    """Format team info into standard response"""
    if STREAMLIT_AVAILABLE:
        st.sidebar.success(f"✅ Bulunan: {team_info['name']} ({team_info['id']})")
    
    return {
        'id': team_info['id'], 
        'name': team_info['name'], 
        'logo': team_info.get('logo'),
        'country': team_info.get('country'),
        'founded': team_info.get('founded'),
        'venue_name': team_info.get('venue', {}).get('name') if team_info.get('venue') else None
    }

def process_team_search_results(teams: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Process team search results with priority sorting"""
    if not teams:
        return None    # Priority order for popular teams
    popular_teams = [
        644, 645, 646, 643, 3569, 3568, 2833,  # Turkey
        33, 34, 40, 42, 47, 49, 50,  # England  
        529, 530, 531, 532, 533,  # Spain
        489, 487, 488, 492, 496, 500, 505,  # Italy
        157, 165, 173, 168, 172,  # Germany
        85, 79, 81, 80, 84,  # France
    ]
    
    def get_priority(team_item):
        # Handle different response formats
        if 'team' in team_item:
            team_id = team_item['team']['id']
        else:
            team_id = team_item.get('id', 0)
        
        if team_id in popular_teams:
            return popular_teams.index(team_id)
        return 999
    
    # Sort by priority if multiple results
    if len(teams) > 1:
        teams.sort(key=get_priority)
    
    # Extract team data from first result
    first_team = teams[0]
    if 'team' in first_team:
        team_data = first_team['team']
    else:
        team_data = first_team
    
    return format_team_response(team_data)

@st.cache_data(ttl=18000)
def get_team_injuries(api_key: str, base_url: str, team_id: int, fixture_id: Optional[int] = None) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
    """
    Takımın sakatlık ve ceza bilgilerini getirir.
    Returns: (injuries_list, error_message)
    """
    params = {'team': team_id}
    if fixture_id:
        params['fixture'] = fixture_id
    
    response, error = make_api_request(api_key, base_url, "injuries", params)
    if error:
        return None, error
    
    if not response:
        return [], None  # Sakatlık yok
    
    # Aktif sakatlıkları filtrele
    active_injuries = []
    for injury in response:
        player = injury.get('player', {})
        injury_type = injury.get('player', {}).get('type', 'Unknown')
        injury_reason = injury.get('player', {}).get('reason', 'N/A')
        
        active_injuries.append({
            'player_name': player.get('name', 'Unknown'),
            'player_id': player.get('id'),
            'type': injury_type,
            'reason': injury_reason
        })
    
    return active_injuries, None


# =============================================================================
# ADMIN YÖNETİM FONKSİYONLARI
# =============================================================================

def get_all_users_info() -> Dict[str, Any]:
    """
    Tüm kullanıcıların detaylı bilgilerini döndürür.
    Returns: {username: {name, email, tier, daily_limit, monthly_limit, usage_today, usage_month, ip_restricted}}
    """
    try:
        # Config.yaml'den kullanıcı bilgilerini al
        config_path = 'config.yaml'
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        users_info = {}
        usernames_data = config.get('credentials', {}).get('usernames', {})
        
        # Usage data'yı al
        usage_data = _read_usage_file()
        
        for username, user_data in usernames_data.items():
            user_usage = get_current_usage(username)
            
            # Günlük ve aylık limitler
            daily_limit = usage_data.get('_limits', {}).get(username, TIER_LIMITS.get(user_data.get('tier', 'ücretsiz')))
            monthly_limit = usage_data.get('_monthly_limits', {}).get(username, 0)
            
            users_info[username] = {
                'name': user_data.get('name', 'N/A'),
                'email': user_data.get('email', 'N/A'),
                'tier': user_data.get('tier', 'ücretsiz'),
                'daily_limit': daily_limit,
                'monthly_limit': monthly_limit if monthly_limit else None,
                'usage_today': user_usage.get('count', 0),
                'usage_month': user_usage.get('monthly_count', 0),
                'ip_restricted': user_data.get('ip_restricted', False),
                'allowed_ips': user_data.get('allowed_ips', [])
            }
        
        return users_info
    except Exception as e:
        print(f"[ERROR] get_all_users_info: {e}")
        return {}


def delete_user(username: str) -> Tuple[bool, str]:
    """
    Kullanıcıyı config.yaml'den siler.
    Returns: (success: bool, message: str)
    """
    try:
        config_path = 'config.yaml'
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if username not in config.get('credentials', {}).get('usernames', {}):
            return False, f"Kullanıcı '{username}' bulunamadı."
        
        del config['credentials']['usernames'][username]
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True)
        
        return True, f"Kullanıcı '{username}' başarıyla silindi."
    except Exception as e:
        return False, f"Kullanıcı silinirken hata oluştu: {e}"


def reset_user_password(username: str, new_password: str) -> Tuple[bool, str]:
    """
    Kullanıcının şifresini sıfırlar.
    Returns: (success: bool, message: str)
    """
    try:
        import streamlit_authenticator as stauth
        config_path = 'config.yaml'
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if username not in config.get('credentials', {}).get('usernames', {}):
            return False, f"Kullanıcı '{username}' bulunamadı."
        
        # Şifreyi hash'le
        hasher = stauth.Hasher()
        hashed_password = hasher.hash(new_password)
        
        config['credentials']['usernames'][username]['password'] = hashed_password
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True)
        
        return True, f"Kullanıcı '{username}' şifresi başarıyla güncellendi."
    except Exception as e:
        return False, f"Şifre güncellenirken hata oluştu: {e}"


def set_ip_restriction(username: str, enabled: bool, allowed_ips: list = None) -> Tuple[bool, str]:
    """
    Kullanıcı için IP kısıtlaması ayarlar.
    Args:
        username: Kullanıcı adı
        enabled: IP kısıtlaması aktif mi?
        allowed_ips: İzin verilen IP listesi (varsayılan: [])
    Returns: (success: bool, message: str)
    """
    try:
        config_path = 'config.yaml'
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if username not in config.get('credentials', {}).get('usernames', {}):
            return False, f"Kullanıcı '{username}' bulunamadı."
        
        config['credentials']['usernames'][username]['ip_restricted'] = enabled
        config['credentials']['usernames'][username]['allowed_ips'] = allowed_ips or []
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True)
        
        status = "aktif" if enabled else "pasif"
        return True, f"Kullanıcı '{username}' IP kısıtlaması {status} yapıldı."
    except Exception as e:
        return False, f"IP kısıtlaması ayarlanırken hata oluştu: {e}"


def check_ip_restriction(username: str, user_ip: str) -> Tuple[bool, str]:
    """
    Kullanıcının IP kısıtlaması var mı ve izinli mi kontrol eder.
    Returns: (allowed: bool, message: str)
    """
    try:
        config_path = 'config.yaml'
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        user_data = config.get('credentials', {}).get('usernames', {}).get(username, {})
        
        ip_restricted = user_data.get('ip_restricted', False)
        if not ip_restricted:
            return True, "IP kısıtlaması yok."
        
        allowed_ips = user_data.get('allowed_ips', [])
        if user_ip in allowed_ips:
            return True, "IP izinli."
        
        return False, f"IP adresi ({user_ip}) bu hesap için yetkilendirilmemiş."
    except Exception as e:
        return False, f"IP kontrolü yapılırken hata oluştu: {e}"


def add_admin_user(username: str) -> Tuple[bool, str]:
    """
    Kullanıcıyı admin listesine ekler.
    Returns: (success: bool, message: str)
    """
    try:
        config_path = 'config.yaml'
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Kullanıcının var olup olmadığını kontrol et
        if username not in config.get('credentials', {}).get('usernames', {}):
            return False, f"Kullanıcı '{username}' bulunamadı. Önce kullanıcı oluşturun."
        
        admin_users = config.get('admin_users', [])
        if username in admin_users:
            return False, f"Kullanıcı '{username}' zaten admin."
        
        admin_users.append(username)
        config['admin_users'] = admin_users
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True)
        
        return True, f"Kullanıcı '{username}' admin yetkisi aldı."
    except Exception as e:
        return False, f"Admin yetkisi verilirken hata oluştu: {e}"


def remove_admin_user(username: str) -> Tuple[bool, str]:
    """
    Kullanıcıdan admin yetkisini kaldırır.
    Returns: (success: bool, message: str)
    """
    try:
        config_path = 'config.yaml'
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        admin_users = config.get('admin_users', [])
        if username not in admin_users:
            return False, f"Kullanıcı '{username}' zaten admin değil."
        
        admin_users.remove(username)
        config['admin_users'] = admin_users
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True)
        
        return True, f"Kullanıcı '{username}' admin yetkisi kaldırıldı."
    except Exception as e:
        return False, f"Admin yetkisi kaldırılırken hata oluştu: {e}"


def get_admin_users() -> list:
    """
    Admin kullanıcı listesini döndürür.
    """
    try:
        config_path = 'config.yaml'
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config.get('admin_users', [])
    except Exception:
        return []


def export_usage_stats() -> Dict[str, Any]:
    """
    Tüm kullanıcıların kullanım istatistiklerini export eder.
    Returns: Dictionary with detailed usage stats
    """
    try:
        usage_data = _read_usage_file()
        all_users = get_all_users_info()
        
        export_data = {
            'export_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_users': len(all_users),
            'users': []
        }
        
        for username, info in all_users.items():
            export_data['users'].append({
                'username': username,
                'name': info['name'],
                'email': info['email'],
                'tier': info['tier'],
                'daily_limit': info['daily_limit'],
                'monthly_limit': info['monthly_limit'],
                'usage_today': info['usage_today'],
                'usage_month': info['usage_month'],
                'ip_restricted': info['ip_restricted']
            })
        
        return export_data
    except Exception as e:
        return {'error': str(e)}


def reset_all_daily_counters() -> Tuple[bool, str]:
    """
    Tüm kullanıcıların günlük sayaçlarını sıfırlar.
    Returns: (success: bool, message: str)
    """
    try:
        reset_daily_usage()
        return True, "Tüm günlük sayaçlar başarıyla sıfırlandı."
    except Exception as e:
        return False, f"Sayaçlar sıfırlanırken hata oluştu: {e}"


def reset_all_monthly_counters() -> Tuple[bool, str]:
    """
    Tüm kullanıcıların aylık sayaçlarını sıfırlar.
    Returns: (success: bool, message: str)
    """
    try:
        usage_data = _read_usage_file()
        today = datetime.now().date()
        
        for username in usage_data.keys():
            if not username.startswith('_'):
                usage_data[username]['monthly_count'] = 0
                usage_data[username]['month'] = today.strftime('%Y-%m')
        
        _write_usage_file(usage_data)
        return True, "Tüm aylık sayaçlar başarıyla sıfırlandı."
    except Exception as e:
        return False, f"Aylık sayaçlar sıfırlanırken hata oluştu: {e}"

# API Enhancement Functions - Yeni İşlevler

@st.cache_data(ttl=3600)  # 1 saat cache
def get_api_predictions(api_key: str, base_url: str, fixture_id: int) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """API-Football'un kendi tahminlerini getirir."""
    response, error = make_api_request(api_key, base_url, "predictions", {'fixture': fixture_id})
    if error:
        return None, error
    return (response[0], None) if response else (None, "API tahmini bulunamadı.")

@st.cache_data(ttl=3600)  # 1 saat cache
def get_betting_odds(api_key: str, base_url: str, fixture_id: int) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
    """Maç için bahis oranlarını getirir."""
    response, error = make_api_request(api_key, base_url, "odds", {'fixture': fixture_id})
    if error:
        return None, error
    return (response, None) if response else (None, "Bahis oranları bulunamadı.")

@st.cache_data(ttl=3600)  # 1 saat cache
def get_team_top_players(api_key: str, base_url: str, team_id: int, season: int) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
    """Takımın en iyi oyuncularını getirir."""
    response, error = make_api_request(api_key, base_url, "players", {'team': team_id, 'season': season})
    if error:
        return None, error
    return (response, None) if response else (None, "Oyuncu bilgileri bulunamadı.")

@st.cache_data(ttl=3600)  # 1 saat cache
def get_fixtures_lineups(api_key: str, base_url: str, fixture_id: int) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Maç kadro dizilimlerini getirir."""
    response, error = make_api_request(api_key, base_url, "fixtures/lineups", {'fixture': fixture_id})
    if error:
        return None, error
    return (response, None) if response else (None, "Kadro bilgileri bulunamadı.")

@st.cache_data(ttl=3600)  # 1 saat cache  
def get_fixture_players_stats(api_key: str, base_url: str, fixture_id: int) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
    """Maçtaki oyuncu performanslarını getirir."""
    response, error = make_api_request(api_key, base_url, "fixtures/players", {'fixture': fixture_id})
    if error:
        return None, error
    return (response, None) if response else (None, "Oyuncu performans bilgileri bulunamadı.")

@st.cache_data(ttl=86400)  # 24 saat cache
def get_team_transfers(api_key: str, base_url: str, team_id: int) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
    """Takımın son transferlerini getirir."""
    response, error = make_api_request(api_key, base_url, "transfers", {'team': team_id})
    if error:
        return None, error
    return (response, None) if response else (None, "Transfer bilgileri bulunamadı.")

@st.cache_data(ttl=86400)  # 24 saat cache
def get_league_top_scorers(api_key: str, base_url: str, league_id: int, season: int) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
    """Lig gol krallığı listesini getirir."""
    response, error = make_api_request(api_key, base_url, "players/topscorers", {'league': league_id, 'season': season})
    if error:
        return None, error
    return (response, None) if response else (None, "Gol krallığı bilgileri bulunamadı.")

@st.cache_data(ttl=86400)  # 24 saat cache
def get_league_top_assists(api_key: str, base_url: str, league_id: int, season: int) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
    """Lig asist krallığı listesini getirir."""
    response, error = make_api_request(api_key, base_url, "players/topassists", {'league': league_id, 'season': season})
    if error:
        return None, error
    return (response, None) if response else (None, "Asist krallığı bilgileri bulunamadı.")