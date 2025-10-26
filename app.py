# -*- coding: utf-8 -*-
# app.py

import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, List
import json

# --- ZAMANLANMIŞ GÖREV TETİKLEYİCİSİ ---
# Bu blok, uygulamanın en başında olmalıdır.
try:
    import daily_reset
    import update_elo

    # 1. ADIM: Bu gizli anahtarı tahmin edilmesi zor, size özel bir şeyle değiştirin.
    SCHEDULED_TASK_SECRET = "Elam1940*"

    # Uygulama URL'sine eklenen özel parametreleri kontrol et
    query_params = st.query_params
    if query_params.get("action") == "run_tasks" and query_params.get("secret") == SCHEDULED_TASK_SECRET:
        print("Zamanlanmış görevler tetiklendi.")
        st.write("Zamanlanmış görevler çalıştırılıyor...")
        
        try:
            daily_reset.run_daily_reset()
            st.write("Günlük sayaç sıfırlama tamamlandı.")
            print("Günlük sayaç sıfırlama tamamlandı.")
        except Exception as e:
            st.error(f"Günlük sayaç sıfırlama sırasında hata: {e}")
            print(f"Günlük sayaç sıfırlama sırasında hata: {e}")

        try:
            update_elo.run_elo_update()
            st.write("Elo reyting güncellemesi tamamlandı.")
            print("Elo reyting güncellemesi tamamlandı.")
        except Exception as e:
            st.error(f"Elo reyting güncellemesi sırasında hata: {e}")
            print(f"Elo reyting güncellemesi sırasında hata: {e}")
            
        st.success("Tüm görevler tamamlandı.")
        print("Tüm görevler tamamlandı.")
        # Görevler bittikten sonra uygulamanın geri kalanını yüklemeyi durdur
        st.stop()
except ImportError:
    # Proje ilk kurulduğunda bu dosyalar olmayabilir, hata vermesini engelle
    pass
# --- ZAMANLANMIŞ GÖREV BÖLÜMÜ SONU ---


# --- GEREKLİ KÜTÜPHANELER ---
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

import api_utils
import analysis_logic
from password_manager import change_password, change_email
import base64
import os
from enhanced_analysis import display_enhanced_match_analysis


def get_logo_base64():
    """Logo dosyasını base64 formatına çevirir"""
    logo_path = os.path.join(os.path.dirname(__file__), 'assets', 'logo.svg')
    try:
        with open(logo_path, 'r', encoding='utf-8') as f:
            svg_content = f.read()
        return base64.b64encode(svg_content.encode()).decode()
    except Exception as e:
        print(f"Logo yüklenemedi: {e}")
        return None


def display_logo(sidebar=False, size="medium"):
    """Logoyu gösterir
    Args:
        sidebar: Sidebar'da mı gösterilecek
        size: Logo boyutu - small (100px), medium (140px), large (200px)
    """
    logo_base64 = get_logo_base64()
    if not logo_base64:
        return
    
    sizes = {"small": 100, "medium": 140, "large": 200}
    width = sizes.get(size, 140)
    
    logo_html = f"""
    <div style='text-align: center; margin: 30px 0; padding: 20px;'>
        <img src='data:image/svg+xml;base64,{logo_base64}' width='{width}' 
             style='border-radius: 20px; box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4); 
                    border: 4px solid rgba(102, 126, 234, 0.2); transition: transform 0.3s ease;'>
    </div>
    """
    
    if sidebar:
        st.sidebar.markdown(logo_html, unsafe_allow_html=True)
    else:
        st.markdown(logo_html, unsafe_allow_html=True)


def safe_rerun():
    """Try to rerun the Streamlit script in a backwards/forwards compatible way."""
    try:
        rerun = getattr(st, 'rerun', None)
        if callable(rerun):
            return rerun()
    except Exception:
        pass
    try:
        from streamlit.runtime.scriptrunner.script_runner import RerunException
        raise RerunException()
    except Exception:
        st.stop()

def update_url_and_rerun(view_name):
    """URL'yi günceller ve sayfayı yeniler"""
    st.session_state.view = view_name
    st.query_params.update({"view": view_name})
    st.rerun()

# --- KONFİGÜRASYON ---
st.set_page_config(
    layout="wide", 
    page_title="⚽ Güvenilir Analiz",
    page_icon="⚽",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "# Güvenilir Analiz\n### Yapay Zeka Destekli Maç Tahmin Platformu"
    }
)

# API KEY'i önce environment variable'dan, sonra secrets'tan al (Railway uyumluluğu için)
import os
try:
    # Railway environment variables'dan al
    API_KEY = os.environ.get("API_KEY")
    
    if not API_KEY:
        # Lokal geliştirme için secrets'tan al
        try:
            API_KEY = st.secrets["API_KEY"]
        except:
            pass
        
    if not API_KEY:
        raise ValueError("API_KEY bulunamadı")
        
except Exception as e:
    st.error("⚠️ API_KEY bulunamadı. Railway'de environment variable olarak ayarlayın veya lokal geliştirme için `.streamlit/secrets.toml` dosyasını oluşturun.")
    st.stop()

BASE_URL = "https://v3.football.api-sports.io"

# Oturum kalıcılığı ve F5/geri tuşunda çıkış olmaması için session/cookie ayarları
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = None
if 'auth_time' not in st.session_state:
    st.session_state['auth_time'] = datetime.now()

def set_authenticated(username):
    st.session_state['authenticated'] = True
    st.session_state['username'] = username
    st.session_state['auth_time'] = datetime.now()

def is_authenticated():
    # 5 gün boyunca oturum açık kalsın (cookie expiry_days zaten 90)
    if st.session_state.get('authenticated', False):
        if (datetime.now() - st.session_state.get('auth_time', datetime.now())).days < 5:
            return True
    return False

INTERESTING_LEAGUES = {
    # Popüler Avrupa 1. Ligleri
    39: "🇬🇧 Premier League", 140: "🇪🇸 La Liga", 135: "🇮🇹 Serie A", 
    78: "🇩🇪 Bundesliga", 61: "🇫🇷 Ligue 1", 203: "🇹🇷 Süper Lig",
    88: "🇳🇱 Eredivisie", 94: "🇵🇹 Primeira Liga", 144: "🇧🇪 Pro League",
    106: "🇷🇺 Premier League", 197: "🇬🇷 Super League", 169: "🇵🇱 Ekstraklasa",
    333: "🇦🇹 Bundesliga", 218: "🇨🇿 1. Liga", 235: "🇷🇴 Liga I",
    271: "🇸🇪 Allsvenskan", 119: "🇩🇰 Superliga", 103: "🇳🇴 Eliteserien",
    179: "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Premiership", 283: "🇺🇦 Premier League", 345: "🇭🇷 1. HNL",
    318: "🇸🇰 Super Liga", 177: "🇧🇬 Parva Liga", 327: "🇷🇸 Super Liga",
    
    # Popüler Avrupa 2. Ligleri
    40: "🇬🇧 Championship", 141: "🇪🇸 La Liga 2", 136: "🇮🇹 Serie B", 
    79: "🇩🇪 2. Bundesliga", 62: "🇫🇷 Ligue 2", 204: "🇹🇷 TFF 1. Lig",
    89: "🇳🇱 Eerste Divisie", 95: "🇵🇹 Liga Portugal 2", 145: "🇧🇪 Challenger Pro",
    
    # UEFA Kupaları
    2: "🏆 UEFA Champions League", 3: "🏆 UEFA Europa League", 848: "🏆 UEFA Conference League",
    
    # Dünya Ligleri - Amerika
    253: "🇺🇸 Major League Soccer", 255: "🇺🇸 USL Championship",
    71: "🇧🇷 Serie A", 72: "🇧🇷 Serie B",
    128: "🇦🇷 Liga Profesional", 129: "🇦🇷 Primera Nacional",
    265: "�� Liga MX", 266: "🇲🇽 Liga Expansion",
    239: "�🇴 Primera A", 240: "🇨🇴 Primera B",
    242: "�� Liga Pro", 281: "🇵🇪 Primera Division",
    250: "�� Primera Division", 274: "🇺🇾 Primera Division",
    
    # Dünya Ligleri - Asya
    98: "🇯🇵 J1 League", 99: "🇯🇵 J2 League",
    292: "�� K League 1", 293: "🇰🇷 K League 2",
    307: "🇸🇦 Professional League", 955: "🇸🇦 Division 1",
    480: "�� Arabian Gulf League", 305: "🇶🇦 Stars League",
    301: "�� Iraqi League", 202: "🇮🇷 Persian Gulf Pro League",
    188: "🇨🇳 Super League", 340: "�� A-League",
    
    # Dünya Ligleri - Afrika
    302: "🇿🇦 Premier Division", 233: "🇪🇬 Premier League",
    
    # Dünya Ligleri - Diğer
    180: "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Championship", 667: "�󠁧󠁢󠁷󠁬󠁳󠁿 Premier League",
}

ADMIN_USERS = ['sivrii1940', 'admin']

# En Popüler 100 Lig (Admin paneli için)
TOP_100_POPULAR_LEAGUES = [
    # UEFA Kupaları (en önemli)
    2, 3, 848,
    # Top 6 Avrupa Ligleri
    39, 140, 135, 78, 61, 203,
    # Diğer Önemli Avrupa 1. Ligleri
    88, 94, 144, 106, 197, 169, 333, 218, 235, 271, 119, 103, 179, 283, 345, 318, 177, 327,
    # Avrupa 2. Ligleri
    40, 141, 136, 79, 62, 204, 89, 95, 145,
    # Amerika Ligleri
    253, 255, 71, 72, 128, 129, 265, 266, 239, 240, 242, 281, 250, 274,
    # Asya Ligleri
    98, 99, 292, 293, 307, 955, 480, 305, 301, 202, 188, 340,
    # Afrika ve Diğer
    302, 233, 180, 667,
    # Ek Önemli Ligler
    113, 114, 115, 116, 117, 118, 120, 121, 122, 123, 124, 125, 126, 127,
    130, 131, 132, 133, 134, 137, 138, 139, 142, 143, 146, 147, 148, 149,
    150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163
]

# Popüler Takımlar (ID bazlı - arama sonuçlarında öncelik verilir)
POPULAR_TEAM_IDS = [
    # Türkiye
    645, 646, 644, 643, 3569,  # Fenerbahçe, Beşiktaş, Galatasaray, Trabzonspor, Kasımpaşa
    # İngiltere
    33, 34, 40, 42, 47, 49, 50,  # Man United, Newcastle, Liverpool, Arsenal, Tottenham, Chelsea, Man City
    # İspanya
    529, 530, 531, 532, 533,  # Barcelona, Atletico, Real Madrid, Valencia, Sevilla
    # İtalya
    489, 487, 488, 492, 496, 500, 505,  # AC Milan, Inter, Juventus, Napoli, Lazio, Roma, Atalanta
    # Almanya
    157, 165, 173, 168, 172,  # Bayern München, Dortmund, RB Leipzig, Leverkusen, Stuttgart
    # Fransa
    85, 79, 81, 80, 84,  # PSG, Marseille, Monaco, Lyon, Lille
    # Portekiz
    210, 211, 212, 228,  # Porto, Benfica, Sporting Lizbon, Braga
    # Hollanda
    194, 200, 202,  # Ajax, PSV, Feyenoord
    # Diğer Önemli
    211, 212, 529, 530, 531, 85, 157,  # Tekrar vurgulananlar
]

# Popüler Lig Öncelik Sırası (sayısal sıralama için)
LEAGUE_POPULARITY_ORDER = {
    # En Popüler (Tier 1)
    203: 1, 39: 2, 140: 3, 135: 4, 78: 5, 61: 6,  # Süper Lig, Premier, La Liga, Serie A, Bundesliga, Ligue 1
    # UEFA Kupaları
    2: 7, 3: 8, 848: 9,
    # Diğer Önemli Avrupa 1. Ligleri (Tier 2)
    88: 10, 94: 11, 144: 12, 197: 13, 169: 14, 106: 15,
    # Avrupa 2. Ligleri (Tier 3)
    40: 16, 141: 17, 136: 18, 79: 19, 62: 20, 204: 21,
}

def get_league_priority(league_id: int) -> int:
    """Lig için öncelik sırası döner (düşük sayı = yüksek öncelik)"""
    return LEAGUE_POPULARITY_ORDER.get(league_id, 999)

def get_team_priority(team_id: int) -> int:
    """Takım için öncelik sırası döner (düşük sayı = yüksek öncelik)"""
    if team_id in POPULAR_TEAM_IDS:
        return POPULAR_TEAM_IDS.index(team_id)
    return 999

DEFAULT_LEAGUES = INTERESTING_LEAGUES.copy()
LEGACY_LEAGUE_NAMES = {name: lid for lid, name in DEFAULT_LEAGUES.items()}

def _fallback_season_year() -> int:
    today = date.today()
    return today.year if today.month >= 7 else today.year - 1

@st.cache_data(ttl=86400)
def load_league_catalog(api_key: str, base_url: str):
    leagues, error = api_utils.get_all_current_leagues(api_key, base_url)
    if leagues:
        normalized = []
        for entry in leagues:
            display = entry.get('display') or f"{entry.get('country') or 'Uluslararası'} - {entry.get('name')}"
            normalized.append({**entry, 'display': display})
        return normalized, error

    fallback_season = _fallback_season_year()
    fallback_catalog = [{
        'id': lid,
        'name': name,
        'country': 'Bilinmiyor',
        'type': 'League',
        'season': fallback_season,
        'display': name
    } for lid, name in DEFAULT_LEAGUES.items()]
    fallback_error = error or "Dinamik lig listesi yüklenemedi; varsayılan liste kullanılıyor."
    return fallback_catalog, fallback_error


try:
    LEAGUE_CATALOG, LEAGUE_LOAD_ERROR = load_league_catalog(API_KEY, BASE_URL)
except Exception as exc:  # Streamlit dışı koşullarda güvenli geri dönüş
    fallback_season = _fallback_season_year()
    LEAGUE_CATALOG = [{
        'id': lid,
        'name': name,
        'country': 'Bilinmiyor',
        'type': 'League',
        'season': fallback_season,
        'display': name
    } for lid, name in DEFAULT_LEAGUES.items()]
    LEAGUE_LOAD_ERROR = f"Lig kataloğu dinamik olarak yüklenemedi ({exc}). Varsayılan liste kullanılıyor."
INTERESTING_LEAGUES = {item['id']: item['display'] for item in LEAGUE_CATALOG}
LEAGUE_METADATA = {item['id']: item for item in LEAGUE_CATALOG}
LEAGUE_NAME_TO_ID = {display: lid for lid, display in INTERESTING_LEAGUES.items()}
COUNTRY_INDEX = sorted({item.get('country', 'Uluslararası') for item in LEAGUE_CATALOG})

def get_league_id_from_display(label: Optional[str]) -> Optional[int]:
    if not label:
        return None
    return LEAGUE_NAME_TO_ID.get(label) or LEGACY_LEAGUE_NAMES.get(label)

def resolve_season_for_league(league_id: int) -> int:
    info = LEAGUE_METADATA.get(league_id)
    if info and info.get('season'):
        return int(info['season'])
    return _fallback_season_year()

def get_default_favorite_leagues() -> List[str]:
    preferred_ids = [203, 39, 140]
    favorites = [INTERESTING_LEAGUES.get(lid) for lid in preferred_ids if INTERESTING_LEAGUES.get(lid)]
    if not favorites:
        favorites = list(INTERESTING_LEAGUES.values())[:3]
    return favorites

def save_user_favorite_leagues(username: str, leagues: List[str]):
    """Kullanıcının favori liglerini config.yaml'e kaydeder"""
    try:
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if 'credentials' not in config:
            config['credentials'] = {}
        if 'usernames' not in config['credentials']:
            config['credentials']['usernames'] = {}
        
        if username in config['credentials']['usernames']:
            config['credentials']['usernames'][username]['favorite_leagues'] = leagues
            
            with open('config.yaml', 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
            return True
        return False
    except Exception as e:
        print(f"Favori ligler kaydedilemedi: {e}")
        return False

def load_user_favorite_leagues(username: str) -> Optional[List[str]]:
    """Kullanıcının favori liglerini config.yaml'den yükler"""
    try:
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if 'credentials' in config and 'usernames' in config['credentials']:
            if username in config['credentials']['usernames']:
                return config['credentials']['usernames'][username].get('favorite_leagues')
        return None
    except Exception:
        return None

def normalize_league_labels(labels: Optional[List[str]]) -> List[str]:
    if not labels:
        return []
    normalized: List[str] = []
    for label in labels:
        if label in INTERESTING_LEAGUES.values():
            normalized.append(label)
            continue
        legacy_id = LEGACY_LEAGUE_NAMES.get(label)
        if legacy_id:
            current_label = INTERESTING_LEAGUES.get(legacy_id)
            if current_label:
                normalized.append(current_label)
    # Sıralamayı koruyarak tekrarları kaldır
    seen = set()
    deduped = []
    for label in normalized:
        if label not in seen:
            deduped.append(label)
            seen.add(label)
    return deduped

LIG_ORTALAMA_GOL = 1.35
DEFAULT_MAX_GOAL_EXPECTANCY, DEFAULT_KEY_PLAYER_IMPACT_MULTIPLIER, BEST_BET_THRESHOLD, H2H_MATCH_LIMIT = 2.5, 0.85, 30.0, 10
TOP_GOAL_BET_THRESHOLD = 65.0 

# --- YARDIMCI GÖRÜNÜM FONKSİYONLARI ---

def display_team_with_logo(team_name: str, logo_url: str = None, size: int = 30):
    """Takım adını logosuyla birlikte gösterir"""
    if logo_url:
        return f'<img src="{logo_url}" width="{size}" style="vertical-align: middle; margin-right: 8px;"/>{team_name}'
    return team_name

def display_best_bet_card(title: str, match_data: pd.Series, prediction_label: str, prediction_value: str, metric_label: str, metric_value: str):
    with st.container(border=True):
        st.markdown(f"<h5 style='text-align: center;'>{title}</h5>", unsafe_allow_html=True)
        # Logoları ekle
        home_logo = match_data.get('home_logo', '')
        away_logo = match_data.get('away_logo', '')
        home_with_logo = display_team_with_logo(match_data['Ev Sahibi'], home_logo, size=25)
        away_with_logo = display_team_with_logo(match_data['Deplasman'], away_logo, size=25)
        st.markdown(f"<div style='text-align: center; margin: 10px 0;'>{home_with_logo} vs {away_with_logo}</div>", unsafe_allow_html=True)
        st.metric(prediction_label, prediction_value)
        st.metric(metric_label, metric_value)

        
def display_summary_tab(analysis: Dict, team_names: Dict, odds_data: Optional[Dict], model_params: Dict, team_logos: Optional[Dict] = None):
    name_a, name_b = team_names['a'], team_names['b']
    logo_a = team_logos.get('a', '') if team_logos else ''
    logo_b = team_logos.get('b', '') if team_logos else ''
    
    score_a, score_b, probs, confidence, diff = analysis['score_a'], analysis['score_b'], analysis['probs'], analysis['confidence'], analysis['diff']
    max_prob_key = max(probs, key=lambda k: probs[k] if 'win' in k or 'draw' in k else -1)
    decision = f"{name_a} Kazanır" if max_prob_key == 'win_a' else f"{name_b} Kazanır" if max_prob_key == 'win_b' else "Beraberlik"
    
    # Takım logoları ve isimlerini başlık olarak göster
    if logo_a and logo_b:
        col_logo_a, col_vs, col_logo_b = st.columns([2, 1, 2])
        with col_logo_a:
            st.markdown(f"""
            <div style='text-align: center;'>
                <img src='{logo_a}' width='80' style='border-radius: 50%; border: 2px solid #667eea;'>
                <h3 style='margin-top: 10px;'>{name_a}</h3>
                <p style='color: #888; font-size: 0.9em;'>Ev Sahibi</p>
            </div>
            """, unsafe_allow_html=True)
        with col_vs:
            st.markdown("<h2 style='text-align: center; margin-top: 40px;'>⚔️ VS ⚔️</h2>", unsafe_allow_html=True)
        with col_logo_b:
            st.markdown(f"""
            <div style='text-align: center;'>
                <img src='{logo_b}' width='80' style='border-radius: 50%; border: 2px solid #764ba2;'>
                <h3 style='margin-top: 10px;'>{name_b}</h3>
                <p style='color: #888; font-size: 0.9em;'>Deplasman</p>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("---")
    
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Ev S. Gol Beklentisi", f"{score_a:.2f}")
    c2.metric("Dep. Gol Beklentisi", f"{score_b:.2f}")
    c3.metric("Toplam Gol Beklentisi", f"{analysis.get('expected_total', score_a + score_b):.2f}")
    c4.metric("Olasılık Farkı", f"{diff:.1f}%")
    c5.metric("AI Güven Puanı", f"**{confidence:.1f}**")
    params = analysis.get('params', {})
    st.caption(f"Beklenen gol farkı (ev - dep): {analysis.get('goal_spread', score_a - score_b):+.2f} | Elo farkı: {params.get('elo_diff', 0):+.0f} | Tempo endeksi: x{params.get('pace_index', 1.0):.2f}")
    st.info(f"**Ana Karar (1X2):** {decision}")
    if analysis.get('reasons'):
        with st.expander("🕵️‍♂️ Tahminin Arkasındaki Nedenleri Gör"):
            for reason in analysis['reasons']: st.markdown(f"- {reason}")
    st.markdown("---")
    st.subheader("📊 Model Olasılıkları ve Piyasa Karşılaştırması")
    # Olasılıklar zaten yüzde formatında geliyor
    model_probs = [analysis['probs']['win_a'], analysis['probs']['draw'], analysis['probs']['win_b']]
    if odds_data:
        market_odds = [odds_data['home']['odd'], odds_data['draw']['odd'], odds_data['away']['odd']]
        market_probs = [odds_data['home']['prob'], odds_data['draw']['prob'], odds_data['away']['prob']]
        value_threshold = model_params.get('value_threshold', 5)
        value_tags = [f"✅ Değerli Oran! (+{model_p - market_p:.1f}%)" if model_p > market_p + value_threshold else "" for model_p, market_p in zip(model_probs, market_probs)]
        comparison_df = pd.DataFrame({'Sonuç': [f"{name_a} Kazanır", "Beraberlik", f"{name_b} Kazanır"], 'Model Olasılığı (%)': model_probs, 'Piyasa Ort. Oranı': market_odds, 'Piyasa Olasılığı (%)': market_probs, 'Değer Analizi': value_tags})
        st.dataframe(comparison_df.style.format({'Model Olasılığı (%)': '{:.1f}', 'Piyasa Ort. Oranı': '{:.2f}', 'Piyasa Olasılığı (%)': '{:.1f}'}).apply(lambda x: ['background-color: #285238' if 'Değerli' in x.iloc[4] else '' for i in x], axis=1), hide_index=True, use_container_width=True)
    else:
        st.warning("Bu maç için oran verisi bulunamadı.")
        st.markdown("##### 🏆 Maç Sonu (1X2) Model Olasılıkları")
        chart_data = pd.DataFrame({'Olasılık (%)': {f'{name_a} K.': model_probs[0], 'Ber.': model_probs[1], f'{name_b} K.': model_probs[2]}})
        st.bar_chart(chart_data)
    st.markdown("---")
    st.subheader("⚽ Gol Piyasaları (Model Tahmini)")
    # Olasılıklar zaten yüzde formatında geliyor
    gol_data = pd.DataFrame({'Kategori': ['2.5 ÜST', '2.5 ALT', 'KG VAR', 'KG YOK'], 'İhtimal (%)': [analysis['probs']['ust_2.5'], analysis['probs']['alt_2.5'], analysis['probs']['kg_var'], analysis['probs']['kg_yok']]}).set_index('Kategori')
    st.dataframe(gol_data.style.format("{:.1f}"), use_container_width=True)

def display_stats_tab(stats: Dict, team_names: Dict, team_ids: Dict, params: Optional[Dict] = None):
    name_a, name_b, id_a, id_b = team_names['a'], team_names['b'], team_ids['a'], team_ids['b']
    
    # 🆕 Form Grafikleri - Son 5 Maç
    if params and (params.get('form_string_a') or params.get('form_string_b')):
        st.subheader("📈 Son 5 Maçın Form Trendi")
        col_form_a, col_form_b = st.columns(2)
        
        def display_form_badges(form_string: str, team_name: str, column):
            with column:
                st.markdown(f"**{team_name}**")
                if not form_string:
                    st.info("Form verisi yok")
                    return
                
                # Form badge'lerini oluştur
                badges_html = "<div style='display: flex; gap: 8px; justify-content: center; margin: 10px 0;'>"
                for char in form_string:
                    if char == 'W':
                        badge = "<span style='background-color: #28a745; color: white; padding: 8px 12px; border-radius: 5px; font-weight: bold;'>G</span>"
                    elif char == 'D':
                        badge = "<span style='background-color: #6c757d; color: white; padding: 8px 12px; border-radius: 5px; font-weight: bold;'>B</span>"
                    else:  # L
                        badge = "<span style='background-color: #dc3545; color: white; padding: 8px 12px; border-radius: 5px; font-weight: bold;'>M</span>"
                    badges_html += badge
                badges_html += "</div>"
                st.markdown(badges_html, unsafe_allow_html=True)
                
                # İstatistik hesapla
                wins = form_string.count('W')
                draws = form_string.count('D')
                losses = form_string.count('L')
                total = len(form_string)
                points = (wins * 3) + draws
                st.metric("Puan", f"{points}/{total*3}", help=f"{wins}G - {draws}B - {losses}M")
        
        display_form_badges(params.get('form_string_a', ''), name_a, col_form_a)
        display_form_badges(params.get('form_string_b', ''), name_b, col_form_b)
        st.markdown("---")
    
    st.subheader("📊 İstatistiksel Karşılaştırma Grafiği (Radar)")
    stats_a_home = stats['a'].get('home', {}); stats_b_away = stats['b'].get('away', {})
    
    # Eğer istatistikler boşsa varsayılan değerler kullan
    default_goals_scored = 1.2
    default_goals_conceded = 1.2
    default_stability = 50
    
    categories = ['Atılan Gol', 'Yenen Gol', 'İstikrar']
    values_a = [
        stats_a_home.get('Ort. Gol ATILAN', default_goals_scored), 
        stats_a_home.get('Ort. Gol YENEN', default_goals_conceded), 
        stats_a_home.get('Istikrar_Puani', default_stability)
    ]
    values_b = [
        stats_b_away.get('Ort. Gol ATILAN', default_goals_scored), 
        stats_b_away.get('Ort. Gol YENEN', default_goals_conceded), 
        stats_b_away.get('Istikrar_Puani', default_stability)
    ]
    
    # Eğer tüm değerler varsayılan ise uyarı göster
    if values_a == [default_goals_scored, default_goals_conceded, default_stability] and \
       values_b == [default_goals_scored, default_goals_conceded, default_stability]:
        st.warning("⚠️ Bu takımlar için bu sezon detaylı istatistik verisi bulunamadı. Analiz genel verilere dayanıyor.")
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=values_a, theta=categories, fill='toself', name=f'{name_a} (Ev)'))
    fig.add_trace(go.Scatterpolar(r=values_b, theta=categories, fill='toself', name=f'{name_b} (Dep)'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True)), showlegend=True, height=350, margin=dict(l=40, r=40, t=40, b=40))
    st.plotly_chart(fig, use_container_width=True)
    st.info("Not: 'Yenen Gol' metriğinde daha düşük değerler daha iyidir.")
    st.markdown("---")
    st.subheader("📈 Genel Form İstatistikleri ve Son Maçlar")
    col1_form, col2_form = st.columns(2)
    with col1_form:
        st.markdown(f"**{name_a} - Son 10 Maç Formu**")
        form_a = api_utils.get_team_form_sequence(API_KEY, BASE_URL, id_a)
        if form_a:
            results = [r['result'] for r in form_a]; colors = [{'G': 'green', 'B': 'gray', 'M': 'red'}[r] for r in results]
            hover_texts = [f"Rakip: {r['opponent']}<br>Skor: {r['score']}" for r in form_a]
            fig_a = go.Figure(data=go.Scatter(x=list(range(1, len(results) + 1)), y=results, mode='markers', marker=dict(color=colors, size=15), hoverinfo='text', hovertext=hover_texts))
            fig_a.update_layout(yaxis_title=None, xaxis_title="Oynanan Maçlar (Eskiden Yeniye)", height=250, margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig_a, use_container_width=True)
    with col2_form:
        st.markdown(f"**{name_b} - Son 10 Maç Formu**")
        form_b = api_utils.get_team_form_sequence(API_KEY, BASE_URL, id_b)
        if form_b:
            results = [r['result'] for r in form_b]; colors = [{'G': 'green', 'B': 'gray', 'M': 'red'}[r] for r in results]
            hover_texts = [f"Rakip: {r['opponent']}<br>Skor: {r['score']}" for r in form_b]
            fig_b = go.Figure(data=go.Scatter(x=list(range(1, len(results) + 1)), y=results, mode='markers', marker=dict(color=colors, size=15), hoverinfo='text', hovertext=hover_texts))
            fig_b.update_layout(yaxis_title=None, xaxis_title="Oynanan Maçlar (Eskiden Yeniye)", height=250, margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig_b, use_container_width=True)
    st.markdown("---")
    def format_stats(stat_dict):
        if not stat_dict or not any(stat_dict.values()):
            return {"Bilgi": "Bu sezon için veri bulunamadı"}
        filtered_dict = {k: v for k, v in stat_dict.items() if k != 'team_specific_home_adv'}
        return {k.replace('_', ' ').title(): f"{v:.2f}" for k, v in filtered_dict.items()} if filtered_dict else {"Bilgi": "Veri bulunamadı"}
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**{name_a}**")
        st.write("**Ev Sahibi Olarak:**")
        home_stats_a = format_stats(stats['a'].get('home'))
        if "Bilgi" in home_stats_a:
            st.info(home_stats_a["Bilgi"])
        else:
            st.dataframe(pd.Series(home_stats_a), use_container_width=True)
        
        st.write("**Deplasmanda Olarak:**")
        away_stats_a = format_stats(stats['a'].get('away'))
        if "Bilgi" in away_stats_a:
            st.info(away_stats_a["Bilgi"])
        else:
            st.dataframe(pd.Series(away_stats_a), use_container_width=True)
    with c2:
        st.markdown(f"**{name_b}**")
        st.write("**Ev Sahibi Olarak:**")
        home_stats_b = format_stats(stats['b'].get('home'))
        if "Bilgi" in home_stats_b:
            st.info(home_stats_b["Bilgi"])
        else:
            st.dataframe(pd.Series(home_stats_b), use_container_width=True)
        
        st.write("**Deplasmanda Olarak:**")
        away_stats_b = format_stats(stats['b'].get('away'))
        if "Bilgi" in away_stats_b:
            st.info(away_stats_b["Bilgi"])
        else:
            st.dataframe(pd.Series(away_stats_b), use_container_width=True)

def display_injuries_tab(fixture_id: int, team_names: Dict, team_ids: Dict, league_info: Dict):
    st.subheader("❗ Maç Öncesi Önemli Eksikler")
    injuries, error = api_utils.get_fixture_injuries(API_KEY, BASE_URL, fixture_id)
    if error: 
        st.warning(f"Sakatlık verisi çekilemedi: {error}")
    elif not injuries: 
        st.success("✅ Takımlarda önemli bir eksik bildirilmedi.")
    else:
        team_a_inj = [p for p in injuries if p['team']['id'] == team_ids['a']]
        team_b_inj = [p for p in injuries if p['team']['id'] == team_ids['b']]
        season = league_info['season']
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**{team_names['a']}**")
            if team_a_inj: 
                for p in team_a_inj:
                    player_id = p['player']['id']
                    player_stats_data, _ = api_utils.get_player_stats(API_KEY, BASE_URL, player_id, season)
                    stats_str = analysis_logic.process_player_stats(player_stats_data) or ""
                    st.warning(f"**{p['player']['name']}** - {p['player']['reason']}{stats_str}")
            else: 
                st.write("Eksik yok.")
        with c2:
            st.markdown(f"**{team_names['b']}**")
            if team_b_inj: 
                for p in team_b_inj:
                    player_id = p['player']['id']
                    player_stats_data, _ = api_utils.get_player_stats(API_KEY, BASE_URL, player_id, season)
                    stats_str = analysis_logic.process_player_stats(player_stats_data) or ""
                    st.warning(f"**{p['player']['name']}** - {p['player']['reason']}{stats_str}")
            else: 
                st.write("Eksik yok.")

def display_standings_tab(league_info: Dict, team_names: Dict):
    st.subheader("🏆 Lig Puan Durumu")
    standings_data, error = api_utils.get_league_standings(API_KEY, BASE_URL, league_info['league_id'], league_info['season'])
    if error: st.warning(f"Puan durumu çekilemedi: {error}")
    elif standings_data:
        df = pd.DataFrame(standings_data)[['rank', 'team', 'points', 'goalsDiff', 'form']].rename(columns={'rank':'Sıra', 'team':'Takım', 'points':'Puan', 'goalsDiff':'Averaj', 'form':'Form'})
        df['Takım'] = df['Takım'].apply(lambda x: x['name'])
        def highlight(row):
            if row.Takım == team_names['a']: return ['background-color: lightblue'] * len(row)
            if row.Takım == team_names['b']: return ['background-color: lightcoral'] * len(row)
            return [''] * len(row)
        st.dataframe(df.style.apply(highlight, axis=1), hide_index=True, use_container_width=True)
    else: st.warning("Bu lig için puan durumu verisi bulunamadı.")

def display_referee_tab(referee_stats: Optional[Dict]):
    st.subheader("⚖️ Hakem İstatistikleri")
    if referee_stats:
        st.info(f"Maçın hakemi: **{referee_stats['name']}**")
        if referee_stats.get('total_games') != "N/A":
            c1, c2, c3 = st.columns(3)
            c1.metric("Yönettiği Maç Sayısı", referee_stats['total_games'])
            c2.metric("Maç Başına Sarı Kart", f"{referee_stats['yellow_per_game']:.2f}")
            c3.metric("Maç Başına Kırmızı Kart", f"{referee_stats['red_per_game']:.2f}")
        else:
            st.warning("Bu hakemin detaylı istatistikleri bu sezon için bulunamadı.")
    else:
        st.warning("Bu maç için hakem bilgisi atanmamış veya bulunamadı.")

def display_detailed_betting_tab(analysis: Dict, team_names: Dict, fixture_id: int, model_params: Dict):
    """🎲 Detaylı İddaa Tahminleri - Model vs Piyasa Karşılaştırması"""
    st.subheader("🎲 Detaylı İddaa Tahminleri ve Piyasa Karşılaştırması")
    
    # Piyasa oranlarını çek
    with st.spinner("Piyasa oranları alınıyor..."):
        detailed_odds, error = api_utils.get_fixture_detailed_odds(API_KEY, BASE_URL, fixture_id)
    
    if error:
        st.warning(f"⚠️ Detaylı piyasa oranları alınamadı: {error}")
        st.info("💡 Model tahminlerini göstermeye devam ediyoruz, ancak piyasa karşılaştırması yapılamayacak.")
        detailed_odds = None
    elif not detailed_odds:
        st.warning("⚠️ Bu maç için detaylı bahis oranları bulunamadı.")
        st.info("💡 Muhtemelen yaklaşan bir maç veya bahis şirketleri henüz oran açmamış.")
        detailed_odds = None
    
    # Debug: Hangi kategorilerde oran var göster
    if detailed_odds:
        available_categories = []
        for category, data in detailed_odds.items():
            if data:
                available_categories.append(category)
        if available_categories:
            st.success(f"✅ Bulunan oran kategorileri: {', '.join(available_categories)}")
        else:
            st.warning("⚠️ API'den veri geldi ancak hiçbir kategori dolu değil.")
    
    # Detaylı oranları işle
    processed_detailed_odds = analysis_logic.process_detailed_odds(detailed_odds) if detailed_odds else {}
    
    value_threshold = model_params.get('value_threshold', 5)
    
    # Model tahminleri
    probs = analysis.get('probs', {})
    corner_probs = analysis.get('corner_probs', {})
    card_probs = analysis.get('card_probs', {})
    first_half_probs = analysis.get('first_half_probs', {})
    
    # Seksiyon 1: Handikap Tahminleri
    st.markdown("### 🎯 Handikap Bahisleri")
    handicap_data = []
    
    # Ev sahibi -0.5
    model_h_0_5 = probs.get('handicap_ev_minus_0.5', 0)
    market_h_0_5 = processed_detailed_odds.get('handicap', {}).get('home_minus_0.5')
    if market_h_0_5:
        diff = model_h_0_5 - market_h_0_5['prob']
        value_tag = f"✅ Değerli! (+{diff:.1f}%)" if diff > value_threshold else ""
        handicap_data.append({
            'Bahis': f'{team_names["a"]} -0.5',
            'Model (%)': model_h_0_5,
            'Piyasa Oranı': market_h_0_5['odd'],
            'Piyasa (%)': market_h_0_5['prob'],
            'Değer': value_tag
        })
    else:
        handicap_data.append({
            'Bahis': f'{team_names["a"]} -0.5',
            'Model (%)': model_h_0_5,
            'Piyasa Oranı': '-',
            'Piyasa (%)': '-',
            'Değer': ''
        })
    
    # Ev sahibi -1.5
    model_h_1_5 = probs.get('handicap_ev_minus_1.5', 0)
    market_h_1_5 = processed_detailed_odds.get('handicap', {}).get('home_minus_1.5')
    if market_h_1_5:
        diff = model_h_1_5 - market_h_1_5['prob']
        value_tag = f"✅ Değerli! (+{diff:.1f}%)" if diff > value_threshold else ""
        handicap_data.append({
            'Bahis': f'{team_names["a"]} -1.5',
            'Model (%)': model_h_1_5,
            'Piyasa Oranı': market_h_1_5['odd'],
            'Piyasa (%)': market_h_1_5['prob'],
            'Değer': value_tag
        })
    else:
        handicap_data.append({
            'Bahis': f'{team_names["a"]} -1.5',
            'Model (%)': model_h_1_5,
            'Piyasa Oranı': '-',
            'Piyasa (%)': '-',
            'Değer': ''
        })
    
    # Deplasman +0.5, +1.5
    handicap_data.append({
        'Bahis': f'{team_names["b"]} +0.5',
        'Model (%)': probs.get('handicap_dep_plus_0.5', 0),
        'Piyasa Oranı': '-',
        'Piyasa (%)': '-',
        'Değer': ''
    })
    
    if handicap_data:
        df_handicap = pd.DataFrame(handicap_data)
        st.dataframe(df_handicap, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Seksiyon 2: İlk Yarı Tahminleri
    st.markdown("### ⏱️ İlk Yarı Tahminleri")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 1X2 (İlk Yarı)")
        first_half_data = []
        
        model_ht_home = first_half_probs.get('ilk_yari_ev_kazanir', 0)
        model_ht_draw = first_half_probs.get('ilk_yari_beraberlik', 0)
        model_ht_away = first_half_probs.get('ilk_yari_dep_kazanir', 0)
        
        market_ht = processed_detailed_odds.get('first_half_winner')
        
        if market_ht and market_ht.get('home'):
            diff_home = model_ht_home - market_ht['home']['prob']
            value_tag_home = f"✅ Değerli! (+{diff_home:.1f}%)" if diff_home > value_threshold else ""
            first_half_data.append({
                'Sonuç': f'{team_names["a"]} Kazanır',
                'Model (%)': model_ht_home,
                'Piyasa Oranı': market_ht['home']['odd'],
                'Piyasa (%)': market_ht['home']['prob'],
                'Değer': value_tag_home
            })
        else:
            first_half_data.append({
                'Sonuç': f'{team_names["a"]} Kazanır',
                'Model (%)': model_ht_home,
                'Piyasa Oranı': '-',
                'Piyasa (%)': '-',
                'Değer': ''
            })
        
        if market_ht and market_ht.get('draw'):
            first_half_data.append({
                'Sonuç': 'Beraberlik',
                'Model (%)': model_ht_draw,
                'Piyasa Oranı': market_ht['draw']['odd'],
                'Piyasa (%)': market_ht['draw']['prob'],
                'Değer': ''
            })
        else:
            first_half_data.append({
                'Sonuç': 'Beraberlik',
                'Model (%)': model_ht_draw,
                'Piyasa Oranı': '-',
                'Piyasa (%)': '-',
                'Değer': ''
            })
        
        if market_ht and market_ht.get('away'):
            diff_away = model_ht_away - market_ht['away']['prob']
            value_tag_away = f"✅ Değerli! (+{diff_away:.1f}%)" if diff_away > value_threshold else ""
            first_half_data.append({
                'Sonuç': f'{team_names["b"]} Kazanır',
                'Model (%)': model_ht_away,
                'Piyasa Oranı': market_ht['away']['odd'],
                'Piyasa (%)': market_ht['away']['prob'],
                'Değer': value_tag_away
            })
        else:
            first_half_data.append({
                'Sonuç': f'{team_names["b"]} Kazanır',
                'Model (%)': model_ht_away,
                'Piyasa Oranı': '-',
                'Piyasa (%)': '-',
                'Değer': ''
            })
        
        df_first_half = pd.DataFrame(first_half_data)
        st.dataframe(df_first_half, use_container_width=True, hide_index=True)
    
    with col2:
        st.markdown("#### 1.5 Üst/Alt (İlk Yarı)")
        model_ht_over = probs.get('ilk_yari_1.5_ust', 0)
        model_ht_under = probs.get('ilk_yari_1.5_alt', 0)
        
        first_half_ou_data = [
            {'Bahis': '1.5 Üst', 'Model (%)': model_ht_over, 'Piyasa Oranı': '-', 'Piyasa (%)': '-', 'Değer': ''},
            {'Bahis': '1.5 Alt', 'Model (%)': model_ht_under, 'Piyasa Oranı': '-', 'Piyasa (%)': '-', 'Değer': ''}
        ]
        
        df_ht_ou = pd.DataFrame(first_half_ou_data)
        st.dataframe(df_ht_ou, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Seksiyon 3: Korner Tahminleri
    st.markdown("### ⛳ Korner Tahminleri")
    st.info(f"📊 Beklenen Toplam Korner: **{corner_probs.get('expected_corners', 10.0):.1f}**")
    
    corner_data = []
    
    # 9.5 Üst/Alt
    model_c_9_5_over = corner_probs.get('over_9.5', 0)
    model_c_9_5_under = corner_probs.get('under_9.5', 0)
    market_c_9_5 = processed_detailed_odds.get('corners_9.5')
    
    if market_c_9_5 and market_c_9_5.get('over'):
        diff = model_c_9_5_over - market_c_9_5['over']['prob']
        value_tag = f"✅ Değerli! (+{diff:.1f}%)" if diff > value_threshold else ""
        corner_data.append({
            'Bahis': '9.5 Üst',
            'Model (%)': model_c_9_5_over,
            'Piyasa Oranı': market_c_9_5['over']['odd'],
            'Piyasa (%)': market_c_9_5['over']['prob'],
            'Değer': value_tag
        })
    else:
        corner_data.append({
            'Bahis': '9.5 Üst',
            'Model (%)': model_c_9_5_over,
            'Piyasa Oranı': '-',
            'Piyasa (%)': '-',
            'Değer': ''
        })
    
    # 10.5 Üst/Alt
    model_c_10_5_over = corner_probs.get('over_10.5', 0)
    market_c_10_5 = processed_detailed_odds.get('corners_10.5')
    
    if market_c_10_5 and market_c_10_5.get('over'):
        diff = model_c_10_5_over - market_c_10_5['over']['prob']
        value_tag = f"✅ Değerli! (+{diff:.1f}%)" if diff > value_threshold else ""
        corner_data.append({
            'Bahis': '10.5 Üst',
            'Model (%)': model_c_10_5_over,
            'Piyasa Oranı': market_c_10_5['over']['odd'],
            'Piyasa (%)': market_c_10_5['over']['prob'],
            'Değer': value_tag
        })
    else:
        corner_data.append({
            'Bahis': '10.5 Üst',
            'Model (%)': model_c_10_5_over,
            'Piyasa Oranı': '-',
            'Piyasa (%)': '-',
            'Değer': ''
        })
    
    if corner_data:
        df_corners = pd.DataFrame(corner_data)
        st.dataframe(df_corners, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Seksiyon 4: Kart Tahminleri
    st.markdown("### 🟨 Kart Tahminleri")
    st.info(f"📊 Beklenen Sarı Kart: **{card_probs.get('expected_yellow_cards', 4.0):.1f}** | Kırmızı Kart: **{card_probs.get('expected_red_cards', 0.15):.2f}**")
    
    card_data = [
        {'Bahis': '3.5 Üst (Sarı)', 'Model (%)': card_probs.get('over_3.5_yellow', 0), 'Piyasa Oranı': '-', 'Piyasa (%)': '-', 'Değer': ''},
        {'Bahis': '4.5 Üst (Sarı)', 'Model (%)': card_probs.get('over_4.5_yellow', 0), 'Piyasa Oranı': '-', 'Piyasa (%)': '-', 'Değer': ''},
        {'Bahis': 'Kırmızı Kart VAR', 'Model (%)': card_probs.get('red_card_yes', 0), 'Piyasa Oranı': '-', 'Piyasa (%)': '-', 'Değer': ''},
    ]
    
    # Piyasa oranı varsa ekle
    market_cards = processed_detailed_odds.get('cards_over_3.5')
    if market_cards:
        card_data[0]['Piyasa Oranı'] = market_cards['odd']
        card_data[0]['Piyasa (%)'] = market_cards['prob']
        diff = card_data[0]['Model (%)'] - market_cards['prob']
        if diff > value_threshold:
            card_data[0]['Değer'] = f"✅ Değerli! (+{diff:.1f}%)"
    
    df_cards = pd.DataFrame(card_data)
    st.dataframe(df_cards, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.caption("💡 **Değerli Oran:** Model tahmini piyasa olasılığından eşik değerden (%5) fazla olduğunda işaretlenir.")

def display_h2h_tab(h2h_stats: Optional[Dict], team_names: Dict):
    st.subheader(f"⚔️ {team_names['a']} vs {team_names['b']}: Kafa Kafaya Analiz")
    if h2h_stats:
        summary = h2h_stats['summary']
        goals = h2h_stats['goals']
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Toplam Maç", summary['total_matches'])
        c2.metric(f"{team_names['a']} Galibiyeti", summary['wins_a'])
        c3.metric(f"{team_names['b']} Galibiyeti", summary['wins_b'])
        c4.metric("Beraberlik", summary['draws'])
        st.markdown("---")
        st.markdown("##### Gol İstatistikleri")
        goal_df = pd.DataFrame({'İstatistik': ['Toplam Gol', 'Maç Başına Gol'], team_names['a']: [goals['goals_a'], f"{goals['avg_goals_a']:.2f}"], team_names['b']: [goals['goals_b'], f"{goals['avg_goals_b']:.2f}"]}).set_index('İstatistik')
        st.table(goal_df)
        st.markdown("---")
        st.markdown("##### Son Karşılaşmalar")
        recent_matches_df = pd.DataFrame(h2h_stats['recent_matches'])
        st.dataframe(recent_matches_df, hide_index=True, use_container_width=True)
    else:
        st.warning("İki takım arasında geçmişe dönük karşılaşma verisi bulunamadı.")
        
def display_parameters_tab(params: Dict, team_names: Dict):
    st.subheader("⚙️ Modelin Kullandığı Parametreler")
    
    # 🆕 Yeni faktörler özel bölümü
    st.markdown("### 🎯 Gelişmiş Analiz Faktörleri")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        momentum_a = params.get('momentum_a', 1.0)
        color_a = "normal" if 0.98 <= momentum_a <= 1.02 else ("inverse" if momentum_a < 0.98 else "off")
        st.metric("Momentum (Ev)", f"x{momentum_a:.2f}", 
                 delta=f"{((momentum_a - 1.0) * 100):+.0f}%", delta_color=color_a,
                 help="Son 5 maçtaki gol farkı trendi")
    with col2:
        momentum_b = params.get('momentum_b', 1.0)
        color_b = "normal" if 0.98 <= momentum_b <= 1.02 else ("inverse" if momentum_b < 0.98 else "off")
        st.metric("Momentum (Dep)", f"x{momentum_b:.2f}",
                 delta=f"{((momentum_b - 1.0) * 100):+.0f}%", delta_color=color_b)
    with col3:
        h2h = params.get('h2h_factor', 1.0)
        h2h_desc = "Ev dominant" if h2h >= 1.05 else "Dep dominant" if h2h <= 0.95 else "Dengeli"
        st.metric("H2H Faktörü", f"x{h2h:.2f}", help=f"Son karşılaşmalar: {h2h_desc}")
    with col4:
        referee = params.get('referee_factor', 1.0)
        ref_desc = "Sert" if referee <= 0.95 else "Yumuşak" if referee >= 1.03 else "Normal"
        st.metric("Hakem Faktörü", f"x{referee:.2f}", help=f"Hakem stili: {ref_desc}")
    
    col5, col6, col7, col8 = st.columns(4)
    with col5:
        rest_a = params.get('rest_factor_a', 1.0)
        st.metric("Dinlenme (Ev)", f"x{rest_a:.2f}", 
                 delta="Yorgun" if rest_a < 0.98 else "İyi",
                 help="Son maçtan bu yana geçen gün sayısı")
    with col6:
        rest_b = params.get('rest_factor_b', 1.0)
        st.metric("Dinlenme (Dep)", f"x{rest_b:.2f}",
                 delta="Yorgun" if rest_b < 0.98 else "İyi")
    with col7:
        value_cat = params.get('value_category', 'Dengeli')
        value_a = params.get('value_mult_a', 1.0)
        value_b = params.get('value_mult_b', 1.0)
        value_display = f"Ev x{value_a:.2f} / Dep x{value_b:.2f}"
        st.metric("Kadro Değeri", value_display, 
                 delta=value_cat,
                 help="Elo ve lig bazlı tahmini kadro değeri karşılaştırması")
    with col8:
        league_q = params.get('league_quality', 0.85)
        st.metric("Lig Kalitesi", f"x{league_q:.2f}",
                 help="1.00 = En üst lig (Premier, La Liga)")
    
    col9, col10 = st.columns(2)
    with col9:
        odds_used = params.get('odds_used', False)
        st.metric("Bahis Oranları", "✅ Evet" if odds_used else "❌ Hayır",
                 help="Model tahminini piyasa oranlarıyla birleştirdi mi?")
    with col10:
        st.metric("", "")  # Placeholder
    
    # 🆕 Sakatlık Durumu
    col11, col12 = st.columns(2)
    with col11:
        injury_a = params.get('injury_factor_a', 1.0)
        inj_count_a = params.get('injuries_count_a', 0)
        inj_status = "🏥 Ciddi" if injury_a <= 0.90 else "🩹 Hafif" if injury_a <= 0.95 else "✅ Sağlam"
        st.metric(f"Sakatlık (Ev) - {team_names['a']}", f"x{injury_a:.2f}",
                 delta=f"{inj_count_a} oyuncu" if inj_count_a > 0 else "Yok",
                 delta_color="inverse" if inj_count_a > 0 else "normal",
                 help=f"Durum: {inj_status}")
    with col12:
        injury_b = params.get('injury_factor_b', 1.0)
        inj_count_b = params.get('injuries_count_b', 0)
        inj_status_b = "🏥 Ciddi" if injury_b <= 0.90 else "🩹 Hafif" if injury_b <= 0.95 else "✅ Sağlam"
        st.metric(f"Sakatlık (Dep) - {team_names['b']}", f"x{injury_b:.2f}",
                 delta=f"{inj_count_b} oyuncu" if inj_count_b > 0 else "Yok",
                 delta_color="inverse" if inj_count_b > 0 else "normal",
                 help=f"Durum: {inj_status_b}")
    
    st.markdown("---")
    st.markdown("### 📊 Temel Parametreler")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"**{team_names['a']} (Ev Sahibi)**")
        st.metric("Hibrit Hücum Gücü", f"{params['home_att']:.2f}", help="Takımın sezonluk ve son 10 maçlık formuna göre hesaplanan hücum gücü.")
        st.metric("Hibrit Savunma Gücü", f"{params['home_def']:.2f}", help="Takımın sezonluk ve son 10 maçlık formuna göre hesaplanan savunma gücü.")
        st.metric("Güncel Form Katsayısı", f"x{params.get('form_factor_a', 1.0):.2f}", help="Son maç sonuçlarına göre hesaplanan dinamik form etkisi.")
        st.metric("Hücum Endeksi", f"x{params.get('home_attack_idx', 1.0):.2f}", help="Lig ortalaması x=1.00 olacak şekilde normalize edilmiştir.")
        st.metric("Savunma Endeksi", f"x{params.get('home_def_idx', 1.0):.2f}", help="Lig ortalaması x=1.00 olacak şekilde normalize edilmiştir (düşük değer daha iyi).")
    with c2:
        st.markdown(f"**{team_names['b']} (Deplasman)**")
        st.metric("Hibrit Hücum Gücü", f"{params['away_att']:.2f}")
        st.metric("Hibrit Savunma Gücü", f"{params['away_def']:.2f}")
        st.metric("Güncel Form Katsayısı", f"x{params.get('form_factor_b', 1.0):.2f}", help="Rakibin deplasman performansına göre dinamik form katsayısı.")
        st.metric("Hücum Endeksi", f"x{params.get('away_attack_idx', 1.0):.2f}")
        st.metric("Savunma Endeksi", f"x{params.get('away_def_idx', 1.0):.2f}", help="Lig ortalaması x=1.00 olacak şekilde normalize edilmiştir (düşük değer daha iyi).")
    with c3:
        st.markdown("**Genel Parametreler**")
        st.metric("Lig Ort. Gol Sayısı", f"{params['avg_goals']:.2f}")
        st.metric("Lig Ev Gol Ort.", f"{params.get('avg_home_goals', params['avg_goals'] * 0.55):.2f}")
        st.metric("Lig Dep Gol Ort.", f"{params.get('avg_away_goals', params['avg_goals'] * 0.45):.2f}")
        st.metric("Dinamik Ev S. Avantajı", f"x{params['home_advantage']:.2f}", help="Ev sahibi takımın PBM istatistiklerine göre dinamik olarak hesaplanan avantaj katsayısı.")
        st.metric("Tempo Endeksi", f"x{params.get('pace_index', 1.0):.2f}")
        st.metric("Elo Farkı", f"{params.get('elo_diff', 0):+.0f}")

@st.cache_data(ttl=3600, show_spinner=False)  # 1 saat cache - daha sık güncelleme
def analyze_fixture_summary(fixture: Dict, model_params: Dict) -> Optional[Dict]:
    """
    Maç özeti analizi yapar - SADECE SİSTEM API KULLANIR (kullanıcı hakkı tüketmez).
    Bu fonksiyon maç panosu için kullanılır.
    """
    try:
        id_a, name_a, id_b, name_b = fixture['home_id'], fixture['home_name'], fixture['away_id'], fixture['away_name']
        # HER ZAMAN skip_limit=True - sistem API'si
        league_info = api_utils.get_team_league_info(API_KEY, BASE_URL, id_a, skip_limit=True)
        
        # Eğer takımdan lig bilgisi alınamazsa, fixture'daki lig bilgisini kullan
        if not league_info and 'league_id' in fixture:
            league_info = {
                'league_id': fixture['league_id'],
                'season': fixture.get('season', datetime.now().year if datetime.now().month > 6 else datetime.now().year - 1)
            }
        
        if not league_info: 
            st.warning(f"⚠️ {name_a} vs {name_b}: Lig bilgisi alınamadı")
            return None
        # HER ZAMAN skip_api_limit=True - sistem API'si
        analysis = analysis_logic.run_core_analysis(API_KEY, BASE_URL, id_a, id_b, name_a, name_b, fixture['match_id'], league_info, model_params, LIG_ORTALAMA_GOL, skip_api_limit=True)
        if not analysis: 
            st.warning(f"⚠️ {name_a} vs {name_b}: Analiz verisi oluşturulamadı")
            return None
        probs = analysis['probs']
        max_prob_key = max(probs, key=lambda k: probs[k] if 'win' in k or 'draw' in k else -1)
        decision = f"{name_a} K." if max_prob_key == 'win_a' else f"{name_b} K." if max_prob_key == 'win_b' else "Ber."
        result_icon, actual_score_str = "", fixture.get('actual_score', '')
        if actual_score_str:
            is_home_winner = fixture.get('winner_home')
            predicted_home_win = " K." in decision and name_a in decision; predicted_away_win = " K." in decision and name_b in decision; predicted_draw = "Ber." in decision
            actual_winner = 'home' if is_home_winner is True else 'away' if is_home_winner is False else 'draw'
            if (predicted_home_win and actual_winner == 'home') or (predicted_away_win and actual_winner == 'away') or (predicted_draw and actual_winner == 'draw'): result_icon = "✅"
            else: result_icon = "❌"
        return {
            "Saat": fixture['time'], 
            "Lig": fixture['league_name'], 
            "Ev Sahibi": name_a, 
            "Deplasman": name_b, 
            "Tahmin": decision, 
            "Gerçekleşen Skor": actual_score_str, 
            "Sonuç": result_icon, 
            "AI Güven Puanı": analysis['confidence'], 
            "2.5 ÜST (%)": probs['ust_2.5'], 
            "KG VAR (%)": probs['kg_var'], 
            "home_id": id_a, 
            "away_id": id_b, 
            "fixture_id": fixture['match_id'],
            "home_logo": fixture.get('home_logo', ''),
            "away_logo": fixture.get('away_logo', ''),
            "league_id": fixture.get('league_id'),
            "season": fixture.get('season')
        }
    except Exception as e: 
        st.error(f"❌ {fixture.get('home_name', '?')} vs {fixture.get('away_name', '?')}: Hata - {str(e)}")
        return None

def analyze_and_display(team_a_data: Dict, team_b_data: Dict, fixture_id: int, model_params: Dict, league_id: int = None, season: int = None):
    """
    Detaylı maç analizi yapar ve gösterir.
    Bu fonksiyon KULLANICI API HAKKI TÜKETİR (her çağrıda 1 kredi).
    Cache yok - her çağrıda yeni analiz yapılır ve API hakkı tüketilir.
    """
    # KULLANICI API HAKKI KONTROLÜ - ÜST SEVİYEDE
    can_request, error_msg = api_utils.check_api_limit()
    if not can_request:
        st.error(f"API Limit Hatası: {error_msg}")
        return
    # Kullanıcı hakkını tüket (her analiz için 1 kredi)
    api_utils.increment_api_usage()
    
    id_a, name_a, id_b, name_b = team_a_data['id'], team_a_data['name'], team_b_data['id'], team_b_data['name']
    logo_a = team_a_data.get('logo', '')
    logo_b = team_b_data.get('logo', '')
    
    # Modern Header Card
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 24px; border-radius: 16px; margin-bottom: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.3);'>
        <div style='display: flex; align-items: center; justify-content: space-between;'>
            <div style='display: flex; align-items: center; gap: 16px;'>
                <img src='{logo_a}' width='56' style='border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.2);'>
                <div>
                    <h2 style='color: white; margin: 0; font-size: 1.8em;'>{name_a}</h2>
                    <p style='color: rgba(255,255,255,0.8); margin: 4px 0 0 0; font-size: 0.9em;'>Ev Sahibi</p>
                </div>
            </div>
            <div style='text-align: center; padding: 0 24px;'>
                <span style='color: white; font-size: 2.5em; font-weight: 700;'>VS</span>
            </div>
            <div style='display: flex; align-items: center; gap: 16px;'>
                <div style='text-align: right;'>
                    <h2 style='color: white; margin: 0; font-size: 1.8em;'>{name_b}</h2>
                    <p style='color: rgba(255,255,255,0.8); margin: 4px 0 0 0; font-size: 0.9em;'>Deplasman</p>
                </div>
                <img src='{logo_b}' width='56' style='border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.2);'>
            </div>
        </div>
        <p style='color: rgba(255,255,255,0.9); margin: 16px 0 0 0; text-align: center; font-size: 1.1em; font-weight: 500;'>
            ⚽ Detaylı Maç Analizi
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Artık HER ZAMAN skip_limit=True - API hakkı üst seviyede yönetiliyor
    league_info = api_utils.get_team_league_info(API_KEY, BASE_URL, id_a, skip_limit=True)
    
    # Eğer takımdan lig bilgisi alınamazsa, manuel olarak verilen lig bilgisini kullan
    if not league_info and league_id:
        if not season:
            season = datetime.now().year if datetime.now().month > 6 else datetime.now().year - 1
        league_info = {'league_id': league_id, 'season': season}
    
    if not league_info: 
        st.error("Lig bilgisi alınamadı."); 
        return
    
    # Artık HER ZAMAN skip_api_limit=True - API hakkı üst seviyede yönetiliyor
    analysis = analysis_logic.run_core_analysis(API_KEY, BASE_URL, id_a, id_b, name_a, name_b, fixture_id, league_info, model_params, LIG_ORTALAMA_GOL, skip_api_limit=True)
    if not analysis: st.error("Analiz verisi oluşturulamadı."); return

    with st.spinner("Ek veriler çekiliyor..."):
        odds_response, _ = api_utils.get_fixture_odds(API_KEY, BASE_URL, fixture_id)
        processed_odds = analysis_logic.process_odds_data(odds_response)
        fixture_details, _ = api_utils.get_fixture_details(API_KEY, BASE_URL, fixture_id)
        processed_referee_stats = None
        if fixture_details:
            referee_info = fixture_details.get('fixture', {}).get('referee')
            referee_id, referee_name_only = None, None
            if isinstance(referee_info, dict):
                referee_id = referee_info.get('id')
            elif isinstance(referee_info, str):
                referee_name_only = referee_info
            if referee_id:
                referee_data, _ = api_utils.get_referee_stats(API_KEY, BASE_URL, referee_id, league_info['season'])
                processed_referee_stats = analysis_logic.process_referee_data(referee_data)
            elif referee_name_only:
                processed_referee_stats = {"name": referee_name_only, "total_games": "N/A"}
        h2h_matches, _ = api_utils.get_h2h_matches(API_KEY, BASE_URL, id_a, id_b, H2H_MATCH_LIMIT)
        processed_h2h = analysis_logic.process_h2h_data(h2h_matches, id_a)

    team_names = {'a': name_a, 'b': name_b}; team_ids = {'a': id_a, 'b': id_b}
    
    # Modern Tab Tasarımı
    st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #1e1e1e;
        padding: 8px;
        border-radius: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        border-radius: 8px;
        padding: 0 24px;
        background-color: #2d2d2d;
        color: #aaa;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    tab_list = ["🎯 Tahmin Özeti", "📈 İstatistikler", "🎲 Detaylı İddaa", "🚑 Eksikler", "📊 Puan Durumu", "⚔️ H2H Analizi", "⚖️ Hakem Analizi", "⚙️ Analiz Parametreleri"]
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(tab_list)

    team_logos = {'a': logo_a, 'b': logo_b}
    
    with tab1: display_summary_tab(analysis, team_names, processed_odds, model_params, team_logos)
    with tab2: display_stats_tab(analysis['stats'], team_names, team_ids, analysis.get('params'))
    with tab3: display_detailed_betting_tab(analysis, team_names, fixture_id, model_params)
    with tab4: display_injuries_tab(fixture_id, team_names, team_ids, league_info)
    with tab5: display_standings_tab(league_info, team_names)
    with tab6: display_h2h_tab(processed_h2h, team_names)
    with tab7: display_referee_tab(processed_referee_stats)
    with tab8: display_parameters_tab(analysis['params'], team_names)

@st.cache_data(ttl=3600, show_spinner=False)  # 1 saat cache - sık güncelleme
def get_top_predictions_today(model_params: Dict, today_date: date, is_admin_user: bool, top_n: int = 5) -> List[Dict]:
    """Bugünün en yüksek güvenli tahminlerini getirir - API limiti tüketmez"""
    
    if is_admin_user:
        # ADMIN: POPÜLER 100 LİG TARA (performans optimizasyonu)
        selected_ids = TOP_100_POPULAR_LEAGUES
        print(f"🔑 ADMIN MODU: Popüler 100 lig taranıyor...")
        max_matches = 100  # Daha fazla maç analiz et
    else:
        # NORMAL KULLANICI: Sadece popüler 6 lig
        selected_ids = [203, 39, 140, 135, 78, 61]  # Süper Lig, Premier, La Liga, Serie A, Bundesliga, Ligue 1
        print(f"👤 Normal kullanıcı: {len(selected_ids)} popüler lig taranıyor...")
        max_matches = 20
    
    # Bugünün maçlarını çek - KULLANICI LİMİTİNİ TÜKETME
    fixtures, error = api_utils.get_fixtures_by_date(API_KEY, BASE_URL, selected_ids, today_date, bypass_limit_check=True)
    
    if error:
        print(f"❌ API Hatası: {error}")  # DEBUG
        return []
    
    if not fixtures:
        print(f"⚠️ Bugün {len(selected_ids)} ligde maç bulunamadı!")  # DEBUG
        return []
    
    print(f"✅ Bugün {len(fixtures)} maç bulundu, {max_matches} tanesi analiz ediliyor...")  # DEBUG
    
    # Liglere göre grupla
    leagues_with_matches = {}
    for fixture in fixtures:
        league_name = fixture.get('league_name', 'Bilinmeyen Lig')
        if league_name not in leagues_with_matches:
            leagues_with_matches[league_name] = 0
        leagues_with_matches[league_name] += 1
    
    print(f"📊 Bugün maç olan ligler: {len(leagues_with_matches)}")
    for league, count in sorted(leagues_with_matches.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   - {league}: {count} maç")
    
    # Maçları analiz et
    analyzed_fixtures = []
    for idx, fixture in enumerate(fixtures[:max_matches], 1):
        try:
            # ANA SAYFA - SİSTEM API'Sİ KULLAN (use_system_api parametresi kaldırıldı, artık her zaman sistem API)
            summary = analyze_fixture_summary(fixture, model_params)
            if summary:
                confidence = summary.get('AI Güven Puanı', 0)
                print(f"  {idx}. {summary['Ev Sahibi']} vs {summary['Deplasman']}: Güven={confidence:.1f}%")  # DEBUG
                if confidence >= 40.0:  # EŞİK: %40
                    analyzed_fixtures.append(summary)
                    print(f"    ✅ EKLENDI (Güven: {confidence:.1f}%)")  # DEBUG
        except Exception as e:
            print(f"  ❌ Hata: {str(e)}")  # DEBUG
            continue
    
    print(f"🎯 Toplam {len(analyzed_fixtures)} uygun tahmin bulundu!")  # DEBUG
    
    # Güvene göre sırala ve top N'i döndür
    analyzed_fixtures.sort(key=lambda x: x['AI Güven Puanı'], reverse=True)
    return analyzed_fixtures[:top_n]

@st.cache_data(ttl=18000, show_spinner=False)  # 5 saat cache - tekrar analiz engellendi
def analyze_fixture_by_id(fixture_id: int, home_id: int, away_id: int, model_params: Dict):
    """Fixture ID ile detaylı analiz yapar"""
    try:
        fixture_details, error = api_utils.get_fixture_details(API_KEY, BASE_URL, fixture_id)
        if error or not fixture_details:
            st.error("Maç detayları alınamadı.")
            return
        home_team = fixture_details['teams']['home']
        away_team = fixture_details['teams']['away']
        
        # Modern başlık kartı
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); 
                    padding: 20px; border-radius: 14px; margin: 16px 0; box-shadow: 0 3px 16px rgba(0,0,0,0.25);'>
            <div style='display: flex; align-items: center; justify-content: center; gap: 24px;'>
                <div style='text-align: center;'>
                    <img src='{home_team.get("logo","")}' width='48' style='border-radius: 50%; border: 2px solid white;'>
                    <p style='color: white; margin: 8px 0 0 0; font-weight: 600;'>{home_team.get("name","")}</p>
                </div>
                <span style='color: white; font-size: 1.8em; font-weight: 700;'>VS</span>
                <div style='text-align: center;'>
                    <img src='{away_team.get("logo","")}' width='48' style='border-radius: 50%; border: 2px solid white;'>
                    <p style='color: white; margin: 8px 0 0 0; font-weight: 600;'>{away_team.get("name","")}</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")
        # Eski detaylı analiz fonksiyonu - league_id bilgisini fixture'dan al
        league_id_from_fixture = fixture_details.get('league', {}).get('id')
        season_from_fixture = fixture_details.get('league', {}).get('season')
        analyze_and_display(home_team, away_team, fixture_id, model_params, 
                          league_id=league_id_from_fixture, season=season_from_fixture)
    except Exception as e:
        st.error(f"Analiz sırasında hata: {str(e)}")

def build_home_view(model_params):
    # Ana başlık ile logo
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <h1 style='text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                   -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
                   background-clip: text; font-size: 2.5em; margin: 10px 0;'>
            🏠 Ana Sayfa
        </h1>
        """, unsafe_allow_html=True)
    
    if LEAGUE_LOAD_ERROR:
        st.caption(f"⚠️ Lig listesi uyarısı: {LEAGUE_LOAD_ERROR}")
    
    # Ana sayfa bilgilendirme
    st.success("✨ Günün tahminleri sistem API'si ile ücretsiz olarak sunulmaktadır. Detaylı analiz yapmak için kullanıcı API hakkınız kullanılacaktır.")
    
    st.markdown("---")
    st.subheader("🔍 Gelişmiş Takım Araması")
    team_query = st.text_input("Takım adı girin (yaklaşan maçları bulacağız):", placeholder="Örn: Galatasaray, Real Madrid, Barcelona")
    
    col1, col2 = st.columns(2)
    with col1:
        search_type = st.radio("Arama Tipi:", ["Hızlı Arama (1 maç)", "Detaylı Arama (Çoklu maç)"])
    with col2:
        max_results = st.slider("Maksimum sonuç:", 1, 10, 3) if search_type == "Detaylı Arama (Çoklu maç)" else 1
    
    if st.button("🔍 Takımı Ara", use_container_width=True):
        if team_query:
            with st.spinner(f"'{team_query}' takımı aranıyor..."):
                team_data = api_utils.get_team_id(API_KEY, BASE_URL, team_query)
                if team_data:
                    st.success(f"✅ Takım bulundu: **{team_data['name']}**")
                    
                    if search_type == "Hızlı Arama (1 maç)":
                        # Eski sistem - tek maç
                        with st.spinner(f"{team_data['name']} takımının yaklaşan maçı aranıyor..."):
                            next_fixture, error = api_utils.get_next_team_fixture(API_KEY, BASE_URL, team_data['id'])
                            if error:
                                st.error(f"❌ Maç aranırken hata: {error}")
                                # Alternatif arama dene
                                st.info("🔄 Alternatif arama yöntemi deneniyor...")
                                fixtures, alt_error = api_utils.get_team_upcoming_fixtures(API_KEY, BASE_URL, team_data['id'], 1)
                                if fixtures and len(fixtures) > 0:
                                    next_fixture = fixtures[0]
                                    error = None
                                    st.success("✅ Alternatif arama ile maç bulundu!")
                            
                            if not error and next_fixture and next_fixture.get('teams'):
                                home_team = next_fixture['teams'].get('home', {})
                                away_team = next_fixture['teams'].get('away', {})
                                fixture_id = next_fixture.get('fixture', {}).get('id')
                                if home_team.get('name') and away_team.get('name'):
                                    st.info(f"📅 **Maç bulundu:** {home_team['name']} vs {away_team['name']}")
                                else:
                                    st.error("❌ Takım bilgileri eksik")
                                league_id_from_fixture = next_fixture.get('league', {}).get('id')
                                season_from_fixture = next_fixture.get('league', {}).get('season')
                                analyze_and_display(home_team, away_team, fixture_id, model_params,
                                                  league_id=league_id_from_fixture, season=season_from_fixture)
                            else:
                                st.error("❌ Bu takımın yaklaşan maçı bulunamadı.")
                    
                    else:
                        # Yeni sistem - çoklu maç
                        with st.spinner(f"{team_data['name']} takımının yaklaşan {max_results} maçı aranıyor..."):
                            fixtures, error = api_utils.get_team_upcoming_fixtures(API_KEY, BASE_URL, team_data['id'], max_results)
                            if error:
                                st.error(f"❌ Maçlar aranırken hata: {error}")
                            elif fixtures and len(fixtures) > 0:
                                st.success(f"✅ **{len(fixtures)} adet yaklaşan maç bulundu!**")
                                
                                for idx, fixture in enumerate(fixtures, 1):
                                    if not fixture.get('teams'):
                                        st.warning(f"⚠️ Maç {idx}: Takım bilgisi eksik")
                                        continue
                                    
                                    home_team = fixture['teams'].get('home', {})
                                    away_team = fixture['teams'].get('away', {})
                                    
                                    if not home_team.get('name') or not away_team.get('name'):
                                        st.warning(f"⚠️ Maç {idx}: Takım isimleri eksik")
                                        continue
                                    
                                    with st.expander(f"📅 Maç {idx}: {home_team['name']} vs {away_team['name']}", expanded=(idx==1)):
                                        fixture_id = fixture.get('fixture', {}).get('id')
                                        
                                        # Maç tarihi göster
                                        fixture_date = fixture.get('fixture', {}).get('date', '')
                                        if fixture_date:
                                            from datetime import datetime
                                            try:
                                                date_obj = datetime.fromisoformat(fixture_date.replace('Z', '+00:00'))
                                                st.write(f"🗓️ **Tarih:** {date_obj.strftime('%d.%m.%Y %H:%M')}")
                                            except:
                                                st.write(f"🗓️ **Tarih:** {fixture_date}")
                                        
                                        league_info = fixture.get('league', {})
                                        if league_info:
                                            st.write(f"🏆 **Lig:** {league_info.get('name', 'Bilinmiyor')}")
                                        
                                        if st.button(f"🔍 Analiz Et", key=f"analyze_{fixture_id}"):
                                            league_id_from_fixture = fixture.get('league', {}).get('id')
                                            season_from_fixture = fixture.get('league', {}).get('season')
                                            analyze_and_display(home_team, away_team, fixture_id, model_params,
                                                              league_id=league_id_from_fixture, season=season_from_fixture)
                            else:
                                st.error(f"❌ **{team_data['name']}** takımının yaklaşan maçı bulunamadı.")
                                st.info("💡 **İpucu:** Takım adını farklı dillerde deneyin (İngilizce, Türkçe vs.)")
                    
                else:
                    st.error(f"❌ '{team_query}' takımı bulunamadı.")
                    st.info("💡 **İpucu:** Takım adını tam olarak yazmaya çalışın veya farklı dillerde deneyin.")
        else:
            st.warning("Lütfen bir takım adı girin.")

def build_dashboard_view(model_params: Dict):
    st.markdown("""
    <h1 style='text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
               -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
               background-clip: text; font-size: 2.5em; margin: 10px 0;'>
        🗓️ Maç Panosu
    </h1>
    """, unsafe_allow_html=True)
    
    if LEAGUE_LOAD_ERROR:
        st.caption(f"⚠️ Lig listesi uyarısı: {LEAGUE_LOAD_ERROR}")
    
    st.markdown("---")
    col1, col2 = st.columns([1, 3])
    with col1:
        # Session state ile tarih seçimini koru
        if 'dashboard_date' not in st.session_state:
            st.session_state.dashboard_date = date.today()
        selected_date = st.date_input("Tarih Seçin", value=st.session_state.dashboard_date, key="dash_date_input")
        st.session_state.dashboard_date = selected_date
    with col2:
        stored_favorites = st.session_state.get('favorite_leagues')
        default_leagues = normalize_league_labels(stored_favorites) or get_default_favorite_leagues()
        
        # Popüler ligleri en üste koy
        popular_league_ids = [203, 39, 140, 135, 78, 61, 2, 3]  # Süper Lig, Premier, La Liga, Serie A, Bundesliga, Ligue 1, UCL, UEL
        popular_leagues = [INTERESTING_LEAGUES[lid] for lid in popular_league_ids if lid in INTERESTING_LEAGUES]
        other_leagues = [league for league in INTERESTING_LEAGUES.values() if league not in popular_leagues]
        sorted_leagues = popular_leagues + sorted(other_leagues)
        
        # Session state ile lig seçimini koru
        if 'dashboard_selected_leagues' not in st.session_state:
            st.session_state.dashboard_selected_leagues = default_leagues
        
        selected_names = st.multiselect(
            "Analiz Edilecek Ligleri Seçin",
            options=sorted_leagues,
            default=st.session_state.dashboard_selected_leagues,
            placeholder="Lig seçimi yapın...",
            key="dash_league_select"
        )
        
        # Seçimi session state'e kaydet
        st.session_state.dashboard_selected_leagues = selected_names
    st.markdown(f"### {selected_date.strftime('%d %B %Y')} Maçları")
    
    # Bilgilendirme mesajı
    st.info("ℹ️ Maç listesi ve özet tahminler sistem API'si kullanılarak sağlanır. Detaylı maç analizi yapmak için kullanıcı API hakkınız kullanılacaktır.")
    
    st.markdown("---")
    if not selected_names: 
        st.warning("Lütfen analiz için yukarıdan en az bir lig seçin."); return
    
    # LİG SAYISI SINIRI - Sadece ücretsiz kullanıcılar için
    MAX_LEAGUES_FREE = 10
    tier = st.session_state.get('tier', 'ücretsiz')
    is_admin = st.session_state.get('username') in st.session_state.get('admin_users', [])
    
    # Ücretsiz kullanıcılar için limit kontrolü (Admin ve ücretli kullanıcılar sınırsız)
    if tier == 'ücretsiz' and not is_admin:
        if len(selected_names) > MAX_LEAGUES_FREE:
            st.error(f"⚠️ Ücretsiz kullanıcılar en fazla {MAX_LEAGUES_FREE} lig seçebilir. Şu anda {len(selected_names)} lig seçili.")
            st.info("💡 Daha fazla lig analizi için ücretli üyeliğe geçin veya ligleri gruplar halinde seçin.")
            return
    else:
        # Admin ve ücretli kullanıcılar için bilgi ve öneri mesajları
        if len(selected_names) > 25:
            st.warning(f"⚠️ {len(selected_names)} lig seçtiniz! API rate limit'e takılma riski var.")
            st.info("💡 **ÖNERİ**: En fazla 20-25 lig seçmeniz önerilir. Daha fazla lig için gruplar halinde analiz yapın.")
            # Kullanıcıya devam etme seçeneği sun
            if not st.button("⚡ Yine de Devam Et", type="primary"):
                return
        elif len(selected_names) > 15:
            # Bekleme süresi tahmini
            estimated_time = len(selected_names) * 1.2  # Saniye cinsinden
            st.info(f"ℹ️ {len(selected_names)} lig seçtiniz. Analiz yaklaşık {estimated_time:.0f} saniye sürecek...")
    
    selected_ids = []
    for label in selected_names:
        league_id = get_league_id_from_display(label)
        if league_id and league_id not in selected_ids:
            selected_ids.append(league_id)
    if not selected_ids:
        st.warning("Seçili ligler bulunamadı. Lütfen seçimlerinizi kontrol edin.")
        return
    
    # MAÇ PANOSUNDA ARAMA - SİSTEM API HAKKI KULLAN (bypass_limit_check=True)
    loading_msg = f"{len(selected_ids)} ligden maçlar getiriliyor..."
    with st.spinner(loading_msg):
        fixtures, error = api_utils.get_fixtures_by_date(API_KEY, BASE_URL, selected_ids, selected_date, bypass_limit_check=True)
    
    # Hata mesajını daha kullanıcı dostu göster
    if error:
        # Eğer başarılı sonuç varsa ve sadece rate limit uyarısıysa, warning olarak göster
        if fixtures and ("✅" in error or "Rate Limit" in error):
            st.warning(f"⚠️ Bazı ligler yüklenemedi:\n\n{error}")
            st.info("💡 Yüklenen maçlarla devam ediliyor. Eksik ligler için daha sonra tekrar deneyin.")
        else:
            st.error(f"❌ Maçlar çekilirken hata oluştu:\n\n{error}")
            if "rate limit" in error.lower() or "too many requests" in error.lower():
                st.info("💡 **Çözüm Önerileri:**\n- Daha az lig seçin (maksimum 20-25)\n- Birkaç dakika bekleyip tekrar deneyin\n- Ligleri gruplar halinde analiz edin")
            return
    
    if not fixtures: 
        st.info(f"Seçtiğiniz tarih ve liglerde maç bulunamadı.")
        return
    
    # Başarı mesajı
    if len(fixtures) > 0:
        st.success(f"✅ {len(fixtures)} maç bulundu, analiz ediliyor...")
    
    progress_bar = st.progress(0, text="Maçlar analiz ediliyor...")
    # MAÇ PANOSUNDA ÖZET ANALİZ - SİSTEM API'Sİ KULLAN (use_system_api parametresi kaldırıldı, artık her zaman sistem API)
    analyzed_fixtures = [summary for i, f in enumerate(fixtures) if (summary := analyze_fixture_summary(f, model_params)) and (progress_bar.progress((i + 1) / len(fixtures), f"Analiz: {f['home_name']}", ))]
    progress_bar.empty()
    if not analyzed_fixtures: st.error("Hiçbir maç analiz edilemedi."); return
    df = pd.DataFrame(analyzed_fixtures)
    if not df.empty and selected_date >= date.today():
        st.subheader("🏆 Günün Öne Çıkan Tahminleri")
        c1, c2, c3 = st.columns(3)
        
        best_1x2 = df.loc[df['AI Güven Puanı'].idxmax()]
        if best_1x2['AI Güven Puanı'] > BEST_BET_THRESHOLD:
            with c1:
                display_best_bet_card(title="🎯 Günün 1X2 Tahmini", match_data=best_1x2, prediction_label="Tahmin", prediction_value=best_1x2['Tahmin'], metric_label="AI Güven Puanı", metric_value=f"{best_1x2['AI Güven Puanı']:.1f}")
        
        best_over = df.loc[df['2.5 ÜST (%)'].idxmax()]
        if best_over['2.5 ÜST (%)'] > TOP_GOAL_BET_THRESHOLD:
            with c2:
                display_best_bet_card(title="📈 Günün 2.5 Üstü Tahmini", match_data=best_over, prediction_label="Tahmin", prediction_value="2.5 Gol Üstü", metric_label="Olasılık", metric_value=f"{best_over['2.5 ÜST (%)']:.1f}%")

        best_btts = df.loc[df['KG VAR (%)'].idxmax()]
        if best_btts['KG VAR (%)'] > TOP_GOAL_BET_THRESHOLD:
            with c3:
                display_best_bet_card(title="⚽ Günün KG Var Tahmini", match_data=best_btts, prediction_label="Tahmin", prediction_value="Karşılıklı Gol Var", metric_label="Olasılık", metric_value=f"{best_btts['KG VAR (%)']:.1f}%")
        st.markdown("---")
    if selected_date < date.today() and 'Sonuç' in df.columns and not df.empty:
        success_count = df['Sonuç'].str.contains('✅').sum(); total_matches = len(df)
        accuracy = (success_count / total_matches) * 100 if total_matches > 0 else 0
        st.metric("Günlük Tahmin Başarısı", f"{accuracy:.1f}%", f"{success_count} / {total_matches} doğru tahmin")
        st.markdown("---")
    st.subheader("📋 Analiz Sonuçları")
    
    # Logo sütunlarını ekle (URL formatında - ImageColumn için)
    if not df.empty and 'home_logo' in df.columns and 'away_logo' in df.columns:
        # Logo URL'lerini direkt kullan (ImageColumn için)
        cols_to_display = ["Saat", "Lig", "home_logo", "Ev Sahibi", "away_logo", "Deplasman", "Tahmin", "AI Güven Puanı", "2.5 ÜST (%)", "KG VAR (%)"]
    else:
        cols_to_display = ["Saat", "Lig", "Ev Sahibi", "Deplasman", "Tahmin", "AI Güven Puanı", "2.5 ÜST (%)", "KG VAR (%)"]
    
    if 'Gerçekleşen Skor' in df.columns and not df['Gerçekleşen Skor'].eq('').all():
        if "home_logo" in cols_to_display:
            cols_to_display.insert(7, "Gerçekleşen Skor")
            cols_to_display.insert(8, "Sonuç")
        else:
            cols_to_display.insert(5, "Gerçekleşen Skor")
            cols_to_display.insert(6, "Sonuç")
    
    st.dataframe(df[cols_to_display].sort_values("AI Güven Puanı", ascending=False), use_container_width=True, hide_index=True, column_config={
        "home_logo": st.column_config.ImageColumn("🏠", help="Ev Sahibi Logosu", width="small"),
        "away_logo": st.column_config.ImageColumn("🛫", help="Deplasman Logosu", width="small")
    })
    st.markdown("---")
    st.subheader("🔍 Detaylı Maç Analizi")
    options = [f"{r['Saat']} | {r['Lig']} | {r['Ev Sahibi']} vs {r['Deplasman']}" for _, r in df.iterrows()]
    selected = st.selectbox("Detaylı analiz için maç seçin:", options, index=None, placeholder="Tablodan bir maç seçin...")
    if selected:
        row = df[df.apply(lambda r: f"{r['Saat']} | {r['Lig']} | {r['Ev Sahibi']} vs {r['Deplasman']}" == selected, axis=1)].iloc[0]
        team_a = {'id': row['home_id'], 'name': row['Ev Sahibi'], 'logo': row.get('home_logo', '')}
        team_b = {'id': row['away_id'], 'name': row['Deplasman'], 'logo': row.get('away_logo', '')}
        with st.spinner(f"**{team_a['name']} vs {team_b['name']}** analizi yapılıyor..."):
            analyze_and_display(team_a, team_b, row['fixture_id'], model_params, 
                              league_id=row.get('league_id'), season=row.get('season'))

def build_manual_view(model_params: Dict):
    st.markdown("""
    <h1 style='text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
               -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
               background-clip: text; font-size: 2.5em; margin: 10px 0;'>
        🔩 Manuel Takım Analizi
    </h1>
    """, unsafe_allow_html=True)
    
    # API Kullanımı Bilgilendirmesi
    st.info("ℹ️ Bu sayfadaki tüm detaylı analizler kullanıcı API hakkınızı kullanacaktır. Maç listesi için sistem API'si kullanılır.")
    
    if LEAGUE_LOAD_ERROR:
        st.warning(f"Lig listesi yüklenirken uyarı: {LEAGUE_LOAD_ERROR}")

    st.markdown("---")
    st.subheader("ID veya Ad ile Hızlı Analiz")
    c1, c2 = st.columns(2)
    t1_in = c1.text_input("Ev Sahibi Takım (Ad/ID)")
    t2_in = c2.text_input("Deplasman Takımı (Ad/ID)")
    if st.button("Analizi Başlat", use_container_width=True):
        if not t1_in or not t2_in:
            st.warning("Lütfen iki takımı da girin.")
        else:
            team_a = api_utils.get_team_id(API_KEY, BASE_URL, t1_in)
            team_b = api_utils.get_team_id(API_KEY, BASE_URL, t2_in)
            if team_a and team_b:
                with st.spinner('Maç aranıyor...'):
                    info = api_utils.get_team_league_info(API_KEY, BASE_URL, team_a['id'])
                    if not info:
                        st.error(f"{team_a['name']} için sezon bilgisi bulunamadı.")
                        info = None
                    if info:
                        match, error = api_utils.find_upcoming_fixture(API_KEY, BASE_URL, team_a['id'], team_b['id'], info['season'])
                    else:
                        match, error = None, None
                if error:
                    st.error(f"Maç aranırken hata oluştu: {error}")
                elif match:
                    fixture_home, fixture_away = match['teams']['home'], match['teams']['away']
                    match_dt = datetime.fromtimestamp(match['fixture']['timestamp']).strftime('%d.%m.%Y')
                    st.success(f"✅ Maç bulundu! Tarih: {match_dt}")
                    with st.spinner('Detaylı analiz yapılıyor...'):
                        league_id_from_match = match.get('league', {}).get('id')
                        analyze_and_display(fixture_home, fixture_away, match['fixture']['id'], model_params, 
                                          league_id=league_id_from_match, season=info.get('season') if info else None)
                else:
                    st.error("Bu iki takım arasında yaklaşan bir maç bulunamadı.")
            else:
                st.error("Takımlar bulunamadı.")

    st.markdown("---")
    st.subheader("Lig ve Takım Seçerek Analiz")
    country_options = ['Tümü'] + [country for country in COUNTRY_INDEX if country]
    selected_country = st.selectbox("Ülke Filtresi", options=country_options, key="manual_country_filter")

    filtered_leagues = [
        (lid, label) for lid, label in INTERESTING_LEAGUES.items()
        if selected_country == 'Tümü' or LEAGUE_METADATA.get(lid, {}).get('country') == selected_country
    ]

    if not filtered_leagues:
        st.info("Seçilen ülke için güncel lig bulunamadı.")
    else:
        # Ligleri popülerlik sırasına göre sırala (popüler ligler üstte)
        filtered_leagues.sort(key=lambda x: get_league_priority(x[0]))
        
        league_labels = [label for _, label in filtered_leagues]
        selected_league_label = st.selectbox("Lig Seçin", options=league_labels, key="manual_league_select")
        league_id = get_league_id_from_display(selected_league_label)
        if league_id:
            season = resolve_season_for_league(league_id)
            with st.spinner("Lig takımları getiriliyor..."):
                teams_response, error = api_utils.get_teams_by_league(API_KEY, BASE_URL, league_id, season)
            if error:
                st.error(f"Takımlar getirilirken hata oluştu: {error}")
            elif not teams_response:
                st.info("Bu lig için takım bilgisi bulunamadı.")
            else:
                team_pairs = sorted([(item['team']['name'], item['team']['id'], item['team'].get('logo', '')) for item in teams_response], key=lambda x: x[0])
                sentinel = [("Takım seçin", None, '')]
                base_options = sentinel + team_pairs

                def _format_team_option(option: tuple[str, Optional[int], str]) -> str:
                    name, team_id, logo = option
                    return name if team_id is None else f"{name} ({team_id})"

                home_choice = st.selectbox(
                    "Ev Sahibi Takım",
                    options=base_options,
                    format_func=_format_team_option,
                    key="manual_home_select"
                )
                home_team = {'name': home_choice[0], 'id': home_choice[1], 'logo': home_choice[2]} if home_choice[1] else None

                away_candidates = sentinel + [opt for opt in team_pairs if not home_team or opt[1] != home_team['id']]
                away_choice = st.selectbox(
                    "Deplasman Takımı",
                    options=away_candidates,
                    format_func=_format_team_option,
                    key="manual_away_select"
                )
                away_team = {'name': away_choice[0], 'id': away_choice[1], 'logo': away_choice[2]} if away_choice[1] else None

                disabled = not (home_team and away_team)
                if st.button("Seçili Takımlarla Analiz Et", use_container_width=True, disabled=disabled):
                    with st.spinner('Maç aranıyor...'):
                        match, error = api_utils.find_upcoming_fixture(API_KEY, BASE_URL, home_team['id'], away_team['id'], season)
                    if error:
                        st.error(f"Maç aranırken hata oluştu: {error}")
                    elif match:
                        fixture_home, fixture_away = match['teams']['home'], match['teams']['away']
                        match_dt = datetime.fromtimestamp(match['fixture']['timestamp']).strftime('%d.%m.%Y')
                        if fixture_home['id'] != home_team['id']:
                            st.info("Not: Seçtiğiniz ev sahibi takım bu maçta deplasmanda yer alıyor.")
                        st.success(f"✅ Maç bulundu! Tarih: {match_dt}")
                        with st.spinner('Detaylı analiz yapılıyor...'):
                            league_id_from_match = match.get('league', {}).get('id')
                            analyze_and_display(fixture_home, fixture_away, match['fixture']['id'], model_params,
                                              league_id=league_id_from_match, season=season)
                    else:
                        st.warning("Bu iki takımın planlanan maçı bulunamadı. Takım kodlarını kullanarak farklı kombinasyonları deneyebilirsiniz.")

    st.markdown("---")
    st.subheader("⭐ Favori Liglerinizdeki Yaklaşan Maçlar")
    
    # Kullanıcının kaydedilmiş favori liglerini yükle
    username = st.session_state.get('username')
    favorite_leagues = st.session_state.get('favorite_leagues')
    
    # Session'da yoksa config'den yükle
    if favorite_leagues is None and username:
        favorite_leagues = load_user_favorite_leagues(username)
        if favorite_leagues:
            st.session_state.favorite_leagues = favorite_leagues
    
    # Hala yoksa varsayılan ligleri kullan
    if favorite_leagues is None:
        favorite_leagues = get_default_favorite_leagues()
        st.session_state.favorite_leagues = favorite_leagues

    normalized_favorites = normalize_league_labels(favorite_leagues)
    st.session_state.favorite_leagues = normalized_favorites
    
    if not normalized_favorites:
        st.info("Favori lig listeniz boş. Kenar çubuğundaki '⭐ Favori Ligleri Yönet' bölümünden ilgilendiğiniz ligleri ekleyebilirsiniz.")
    else:
        selected_ids = []
        for label in normalized_favorites:
            league_id = get_league_id_from_display(label)
            if league_id and league_id not in selected_ids:
                selected_ids.append(league_id)

        if not selected_ids:
            st.warning("Favori ligleriniz güncel katalogla eşleşmiyor. Lütfen listanızı güncelleyin.")
        else:
            today = date.today()
            tomorrow = today + timedelta(days=1)

            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**📅 Bugün ({today.strftime('%d %B %Y')})**")
                with st.spinner("Bugünün favori maçları getiriliyor..."):
                    # KULLANICI LİMİTİNİ TÜKETME - Ana sayfa için ücretsiz
                    fixtures_today, error_today = api_utils.get_fixtures_by_date(API_KEY, BASE_URL, selected_ids, today, bypass_limit_check=True)

                if error_today:
                    st.error(f"Hata: {error_today}")
                elif not fixtures_today:
                    st.info("Bugün maç yok.")
                else:
                    for fix in fixtures_today:
                        st.markdown(f"🕐 `{fix['time']}` | {fix['league_name']}")
                        st.markdown(f"⚽ **{fix['home_name']} vs {fix['away_name']}**")
                        st.markdown("---")

            with col2:
                st.markdown(f"**📅 Yarın ({tomorrow.strftime('%d %B %Y')})**")
                with st.spinner("Yarının favori maçları getiriliyor..."):
                    # KULLANICI LİMİTİNİ TÜKETME - Ana sayfa için ücretsiz
                    fixtures_tomorrow, error_tomorrow = api_utils.get_fixtures_by_date(API_KEY, BASE_URL, selected_ids, tomorrow, bypass_limit_check=True)

                if error_tomorrow:
                    st.error(f"Hata: {error_tomorrow}")
                elif not fixtures_tomorrow:
                    st.info("Yarın maç yok.")
                else:
                    for fix in fixtures_tomorrow:
                        st.markdown(f"🕐 `{fix['time']}` | {fix['league_name']}")
                        st.markdown(f"⚽ **{fix['home_name']} vs {fix['away_name']}**")
                        st.markdown("---")

    st.markdown("---")
    st.subheader("Takım ve Lig Kod Bulucu")
    show_code_finder = st.session_state.get('show_code_finder', False)
    toggle_label = "✍️ Kod Bulucuyu Göster" if not show_code_finder else "Kod Bulucuyu Gizle"
    if st.button(toggle_label, use_container_width=True, key="toggle_code_finder_manual"):
        show_code_finder = not show_code_finder
        st.session_state['show_code_finder'] = show_code_finder
    if show_code_finder:
        render_code_finder(embed=True, key_prefix="manual")

def render_code_finder(embed: bool = False, key_prefix: str = "code_finder"):
    if not embed:
        st.title("✍️ Takım ve Lig Kod Bulucu")
        st.info("Lig ve takım kodlarını bu ekrandan bulabilir, manuel analizlerde kullanabilirsiniz.")
    else:
        st.caption("Lig ve takım kodlarına buradan ulaşabilirsiniz.")

    country_options = ['Tümü'] + [country for country in COUNTRY_INDEX if country]
    selected_country = st.selectbox("Ülke filtresi", options=country_options, key=f"{key_prefix}_country")

    league_candidates = [
        (lid, label) for lid, label in INTERESTING_LEAGUES.items()
        if selected_country == 'Tümü' or LEAGUE_METADATA.get(lid, {}).get('country') == selected_country
    ]

    if not league_candidates:
        st.warning("Filtreye uygun lig bulunamadı.")
        return

    league_labels = [label for _, label in league_candidates]
    selected_league_label = st.selectbox(
        "Lig seçin",
        options=league_labels,
        key=f"{key_prefix}_league"
    )
    league_id = get_league_id_from_display(selected_league_label)
    if not league_id:
        st.error("Lig ID'si çözümlenemedi.")
        return

    season = resolve_season_for_league(league_id)
    metadata = LEAGUE_METADATA.get(league_id, {})
    with st.spinner(f"'{selected_league_label}' ligindeki takımlar getiriliyor..."):
        teams_response, error = api_utils.get_teams_by_league(API_KEY, BASE_URL, league_id, season)
    if error:
        st.error(f"Takımlar getirilirken bir hata oluştu: {error}")
        return

    st.code(f"Lig ID: {league_id}")
    st.caption(f"Ülke: {metadata.get('country', 'Bilinmiyor')} • Sezon: {season or 'Bilinmiyor'}")

    if not teams_response:
        st.warning("Bu lig için takım bilgisi bulunamadı.")
        return

    # Takımları popülerlik ve alfabetik sıraya göre sırala
    teams_data = [
        {
            'Takım Adı': item['team']['name'], 
            'Takım ID': item['team']['id'],
            '_priority': get_team_priority(item['team']['id'])  # Popülerlik skoru
        }
        for item in teams_response
    ]
    
    # Önce popülerliğe göre, sonra alfabetik sırala
    teams_data.sort(key=lambda row: (row['_priority'], row['Takım Adı']))

    search_term = st.text_input("Takım ara", key=f"{key_prefix}_search", placeholder="Takım adı girin...")
    if search_term:
        filtered_data = [row for row in teams_data if search_term.lower() in row['Takım Adı'].lower()]
    else:
        filtered_data = teams_data

    if not filtered_data:
        st.info("Arama kriterine uygun takım bulunamadı.")
        return

    # DataFrame için _priority kolonunu kaldır
    display_data = [{'Takım Adı': row['Takım Adı'], 'Takım ID': row['Takım ID']} for row in filtered_data]
    st.dataframe(pd.DataFrame(display_data), hide_index=True, use_container_width=True)


def build_codes_view():
    render_code_finder(embed=False, key_prefix="standalone")

def main():
    # KALICI OTURUM - LocalStorage ile yönetim
    # JavaScript ile localStorage'dan kullanıcı bilgisini oku
    auth_script = """
    <script>
        window.addEventListener('load', function() {
            const savedAuth = localStorage.getItem('futbol_auth');
            if (savedAuth) {
                const authData = JSON.parse(savedAuth);
                window.parent.postMessage({type: 'streamlit:setComponentValue', value: authData}, '*');
            }
        });
    </script>
    """
    
    with open('config.yaml', encoding='utf-8') as file:
        config = yaml.load(file, Loader=SafeLoader)

    any_hashed = False
    try:
        creds = config.get('credentials', {}).get('usernames', {})
        for u, info in creds.items():
            pw = info.get('password', '')
            if isinstance(pw, str) and pw.startswith('$2'):
                any_hashed = True
                break
    except Exception:
        any_hashed = False

    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )

    admin_users = config.get('admin_users', []) if isinstance(config, dict) else []
    
    # Admin listesini session_state'e kaydet (API kontrolü için gerekli)
    st.session_state['admin_users'] = admin_users
    
    # KALICI OTURUM YÖNETİMİ - Query params ile kontrol
    # URL query params'dan gelen auth bilgisini kontrol et
    query_params = st.query_params
    
    # İlk kontrol: Session state'de authentication var mı?
    if 'authentication_status' not in st.session_state:
        st.session_state['authentication_status'] = None
    
    # Giriş yapılmışsa login formu gösterme
    if st.session_state.get('authentication_status') is True:
        # Zaten giriş yapılmış, direkt ana sayfaya git
        pass
    else:
        # Giriş yapılmamış, login formunu göster
        try:
            name, authentication_status, username = authenticator.login(location='main', fields={'Form name': 'Giriş Yap'})
            
            # Başarılı giriş sonrası session state'e kaydet ve URL'e ekle
            if authentication_status:
                # IP kısıtlaması kontrolü
                user_ip = api_utils.get_public_ip()
                ip_allowed, ip_message = api_utils.check_ip_restriction(username, user_ip)
                
                if not ip_allowed:
                    st.error(f"🚫 Giriş Reddedildi: {ip_message}")
                    st.info(f"Mevcut IP Adresiniz: {user_ip}")
                    st.warning("Yetkilendirilmiş bir IP adresinden giriş yapmanız gerekmektedir. Lütfen sistem yöneticisi ile iletişime geçin.")
                    st.session_state['authentication_status'] = False
                    st.stop()
                
                st.session_state['authentication_status'] = True
                st.session_state['username'] = username
                st.session_state['name'] = name
                
                # Query params'a ekle (kalıcı oturum için)
                st.query_params['auth_user'] = username
                st.rerun()
            elif authentication_status is False:
                st.session_state['authentication_status'] = False
            elif authentication_status is None:
                st.session_state['authentication_status'] = None
        except Exception as e:
            if 'authentication_status' not in st.session_state:
                st.session_state['authentication_status'] = None

    if st.session_state.get('authentication_status') is not True:
        
        # LOGO EN ÜSTTE - Daha büyük ve etkileyici
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            display_logo(sidebar=False, size="large")
            st.markdown("""
            <h1 style='text-align: center; color: #667eea; margin-top: -10px; font-size: 2.8em;'>
                ⚽ Güvenilir Analiz
            </h1>
            <p style='text-align: center; color: #888; font-size: 1.2em; margin-bottom: 30px;'>
                Yapay Zeka Destekli Profesyonel Maç Tahminleri
            </p>
            """, unsafe_allow_html=True)
        
        # Login formu için giriş yapılmamış durumu kontrol et
        if st.session_state.get('authentication_status') is None:
            # İlk açılış - hoş geldiniz mesajı
            pass
        
        # Giriş Formu Alanı
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Şifre/Kullanıcı Adı Unuttum Bölümü
        st.markdown("---")
        with st.expander("🔑 Şifre veya Kullanıcı Adı mı Unuttunuz?"):
            st.markdown("### Bilgilerinizi Güncelleyin")
            st.info("Mevcut bilgilerinizden en az birini doğru girdiğinizde şifrenizi veya kullanıcı adınızı güncelleyebilirsiniz.")
            
            col1, col2 = st.columns(2)
            with col1:
                reset_username = st.text_input("Mevcut Kullanıcı Adınız", key="reset_username")
                reset_email = st.text_input("E-posta Adresiniz", key="reset_email")
            with col2:
                new_username_reset = st.text_input("Yeni Kullanıcı Adı (opsiyonel)", key="new_username_reset")
                new_password_reset = st.text_input("Yeni Şifre", type="password", key="new_password_reset")
                new_password_confirm = st.text_input("Yeni Şifre (Tekrar)", type="password", key="new_password_confirm")
            
            if st.button("🔄 Bilgilerimi Güncelle", key="reset_credentials"):
                if not reset_username and not reset_email:
                    st.error("Lütfen en az kullanıcı adınızı veya e-postanızı girin.")
                elif not new_password_reset or not new_password_confirm:
                    st.error("Lütfen yeni şifrenizi iki kez girin.")
                elif new_password_reset != new_password_confirm:
                    st.error("Şifreler eşleşmiyor!")
                else:
                    # Kullanıcıyı doğrula
                    found_user = None
                    for username, user_info in config['credentials']['usernames'].items():
                        if reset_username and username == reset_username:
                            found_user = username
                            break
                        elif reset_email and user_info.get('email') == reset_email:
                            found_user = username
                            break
                    
                    if found_user:
                        try:
                            import bcrypt
                            # Yeni şifreyi hashle
                            hashed_pw = bcrypt.hashpw(new_password_reset.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                            
                            # Kullanıcı adını güncelle (eğer girilmişse)
                            if new_username_reset and new_username_reset != found_user:
                                # IP hakkını transfer et
                                try:
                                    ip_assignments = api_utils._get_ip_assignments()
                                    # Eski kullanıcıya atanmış IP'yi bul
                                    old_user_ip = None
                                    for ip, assigned_user in ip_assignments.items():
                                        if assigned_user == found_user:
                                            old_user_ip = ip
                                            break
                                    
                                    # IP hakkını yeni kullanıcıya transfer et
                                    if old_user_ip:
                                        api_utils._set_ip_assignment(old_user_ip, new_username_reset)
                                        st.info(f"🔄 IP hakkı ({old_user_ip}) '{found_user}' hesabından '{new_username_reset}' hesabına transfer edildi.")
                                    
                                    # user_usage.json'dan eski kullanıcı verilerini yeniye kopyala
                                    usage_data = api_utils._read_usage_file()
                                    if found_user in usage_data:
                                        # Eski kullanıcının kullanım verilerini yeniye kopyala
                                        usage_data[new_username_reset] = usage_data[found_user].copy()
                                        # Eski kullanıcıyı sil
                                        del usage_data[found_user]
                                        
                                        # Limit ayarlarını da transfer et
                                        if '_limits' in usage_data and found_user in usage_data['_limits']:
                                            usage_data['_limits'][new_username_reset] = usage_data['_limits'][found_user]
                                            del usage_data['_limits'][found_user]
                                        
                                        if '_monthly_limits' in usage_data and found_user in usage_data['_monthly_limits']:
                                            usage_data['_monthly_limits'][new_username_reset] = usage_data['_monthly_limits'][found_user]
                                            del usage_data['_monthly_limits'][found_user]
                                        
                                        # Kaydet
                                        api_utils._write_usage_file(usage_data)
                                        st.info(f"📊 API kullanım verileri '{found_user}' hesabından '{new_username_reset}' hesabına transfer edildi.")
                                except Exception as e:
                                    st.warning(f"⚠️ IP hakkı transferi sırasında uyarı: {e}")
                                
                                # Yeni kullanıcı adıyla yeni entry oluştur
                                config['credentials']['usernames'][new_username_reset] = config['credentials']['usernames'][found_user].copy()
                                config['credentials']['usernames'][new_username_reset]['password'] = hashed_pw
                                # Eski kullanıcıyı sil
                                del config['credentials']['usernames'][found_user]
                                updated_username = new_username_reset
                            else:
                                # Sadece şifreyi güncelle
                                config['credentials']['usernames'][found_user]['password'] = hashed_pw
                                updated_username = found_user
                            
                            # config.yaml'e kaydet
                            with open('config.yaml', 'w', encoding='utf-8') as f:
                                yaml.dump(config, f, allow_unicode=True)
                            
                            st.success(f"✅ Bilgileriniz başarıyla güncellendi! Yeni kullanıcı adınız: **{updated_username}**")
                            st.info("Lütfen yeni bilgilerinizle giriş yapın.")
                            
                            # Sayfayı yenile
                            import time
                            time.sleep(2)
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"Güncelleme sırasında hata oluştu: {e}")
                    else:
                        st.error("❌ Girdiğiniz bilgilerle eşleşen bir kullanıcı bulunamadı.")
        
        st.markdown("---")

    if st.session_state["authentication_status"]:
        username = st.session_state.get('username')
        st.session_state['tier'] = config['credentials']['usernames'][username]['tier']
        user_tier = st.session_state.get('tier')

        try:
            api_utils.ensure_user_limits(username, user_tier)
        except Exception:
            pass

        # IP KISITLAMASI KONTROLÜ - Admin hariç
        if username not in admin_users:
            try:
                client_ip = api_utils.get_client_ip()
                if client_ip:
                    ip_assignments = api_utils._get_ip_assignments()
                    assigned_user = ip_assignments.get(client_ip)
                    
                    if not assigned_user:
                        # Bu IP ilk kez kullanılıyor - kaydet
                        api_utils._set_ip_assignment(client_ip, username)
                    elif assigned_user != username:
                        # Bu IP başka bir kullanıcıya ait! AMA önce kontrol et:
                        # Eğer assigned_user config.yaml'de yoksa (silinmişse), IP'yi mevcut kullanıcıya transfer et
                        if assigned_user not in config['credentials']['usernames']:
                            # Eski hesap silinmiş, IP'yi yeni hesaba transfer et
                            api_utils._set_ip_assignment(client_ip, username)
                            st.success(f"✅ **IP Transferi Tamamlandı:** '{assigned_user}' hesabı bulunamadı, IP hakkı '{username}' hesabına otomatik transfer edildi.")
                        else:
                            # Başka aktif bir kullanıcıya ait, engelle
                            st.error(f"⛔ **IP KISITLAMASI:** Bu IP adresi zaten '{assigned_user}' kullanıcısına tanımlı. Aynı IP'den birden fazla hesap kullanılamaz.")
                            st.warning("Lütfen çıkış yapın ve kendi IP adresinizden giriş yapın.")
                            if st.button("🚪 Çıkış Yap", key="ip_restriction_logout"):
                                authenticator.logout()
                                # Session state temizle
                                for key in ['authentication_status', 'username', 'name', 'tier', 'bypass_login', 'view']:
                                    if key in st.session_state:
                                        del st.session_state[key]
                                st.rerun()
                            st.stop()
            except Exception as e:
                # IP kontrolünde hata olursa uygulamayı durdurma
                print(f"IP kontrol hatası: {e}")

        if 'view' not in st.session_state: 
            # URL'den view parametresini al, yoksa 'home' yap
            query_params = st.query_params
            view_param = query_params.get('view', 'home')
            # Geçerli view'lar: home, dashboard, manual, codes
            valid_views = ['home', 'dashboard', 'manual', 'codes']
            st.session_state.view = view_param if view_param in valid_views else 'home'
        
        # Favori ligleri config'den yükle (ilk giriş)
        if 'favorite_leagues' not in st.session_state or st.session_state.favorite_leagues is None:
            username = st.session_state.get('username')
            if username:
                loaded_favorites = load_user_favorite_leagues(username)
                if loaded_favorites:
                    st.session_state.favorite_leagues = loaded_favorites
                else:
                    st.session_state.favorite_leagues = None
            else:
                st.session_state.favorite_leagues = None

        # ============================================================================
        # PROFESYONEL SİDEBAR YAPISI
        # ============================================================================
        
        # Logo
        display_logo(sidebar=True, size="medium")
        
        # Hoşgeldin Başlığı
        st.sidebar.markdown(f"""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 20px; border-radius: 12px; margin-bottom: 10px; text-align: center;'>
            <h2 style='color: white; margin: 0;'>👋 Hoş Geldin</h2>
            <p style='color: rgba(255,255,255,0.9); margin: 8px 0 0 0; font-size: 1.1em;'>{st.session_state['name']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Branding
        st.sidebar.markdown("""
        <div style='text-align: center; margin: 10px 0 20px 0;'>
            <p style='color: #667eea; font-weight: 600; font-size: 0.9em; margin: 0;'>⚽ Güvenilir Analiz</p>
            <p style='color: #999; font-size: 0.75em; margin: 5px 0 0 0;'>Yapay Zeka Destekli Tahminler</p>
        </div>
        """, unsafe_allow_html=True)
        
        # ============================================================================
        # NAVİGASYON MENÜSÜ
        # ============================================================================
        st.sidebar.markdown("### 🧭 Navigasyon")
        
        nav_col1, nav_col2, nav_col3, nav_col4 = st.sidebar.columns(4)
        with nav_col1:
            if st.button("🏠", use_container_width=True, key="nav_home", help="Ana Sayfa"):
                update_url_and_rerun('home')
        with nav_col2:
            if st.button("🗓️", use_container_width=True, key="nav_dashboard", help="Maç Panosu"):
                update_url_and_rerun('dashboard')
        with nav_col3:
            if st.button("🔩", use_container_width=True, key="nav_manual", help="Manuel Analiz"):
                update_url_and_rerun('manual')
        with nav_col4:
            if st.button("🔍", use_container_width=True, key="nav_enhanced", help="Gelişmiş Analiz"):
                update_url_and_rerun('enhanced')
        
        st.sidebar.markdown("---")
        
        # ============================================================================
        # HESAP BİLGİLERİ VE İSTATİSTİKLER
        # ============================================================================
        st.sidebar.markdown("### 👤 Hesap Bilgileri")
        
        # Admin kontrolü
        try:
            usage_data = api_utils._read_usage_file()
            per_user_limit = usage_data.get('_limits', {}).get(username)
        except Exception:
            per_user_limit = None
        
        is_admin = username in st.session_state.get('admin_users', [])
        
        if is_admin:
            st.sidebar.success("👑 **Admin Hesabı**")
            st.sidebar.metric(label="API Hakkı", value="♾️ Sınırsız", delta="Admin erişimi")
        else:
            user_limit = int(per_user_limit) if per_user_limit is not None else api_utils.get_api_limit_for_user(user_tier)
            current_usage = api_utils.get_current_usage(username)
            remaining_requests = max(0, user_limit - current_usage.get('count', 0))
            
            # Tier badge
            tier_color = "green" if user_tier == 'ücretli' else "blue"
            tier_icon = "💎" if user_tier == 'ücretli' else "🆓"
            st.sidebar.info(f"{tier_icon} **{user_tier.capitalize()} Üyelik**")
            
            # API kullanım progress bar
            usage_percentage = (current_usage.get('count', 0) / user_limit * 100) if user_limit > 0 else 0
            st.sidebar.progress(usage_percentage / 100, text=f"API Kullanımı: {current_usage.get('count', 0)}/{user_limit}")
            
        st.sidebar.markdown("---")
        
        # ============================================================================
        # HIZLI ERİŞİM AYARLARI
        # ============================================================================
        st.sidebar.markdown("### ⚙️ Hızlı Ayarlar")
        
        with st.sidebar.expander("⭐ Favori Ligleri Yönet", expanded=False):
            all_leagues = list(INTERESTING_LEAGUES.values())
            stored_favorites = st.session_state.get('favorite_leagues')
            
            # Config'den yükle
            if stored_favorites is None and username:
                stored_favorites = load_user_favorite_leagues(username)
                if stored_favorites:
                    st.session_state.favorite_leagues = stored_favorites
            
            # Hala yoksa varsayılanları kullan
            if stored_favorites is None:
                stored_favorites = get_default_favorite_leagues()
                st.session_state.favorite_leagues = stored_favorites
            
            current_favorites = normalize_league_labels(stored_favorites)
            st.info(f"📋 Seçili: {len(current_favorites)} lig")
            new_favorites = st.multiselect("Favori liglerinizi seçin:", options=all_leagues, default=current_favorites, key="fav_leagues_multi")
            if st.button("✅ Favorileri Kaydet", key="save_fav", use_container_width=True):
                st.session_state.favorite_leagues = new_favorites
                # Config.yaml'e kaydet
                if username:
                    if save_user_favorite_leagues(username, new_favorites):
                        st.success("✅ Kalıcı olarak kaydedildi!")
                    else:
                        st.warning("⚠️ Oturum için kaydedildi.")
                else:
                    st.warning("⚠️ Oturum için kaydedildi.")
                safe_rerun()

        with st.sidebar.expander("🎯 Model Parametreleri", expanded=False):
            st.caption("Tahmin modelini özelleştirin")
            value_threshold = st.slider("Değerli Oran Eşiği (%)", 1, 20, 5, help="Piyasa oranlarından sapma eşiği")
            injury_impact = st.slider("Sakatlık Etkisi", 0.5, 1.0, DEFAULT_KEY_PLAYER_IMPACT_MULTIPLIER, 0.05, help="Kilit oyuncu sakatlıklarının etkisi")
            max_goals = st.slider("Maksimum Gol Beklentisi", 1.5, 4.0, DEFAULT_MAX_GOAL_EXPECTANCY, 0.1, help="Tek maçta beklenen maksimum gol")
            st.session_state.model_params = {
                "injury_impact": injury_impact,
                "max_goals": max_goals,
                "value_threshold": value_threshold,
            }
            st.success("✅ Ayarlar uygulandı")

        with st.sidebar.expander("👤 Hesap Ayarları", expanded=False):
            st.write(f"**👤 Kullanıcı Adı:** {username}")
            st.write(f"**📧 E-posta:** {config['credentials']['usernames'][username].get('email', 'N/A')}")
            
            st.markdown("#### 🔑 Parola Değiştir")
            new_password = st.text_input("Yeni Parola", type="password", key="new_pw")
            confirm_password = st.text_input("Parolayı Doğrula", type="password", key="confirm_pw")
            if st.button("Parolayı Güncelle", use_container_width=True, key="update_pw_btn"):
                if not new_password or not confirm_password:
                    st.warning("Lütfen her iki alanı da doldurun.")
                elif new_password != confirm_password:
                    st.error("Parolalar eşleşmiyor!")
                else:
                    result = change_password(username, new_password)
                    if result == 0:
                        st.success("✅ Parola güncellendi.")
                    else:
                        st.error("❌ Güncelleme başarısız.")
            
            st.markdown("#### 📧 E-posta Değiştir")
            current_email = config['credentials']['usernames'][username].get('email', '')
            new_email = st.text_input("Yeni E-posta", value=current_email, key="new_email")
            if st.button("E-postayı Güncelle", use_container_width=True, key="update_email_btn"):
                if not new_email:
                    st.warning("E-posta alanı boş olamaz.")
                else:
                    result = change_email(username, new_email)
                    if result == 0:
                        st.success("✅ E-posta güncellendi.")
                        st.rerun()
                    else:
                        st.error("❌ Güncelleme başarısız.")
        
        st.sidebar.markdown("---")
        
        # ============================================================================
        # ÇIKIŞ BUTONU
        # ============================================================================
        if st.sidebar.button("🚪 Çıkış Yap", use_container_width=True, key='logout_button_custom', type="primary"):
            authenticator.logout()
            st.session_state['authentication_status'] = False
            st.session_state['username'] = None
            st.session_state['name'] = None
            # Query params'dan auth_user'ı sil
            if 'auth_user' in st.query_params:
                del st.query_params['auth_user']
            # Session state temizle
            for key in ['authentication_status', 'username', 'name', 'tier', 'bypass_login', 'view']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
        
        # ============================================================================
        # CACHE YÖNETİMİ - SADECE ADMIN
        # ============================================================================
        if is_admin:
            with st.sidebar.expander("🔄 Önbellek Yönetimi", expanded=False):
                st.markdown("**Önbelleği Temizle**")
                st.caption("Eski analiz sonuçlarını temizler ve yeni veriler çeker.")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🗑️ Cache Temizle", use_container_width=True, type="primary"):
                        st.cache_data.clear()
                        st.success("✅ Tüm önbellek temizlendi!")
                        st.info("Sayfa yenilenecek...")
                        import time
                        time.sleep(1)
                        st.rerun()
                
                with col2:
                    if st.button("🔄 Sayfayı Yenile", use_container_width=True):
                        st.rerun()
                
                st.caption("⏱️ Cache süreleri: Analizler 1 saat, Takım verileri 24 saat")
            
            st.sidebar.markdown("---")
        
        # ============================================================================
        # YÖNETİCİ PANELİ
        # ============================================================================

        if is_admin:
            with st.sidebar.expander("🔧 Yönetici Paneli", expanded=False):
                admin_tab = st.radio(
                    "Admin İşlemleri",
                    ["👥 Kullanıcı Yönetimi", "📊 İstatistikler", "⚙️ Sistem Ayarları", "🛡️ Admin Yönetimi"],
                    horizontal=False,
                    key="admin_tab_selector"
                )
                
                all_users = list(config.get('credentials', {}).get('usernames', {}).keys())
                
                # ==================== KULLANICI YÖNETİMİ ====================
                if admin_tab == "👥 Kullanıcı Yönetimi":
                    st.markdown("### 👥 Kullanıcı Yönetimi")
                    
                    # Kullanıcı Listesi
                    with st.expander("📋 Tüm Kullanıcılar", expanded=True):
                        users_info = api_utils.get_all_users_info()
                        if users_info:
                            for username, info in users_info.items():
                                col1, col2 = st.columns([3, 1])
                                with col1:
                                    tier_emoji = "💎" if info['tier'] == 'ücretli' else "🆓"
                                    st.markdown(f"**{tier_emoji} {username}** - {info['name']}")
                                    st.caption(f"📧 {info['email']} | 📊 {info['usage_today']}/{info['daily_limit']} günlük")
                                with col2:
                                    if st.button("🔍", key=f"view_{username}", help="Detayları Gör"):
                                        st.session_state[f'selected_user_detail'] = username
                    
                    st.markdown("---")
                    
                    # Kullanıcı Detayları ve İşlemler
                    selected_user = st.selectbox('İşlem yapmak için kullanıcı seçin:', options=[''] + all_users, key="user_mgmt_select")
                    
                    if selected_user:
                        users_info = api_utils.get_all_users_info()
                        user_info = users_info.get(selected_user, {})
                        
                        # Kullanıcı Bilgileri
                        st.markdown(f"### 📝 {selected_user} - Detaylar")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Seviye", user_info.get('tier', 'N/A').upper())
                        with col2:
                            st.metric("Bugün Kullanım", f"{user_info.get('usage_today', 0)}/{user_info.get('daily_limit', 0)}")
                        with col3:
                            st.metric("Bu Ay Kullanım", user_info.get('usage_month', 0))
                        
                        # Seviye Değiştirme
                        with st.expander("🔄 Seviye Değiştir"):
                            current_tier = user_info.get('tier', 'ücretsiz')
                            new_tier = st.selectbox('Yeni Seviye', options=['ücretsiz', 'ücretli'], 
                                                    index=0 if current_tier == 'ücretsiz' else 1,
                                                    key=f"tier_change_{selected_user}")
                            if st.button("Seviye Güncelle", key=f"update_tier_{selected_user}"):
                                success, message = api_utils.set_user_tier(selected_user, new_tier)
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
                        
                        # Şifre Sıfırlama
                        with st.expander("🔑 Şifre Sıfırla"):
                            new_password = st.text_input("Yeni Şifre", type="password", key=f"new_pwd_{selected_user}")
                            new_password_confirm = st.text_input("Şifre Tekrar", type="password", key=f"new_pwd_confirm_{selected_user}")
                            if st.button("Şifre Güncelle", key=f"reset_pwd_{selected_user}"):
                                if not new_password:
                                    st.error("Lütfen yeni şifre girin.")
                                elif new_password != new_password_confirm:
                                    st.error("Şifreler eşleşmiyor!")
                                else:
                                    success, message = api_utils.reset_user_password(selected_user, new_password)
                                    if success:
                                        st.success(message)
                                    else:
                                        st.error(message)
                        
                        # IP Kısıtlama
                        with st.expander("🌐 IP Kısıtlama"):
                            ip_restricted = user_info.get('ip_restricted', False)
                            allowed_ips = user_info.get('allowed_ips', [])
                            
                            st.toggle("IP Kısıtlaması Aktif", value=ip_restricted, key=f"ip_toggle_{selected_user}")
                            
                            if st.session_state.get(f"ip_toggle_{selected_user}", False):
                                st.markdown("**İzin Verilen IP Adresleri:**")
                                if allowed_ips:
                                    for ip in allowed_ips:
                                        col1, col2 = st.columns([4, 1])
                                        with col1:
                                            st.code(ip)
                                        with col2:
                                            if st.button("❌", key=f"remove_ip_{selected_user}_{ip}"):
                                                allowed_ips.remove(ip)
                                                success, msg = api_utils.set_ip_restriction(selected_user, True, allowed_ips)
                                                if success:
                                                    st.rerun()
                                
                                new_ip = st.text_input("Yeni IP Ekle", placeholder="örn: 192.168.1.100", key=f"new_ip_{selected_user}")
                                if st.button("IP Ekle", key=f"add_ip_{selected_user}"):
                                    if new_ip:
                                        if new_ip not in allowed_ips:
                                            allowed_ips.append(new_ip)
                                        success, message = api_utils.set_ip_restriction(selected_user, True, allowed_ips)
                                        if success:
                                            st.success(message)
                                            st.rerun()
                                        else:
                                            st.error(message)
                            
                            if st.button("IP Ayarlarını Kaydet", key=f"save_ip_{selected_user}"):
                                enabled = st.session_state.get(f"ip_toggle_{selected_user}", False)
                                success, message = api_utils.set_ip_restriction(selected_user, enabled, allowed_ips)
                                if success:
                                    st.success(message)
                                else:
                                    st.error(message)
                        
                        # Limitler
                        with st.expander("📊 Limit Yönetimi"):
                            daily_limit = st.number_input('Günlük Limit (0 = varsayılan)', min_value=0, value=user_info.get('daily_limit', 0), step=50, key=f"daily_lim_{selected_user}")
                            monthly_limit = st.number_input('Aylık Limit (0 = yok)', min_value=0, value=user_info.get('monthly_limit') or 0, step=100, key=f"monthly_lim_{selected_user}")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button('Günlük Limiti Uygula', key=f"apply_daily_{selected_user}"):
                                    api_utils.set_user_daily_limit(selected_user, int(daily_limit))
                                    st.success(f'Günlük limit güncellendi: {daily_limit}')
                            with col2:
                                if st.button('Aylık Limiti Uygula', key=f"apply_monthly_{selected_user}"):
                                    api_utils.set_user_monthly_limit(selected_user, int(monthly_limit))
                                    st.success(f'Aylık limit güncellendi: {monthly_limit}')
                            
                            st.markdown("---")
                            st.markdown("**🔄 Sayaç Sıfırlama**")
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button('🗑️ Günlük Sayacı Sıfırla', key=f"reset_daily_{selected_user}", type="secondary"):
                                    api_utils.reset_daily_usage(selected_user)
                                    st.success(f'✅ {selected_user} kullanıcısının günlük sayacı sıfırlandı!')
                                    st.rerun()
                            with col2:
                                if st.button('🗑️ Aylık Sayacı Sıfırla', key=f"reset_monthly_{selected_user}", type="secondary"):
                                    # Aylık sayacı sıfırlama fonksiyonu
                                    try:
                                        data = api_utils._read_usage_file()
                                        if selected_user in data:
                                            data[selected_user]['monthly_count'] = 0
                                            api_utils._write_usage_file(data)
                                            st.success(f'✅ {selected_user} kullanıcısının aylık sayacı sıfırlandı!')
                                            st.rerun()
                                        else:
                                            st.error('Kullanıcı bulunamadı!')
                                    except Exception as e:
                                        st.error(f'Hata: {str(e)}')
                        
                        # Kullanıcı Silme
                        with st.expander("🗑️ Kullanıcıyı Sil", expanded=False):
                            st.warning(f"⚠️ **{selected_user}** kullanıcısını silmek üzeresiniz. Bu işlem geri alınamaz!")
                            confirm_delete = st.text_input(f"Silmek için '{selected_user}' yazın:", key=f"confirm_delete_{selected_user}")
                            if st.button("Kullanıcıyı Sil", key=f"delete_user_{selected_user}", type="primary"):
                                if confirm_delete == selected_user:
                                    success, message = api_utils.delete_user(selected_user)
                                    if success:
                                        st.success(message)
                                        st.rerun()
                                    else:
                                        st.error(message)
                                else:
                                    st.error("Kullanıcı adı eşleşmiyor!")
                
                # ==================== İSTATİSTİKLER ====================
                elif admin_tab == "📊 İstatistikler":
                    st.markdown("### 📊 Sistem İstatistikleri")
                    
                    users_info = api_utils.get_all_users_info()
                    
                    # Genel İstatistikler
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Toplam Kullanıcı", len(users_info))
                    with col2:
                        paid_users = sum(1 for u in users_info.values() if u['tier'] == 'ücretli')
                        st.metric("Ücretli Kullanıcı", paid_users)
                    with col3:
                        total_usage_today = sum(u['usage_today'] for u in users_info.values())
                        st.metric("Bugün Toplam Kullanım", total_usage_today)
                    with col4:
                        total_usage_month = sum(u['usage_month'] for u in users_info.values())
                        st.metric("Bu Ay Toplam Kullanım", total_usage_month)
                    
                    st.markdown("---")
                    
                    # En Aktif Kullanıcılar
                    st.markdown("### 🔥 En Aktif Kullanıcılar (Bu Ay)")
                    sorted_users = sorted(users_info.items(), key=lambda x: x[1]['usage_month'], reverse=True)[:10]
                    
                    for idx, (username, info) in enumerate(sorted_users, 1):
                        col1, col2, col3 = st.columns([1, 3, 2])
                        with col1:
                            st.markdown(f"**#{idx}**")
                        with col2:
                            tier_emoji = "💎" if info['tier'] == 'ücretli' else "🆓"
                            st.markdown(f"{tier_emoji} **{username}**")
                        with col3:
                            st.markdown(f"📊 {info['usage_month']} kullanım")
                    
                    st.markdown("---")
                    
                    # Export İstatistikler
                    if st.button("📥 İstatistikleri Export Et (JSON)", key="export_stats"):
                        export_data = api_utils.export_usage_stats()
                        st.download_button(
                            label="İndir",
                            data=json.dumps(export_data, indent=2, ensure_ascii=False),
                            file_name=f"usage_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )
                
                # ==================== SİSTEM AYARLARI ====================
                elif admin_tab == "⚙️ Sistem Ayarları":
                    st.markdown("### ⚙️ Sistem Ayarları")
                    
                    # Sayaç Yönetimi
                    with st.expander("🔄 Sayaç Yönetimi", expanded=True):
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("🔄 Tüm Günlük Sayaçları Sıfırla", key="reset_daily_all"):
                                success, message = api_utils.reset_all_daily_counters()
                                if success:
                                    st.success(message)
                                else:
                                    st.error(message)
                        with col2:
                            if st.button("🔄 Tüm Aylık Sayaçları Sıfırla", key="reset_monthly_all"):
                                success, message = api_utils.reset_all_monthly_counters()
                                if success:
                                    st.success(message)
                                else:
                                    st.error(message)
                    
                    # Cache Yönetimi
                    with st.expander("🗑️ Önbellek Yönetimi"):
                        if st.button("🗑️ Tüm Önbelleği Temizle", key="clear_cache_admin"):
                            st.cache_data.clear()
                            st.success("Önbellek temizlendi!")
                            safe_rerun()
                    
                    # Toplu İşlemler
                    with st.expander("⚡ Toplu İşlemler"):
                        st.markdown("**Tüm Kullanıcılar İçin Varsayılan Limitleri Ayarla**")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Ücretsiz → 100", key="bulk_free"):
                                users_info = api_utils.get_all_users_info()
                                count = 0
                                for username, info in users_info.items():
                                    if info['tier'] == 'ücretsiz':
                                        api_utils.set_user_daily_limit(username, 100)
                                        count += 1
                                st.success(f"{count} ücretsiz kullanıcı için limit 100 olarak ayarlandı.")
                        with col2:
                            if st.button("Ücretli → 500", key="bulk_paid"):
                                users_info = api_utils.get_all_users_info()
                                count = 0
                                for username, info in users_info.items():
                                    if info['tier'] == 'ücretli':
                                        api_utils.set_user_daily_limit(username, 500)
                                        count += 1
                                st.success(f"{count} ücretli kullanıcı için limit 500 olarak ayarlandı.")
                
                # ==================== ADMİN YÖNETİMİ ====================
                elif admin_tab == "🛡️ Admin Yönetimi":
                    st.markdown("### 🛡️ Admin Yönetimi")
                    
                    admin_users = api_utils.get_admin_users()
                    
                    # Mevcut Adminler
                    with st.expander("👑 Mevcut Admin Kullanıcılar", expanded=True):
                        if admin_users:
                            for admin in admin_users:
                                col1, col2 = st.columns([4, 1])
                                with col1:
                                    st.markdown(f"👑 **{admin}**")
                                with col2:
                                    if admin != st.session_state.get('username'):  # Kendini silemez
                                        if st.button("❌", key=f"remove_admin_{admin}"):
                                            success, message = api_utils.remove_admin_user(admin)
                                            if success:
                                                st.success(message)
                                                st.rerun()
                                            else:
                                                st.error(message)
                        else:
                            st.info("Admin kullanıcı bulunamadı.")
                    
                    st.markdown("---")
                    
                    # Admin Ekle
                    with st.expander("➕ Yeni Admin Ekle"):
                        available_users = [u for u in all_users if u not in admin_users]
                        if available_users:
                            new_admin = st.selectbox("Kullanıcı Seçin", options=[''] + available_users, key="new_admin_select")
                            if st.button("Admin Yetkisi Ver", key="add_admin_btn"):
                                if new_admin:
                                    success, message = api_utils.add_admin_user(new_admin)
                                    if success:
                                        st.success(message)
                                        st.rerun()
                                    else:
                                        st.error(message)
                                else:
                                    st.warning("Lütfen bir kullanıcı seçin.")
                        else:
                            st.info("Tüm kullanıcılar zaten admin.")
                    
                    st.markdown("---")
                    st.info("💡 **Not:** Kendinizin admin yetkisini kaldıramazsınız.")
        
        st.sidebar.markdown("---")
        
        # 📖 Detaylı Bilgilendirme Bölümü
        with st.sidebar.expander("ℹ️ Detaylı Bilgilendirme"):
            st.markdown("### 📊 Sistemimiz Nasıl Çalışır?")
            
            st.markdown("#### 🏠 Ana Sayfa")
            st.markdown("""
            - **Günün Öne Çıkan Tahminleri**: AI güven puanı en yüksek maçları otomatik seçer
            - **Hızlı Takım Araması**: Herhangi bir takımın sıradaki maçını anında bulun
            - **Favori Ligleriniz**: Seçtiğiniz liglerdeki bugün ve yarının maçlarını görüntüleyin
            """)
            
            st.markdown("#### 🗓️ Maç Panosu")
            st.markdown("""
            - **Tarih Seçimi**: Geçmiş veya gelecek tarihler için analiz yapın
            - **Çoklu Lig Seçimi**: Birden fazla ligi aynı anda analiz edin
            - **Tahmin Başarı Oranı**: Geçmiş tarihler için modelimizin doğruluk oranını görün
            - **Değerli Oranlar**: Model tahmininin piyasa oranlarından sapmasını tespit edin
            """)
            
            st.markdown("#### 🔩 Manuel Analiz")
            st.markdown("""
            - **Takım Seçimi**: İki takım arasında özel maç analizi yapın
            - **Gerçek Zamanlı Veri**: API üzerinden canlı maç ve takım verilerini kullanır
            """)
            
            st.markdown("---")
            st.markdown("### 🎯 Analiz Sekmeleri")
            
            st.markdown("**📊 Tahmin Özeti**")
            st.markdown("""
            - Gol beklentisi ve 1X2 tahminleri
            - Model vs Piyasa karşılaştırması
            - AI güven puanı ve tahmin nedenleri
            - 2.5 Üst/Alt ve Karşılıklı Gol tahminleri
            """)
            
            st.markdown("**📈 İstatistikler**")
            st.markdown("""
            - Son 5 maçın form trendi (G/B/M)
            - Radar grafiği ile görsel karşılaştırma
            - Ev sahibi ve deplasman istatistikleri
            - İstikrar puanı ve performans göstergeleri
            """)
            
            st.markdown("**🎲 Detaylı İddaa**")
            st.markdown("""
            - **Handikap Bahisleri**: -0.5, -1.5, -2.5 tahminleri
            - **İlk Yarı**: 1X2 ve 1.5 Üst/Alt tahminleri
            - **Korner**: Beklenen korner sayısı ve üst/alt tahminleri
            - **Kart**: Sarı/kırmızı kart olasılıkları
            - Her kategori için piyasa oranlarıyla karşılaştırma
            """)
            
            st.markdown("**🚑 Eksikler**")
            st.markdown("""
            - Sakatlık ve ceza durumu
            - Kilit oyuncuların durumu
            - Maça çıkamayacak futbolcular
            """)
            
            st.markdown("**📊 Puan Durumu**")
            st.markdown("""
            - Canlı lig sıralaması
            - Form, galibiyet/beraberlik/mağlubiyet istatistikleri
            - Takımların lig içindeki konumu
            """)
            
            st.markdown("**⚔️ H2H Analizi**")
            st.markdown("""
            - Son karşılaşmalar geçmişi
            - Kafa kafaya galibiyet istatistikleri
            - Ortalama gol sayıları
            """)
            
            st.markdown("**⚖️ Hakem Analizi**")
            st.markdown("""
            - Hakemin sertlik düzeyi
            - Maç başına ortalama kart sayısı
            - Hakem faktörünün tahmine etkisi
            """)
            
            st.markdown("**⚙️ Analiz Parametreleri**")
            st.markdown("""
            - Modelin kullandığı tüm faktörler
            - Elo reytingi, momentum, form katsayıları
            - Dinlenme süresi, sakatlık faktörleri
            - H2H dominance, takım değeri karşılaştırması
            """)
        
        st.sidebar.markdown("---")
        
        # 🏆 Neden Bize Güvenmelisiniz?
        with st.sidebar.expander("🏆 Neden Bize Güvenmelisiniz?"):
            st.markdown("### 🎓 Bilim ve Teknoloji Temelli Analiz")
            
            st.markdown("""
            Futbol tahmin sistemimiz **rastgele tahminlerden** çok daha ötede, bilimsel yöntemler 
            ve gelişmiş matematiksel modeller üzerine inşa edilmiştir.
            """)
            
            st.markdown("---")
            st.markdown("### 🔬 Metodolojimiz")
            
            st.markdown("#### 1️⃣ Poisson Dağılımı")
            st.markdown("""
            **Futbolda en güvenilir istatistiksel yöntem**  
            - Gol olaylarının olasılık dağılımını matematiksel olarak modeller
            - Dünya çapında profesyonel analistler tarafından kullanılır
            - 0-0, 1-1, 2-1 gibi tüm skor kombinasyonlarının olasılığını hesaplar
            """)
            
            st.markdown("#### 2️⃣ Elo Rating Sistemi")
            st.markdown("""
            **Satranç'tan futbola uyarlanmış güç sıralaması**  
            - Her takımın gerçek gücünü sayısal olarak ifade eder
            - Maç sonuçlarına göre dinamik olarak güncellenir
            - Ev sahibi avantajı, gol farkı gibi faktörleri hesaba katar
            - 2000+ takım için güncel rating veritabanı
            """)
            
            st.markdown("#### 3️⃣ Form ve Momentum Analizi")
            st.markdown("""
            **Son performansın geleceğe etkisi**  
            - Son 5-10 maçın ağırlıklı ortalaması
            - Kazanma serisi, gol trendi gibi psikolojik faktörler
            - Ev sahibi ve deplasman formu ayrı ayrı değerlendirilir
            """)
            
            st.markdown("#### 4️⃣ Çoklu Veri Kaynağı")
            st.markdown("""
            **API-Football'dan canlı veri akışı**  
            - 1000+ lig ve 100,000+ maç verisi
            - Gerçek zamanlı sakatlık, ceza ve kadro bilgileri
            - Hakem istatistikleri ve geçmiş performansları
            - Son 3 sezonun detaylı maç geçmişi
            """)
            
            st.markdown("---")
            st.markdown("### 💡 Sistemimizin Avantajları")
            
            st.markdown("#### ✅ Objektif ve Duygusuz")
            st.markdown("""
            - Taraftarlık, önyargı veya hislerden etkilenmez
            - Sadece veriye dayalı kararlar alır
            - İnsani hataların minimize edilmesi
            """)
            
            st.markdown("#### ✅ Çok Boyutlu Analiz")
            st.markdown("""
            Tek bir faktöre değil, **15+ farklı parametreye** bakılır:
            - Takım gücü (Elo)
            - Son form (momentum)
            - Ev sahibi avantajı
            - Sakatlık ve cezalılar
            - Hakem sertliği
            - Dinlenme süresi
            - H2H geçmişi
            - Lig kalitesi
            - Takım değeri
            - Hücum/savunma endeksleri
            ve daha fazlası...
            """)
            
            st.markdown("#### ✅ Piyasa ile Karşılaştırma")
            st.markdown("""
            - **Değerli Oran Tespiti**: Model tahmini piyasa oranlarından sapınca uyarır
            - Bahis şirketlerinin margin'ini görünür kılar
            - Arbitraj fırsatlarını belirler
            """)
            
            st.markdown("#### ✅ Şeffaf ve Açıklanabilir")
            st.markdown("""
            - Her tahminin arkasındaki **nedenleri** görebilirsiniz
            - Hangi faktörlerin etkili olduğunu anlayabilirsiniz
            - "Analiz Parametreleri" sekmesinde tüm hesaplamaları inceleyebilirsiniz
            """)
            
            st.markdown("---")
            st.markdown("### 📊 Güvenilirlik ve Doğruluk")
            
            st.markdown("""
            **Geçmiş Tahmin Başarısı**  
            - Maç Panosu'ndan geçmiş tarihleri seçerek modelimizin doğruluğunu test edebilirsiniz
            - Her gün için başarı oranını gerçek skorlarla karşılaştırarak görebilirsiniz
            - %60+ doğruluk oranı (profesyonel seviye)
            """)
            
            st.markdown("**AI Güven Puanı**")
            st.markdown("""
            - Her tahmin için 0-100 arası güven skoru
            - Yüksek güven = Model verilere çok güveniyor
            - Düşük güven = Belirsiz maç, dikkatli olun
            """)
            
            st.markdown("---")
            st.markdown("### ⚠️ Önemli Uyarı")
            
            st.warning("""
            **Bu sistem bir karar destek aracıdır, kesin sonuç garantisi vermez.**  
            
            Futbol doğası gereği öngörülemez bir oyundur. En iyi modeller bile %100 doğruluk 
            sağlayamaz. Sistemimiz size:
            - Veriye dayalı objektif tahminler
            - Değerli oran fırsatları
            - Detaylı analiz ve içgörüler
            
            sunar. Ancak nihai kararı siz vermelisiniz. Lütfen sorumlu bahis yapın ve 
            kaybetmeyi göze alamayacağınız miktarlarla işlem yapmayın.
            """)
            
            st.markdown("---")
            st.markdown("### 🤝 Bizimle İletişime Geçin")
            st.markdown("""
            **Sorularınız mı var?**  
            Telegram: [@sivrii1940](https://t.me/sivrii1940)
            
            Premium üyelik, özel analizler veya toplu veri talepleri için bizimle iletişime geçebilirsiniz.
            """)
        
        if not is_admin and user_tier == 'ücretsiz':
            st.sidebar.markdown("---")
            with st.sidebar.container(border=True):
                st.subheader("🚀 Premium'a Yükselt")
                st.markdown("Daha yüksek limitler (1500/gün) ve ayrıcalıklar için Premium'a geçin.")
                telegram_url = "https://t.me/sivrii1940"
                st.link_button("Yükseltme Talebi Gönder (Telegram)", url=telegram_url, use_container_width=True)

        # Bekleyen bildirimleri kontrol et ve göster (view'lardan önce)
        pending_notification = api_utils.get_pending_notification(username)
        if pending_notification:
            col1, col2 = st.columns([10, 1])
            with col1:
                st.warning(pending_notification.get('message', ''), icon="⚠️")
            with col2:
                if st.button("✖", key="close_notification", help="Bildirimi kapat"):
                    api_utils.clear_pending_notification(username)
                    st.rerun()
            st.markdown("---")

        if st.session_state.view == 'home':
            build_home_view(st.session_state.model_params)
        elif st.session_state.view == 'dashboard': 
            build_dashboard_view(st.session_state.model_params)
        elif st.session_state.view == 'manual': 
            build_manual_view(st.session_state.model_params)
        elif st.session_state.view == 'enhanced':
            display_enhanced_match_analysis(API_KEY, BASE_URL)
        elif st.session_state.view == 'codes':
            build_codes_view()
            build_codes_view()

    elif st.session_state["authentication_status"] is False:
        st.error('Kullanıcı adı/şifre hatalı')
    elif st.session_state["authentication_status"] is None:
        st.warning('Lütfen kullanıcı adı ve şifrenizi girin')
        with st.expander('Yeni kullanıcı oluştur'):
            st.markdown('Kendi hesabınızı buradan oluşturabilirsiniz. Aynı IP üzerinden yalnızca bir kullanıcıya API hakkı verilecektir.')
            col1, col2 = st.columns(2)
            with col1:
                new_username = st.text_input('Kullanıcı adı (ör: demo_user)', key='reg_username')
                new_email = st.text_input('E-posta', key='reg_email')
                new_name = st.text_input('Ad Soyad', key='reg_name')
            with col2:
                new_tier = 'ücretsiz'
                new_pw = st.text_input('Parola', type='password', key='reg_pw')
                guessed_ip = api_utils.get_client_ip()
                st.text_input('Algılanan IP (auto)', value=guessed_ip, key='reg_ip_display', disabled=True)
            if st.button('Kayıt Ol'):
                if not new_username or not new_email or not new_name or not new_pw:
                    st.error('Lütfen tüm alanları doldurun.')
                else:
                    try:
                        from password_manager import add_user as pm_add
                        res = pm_add(new_username.strip(), new_email.strip(), new_name.strip(), new_pw, new_tier)
                    except Exception as e:
                        st.error(f"Kullanıcı ekleme sırasında hata: {e}")
                        res = 1
                    ip_input = api_utils.get_client_ip() or ''
                    if res == 0:
                        try:
                            ok, reason = api_utils.register_ip_assignment(new_username.strip(), new_tier, ip_input.strip())
                        except Exception:
                            ok, reason = False, 'IP atama sırasında bir hata oluştu.'
                        try:
                            st.session_state['username'] = new_username.strip()
                            st.session_state['name'] = new_name.strip()
                            st.session_state['authentication_status'] = True
                            st.session_state['tier'] = new_tier
                            st.session_state['bypass_login'] = True
                        except Exception:
                            pass
                        if ok:
                            st.success(f"Kullanıcı {new_username} oluşturuldu ve IP {ip_input or '(algılanamadı)'} ile API hakkı atandı. Oturum açıldı.")
                        else:
                            st.warning(f"Kullanıcı oluşturuldu fakat API hakkı atanmadı: {reason}. Oturum açıldı (API erişimi yok).")
                        try:
                            import time
                            st.query_params["_reg"] = str(time.time())
                            safe_rerun()
                        except Exception:
                            safe_rerun()
                    else:
                        st.error('Kullanıcı eklenemedi.')

if __name__ == "__main__":
    main()