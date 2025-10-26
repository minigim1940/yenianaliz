# -*- coding: utf-8 -*-
# analysis_logic.py

import math
from typing import Dict, Any, List, Optional
from datetime import datetime
import api_utils
import elo_utils

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

def process_player_stats(player_data: Optional[List[Dict]]) -> Optional[str]:
    """Oyuncu istatistik verisini işleyip okunabilir bir metin döner."""
    if not player_data or not player_data[0].get('statistics'):
        return None
    
    try:
        # Genellikle oyuncunun ana lig istatistikleri ilk sırada gelir.
        stats = player_data[0]['statistics'][0]
        games = stats['games'].get('appearences', 0)
        goals = stats['goals'].get('total', 0)
        assists = stats['goals'].get('assists', 0)
        
        if not games:
            return None
            
        return f" (Maç: {games}, Gol: {goals}, Asist: {assists or 0})"
    except (KeyError, IndexError):
        return None

def process_h2h_data(h2h_matches: List[Dict], team_a_id: int) -> Optional[Dict]:
    """H2H maç verisini işler ve özet istatistikler çıkarır."""
    if not h2h_matches:
        return None
    
    wins_a, draws, wins_b = 0, 0, 0
    goals_a, goals_b = 0, 0
    
    recent_matches_display = []

    for match in h2h_matches:
        try:
            home_id = match['teams']['home']['id']
            away_id = match['teams']['away']['id']
            score_home = match['score']['fulltime']['home']
            score_away = match['score']['fulltime']['away']

            if score_home is None or score_away is None:
                continue

            if match['teams']['home']['winner'] is True:
                if home_id == team_a_id: wins_a += 1
                else: wins_b += 1
            elif match['teams']['away']['winner'] is True:
                if away_id == team_a_id: wins_a += 1
                else: wins_b += 1
            else:
                draws += 1
            
            if home_id == team_a_id:
                goals_a += score_home
                goals_b += score_away
            else:
                goals_a += score_away
                goals_b += score_home
            
            match_date = datetime.fromtimestamp(match['fixture']['timestamp']).strftime('%d.%m.%Y')
            recent_matches_display.append({
                "Tarih": match_date,
                "Ev Sahibi": match['teams']['home']['name'],
                "Skor": f"{score_home} - {score_away}",
                "Deplasman": match['teams']['away']['name']
            })
        except (KeyError, TypeError):
            continue
            
    total_matches = len(h2h_matches)
    return {
        "summary": {"total_matches": total_matches, "wins_a": wins_a, "draws": draws, "wins_b": wins_b},
        "goals": {"goals_a": goals_a, "goals_b": goals_b, "avg_goals_a": goals_a / total_matches if total_matches > 0 else 0, "avg_goals_b": goals_b / total_matches if total_matches > 0 else 0},
        "recent_matches": recent_matches_display
    }

def process_referee_data(referee_data: Optional[Dict]) -> Optional[Dict]:
    """API'den gelen hakem verisini işler."""
    if not referee_data or not referee_data.get('fixtures'):
        return None
    try:
        name = referee_data['name']
        total_games = len(referee_data['fixtures'])
        total_yellow, total_red = 0, 0
        
        for fixture in referee_data['fixtures']:
            cards = fixture.get('cards', {})
            total_yellow += cards.get('yellow', 0)
            total_red += cards.get('red', 0)
            
        return { "name": name, "total_games": total_games, "yellow_per_game": total_yellow / total_games if total_games > 0 else 0, "red_per_game": total_red / total_games if total_games > 0 else 0, }
    except (KeyError, TypeError):
        return None

@st.cache_data(ttl=86400)
def get_league_goal_baselines(api_key: str, base_url: str, league_info: Dict, default_avg: float, skip_api_limit: bool = False) -> Dict[str, float]:
    params = {
        'league': league_info['league_id'],
        'season': league_info['season'],
        'status': 'FT',
        'last': 250,
    }
    fixtures, _ = api_utils.make_api_request(api_key, base_url, "fixtures", params, skip_limit=skip_api_limit)
    totals: List[int] = []
    home_goals = 0
    away_goals = 0
    if fixtures:
        for item in fixtures:
            try:
                score = item['score']['fulltime']
                home_score = score.get('home')
                away_score = score.get('away')
                if home_score is None or away_score is None:
                    continue
                home_goals += home_score
                away_goals += away_score
                totals.append(home_score + away_score)
            except (KeyError, TypeError):
                continue

    match_count = len(totals)
    if match_count == 0:
        fallback_home = default_avg * 0.55
        fallback_away = max(0.4, default_avg - fallback_home)
        return {
            'total_avg': default_avg,
            'home_avg': fallback_home,
            'away_avg': fallback_away,
            'total_std': default_avg * 0.35,
            'sample_size': 0,
        }

    total_avg = (home_goals + away_goals) / match_count
    home_avg = home_goals / match_count
    away_avg = away_goals / match_count
    variance = sum((value - total_avg) ** 2 for value in totals) / match_count if match_count else 0.0
    total_std = math.sqrt(variance) if variance > 0 else default_avg * 0.35

    return {
        'total_avg': total_avg,
        'home_avg': home_avg,
        'away_avg': away_avg,
        'total_std': total_std,
        'sample_size': match_count,
    }


def get_dynamic_league_average(api_key: str, base_url: str, league_info: Dict, default_avg: float) -> float:
    baselines = get_league_goal_baselines(api_key, base_url, league_info, default_avg)
    return baselines['total_avg']

@st.cache_data(ttl=86400)
def calculate_general_stats_v2(api_key: str, base_url: str, team_id: int, league_id: int, season: int, skip_api_limit: bool = False) -> Dict:
    """Genel istatistikleri ve takıma özel ev sahibi avantajını hesaplar."""
    stats_data, error = api_utils.get_team_statistics(api_key, base_url, team_id, league_id, season, skip_limit=skip_api_limit)
    if error or not stats_data:
        # Varsayılan değerler döndür - sistem yine de çalışabilsin
        return {
            'home': {
                'Ort. Gol ATILAN': 1.2,
                'Ort. Gol YENEN': 1.2,
                'Istikrar_Puani': 50.0
            },
            'away': {
                'Ort. Gol ATILAN': 1.0,
                'Ort. Gol YENEN': 1.3,
                'Istikrar_Puani': 45.0
            },
            'team_specific_home_adv': 1.12
        }

    def get_stats_and_ppg(data, location_key):
        fixtures = data['fixtures']['played'][location_key]
        if fixtures == 0: return {}, 0.0

        wins = data['fixtures']['wins'][location_key]
        draws = data['fixtures']['draws'][location_key]
        ppg = (wins * 3 + draws) / fixtures if fixtures > 0 else 0.0

        stats = {
            'Ort. Gol ATILAN': float(data['goals']['for']['average'][location_key] or 0),
            'Ort. Gol YENEN': float(data['goals']['against']['average'][location_key] or 0),
            'Istikrar_Puani': round(((wins / fixtures) + 0.5 * (draws / fixtures)) * 100, 1)
        }
        return stats, ppg

    home_stats, home_ppg = get_stats_and_ppg(stats_data, 'home')
    away_stats, away_ppg = get_stats_and_ppg(stats_data, 'away')

    team_specific_home_adv = 1.12  # Daha düşük varsayılan
    if home_ppg > 0 and away_ppg > 0:
        ratio = home_ppg / away_ppg
        # Oranı daha dar bir aralığa sıkıştır
        team_specific_home_adv = max(1.02, min(ratio, 1.22))
    elif home_ppg > 0 and away_ppg == 0:
        # Sadece ev verisi varsa, makul bir varsayım
        team_specific_home_adv = 1.10
    elif away_ppg > 0 and home_ppg == 0:
        # Sadece deplasman verisi varsa, düşük avantaj
        team_specific_home_adv = 1.05

    return {
        'home': home_stats if home_stats else {'Ort. Gol ATILAN': 1.2, 'Ort. Gol YENEN': 1.2, 'Istikrar_Puani': 50.0},
        'away': away_stats if away_stats else {'Ort. Gol ATILAN': 1.0, 'Ort. Gol YENEN': 1.3, 'Istikrar_Puani': 45.0},
        'team_specific_home_adv': team_specific_home_adv
    }

def calculate_weighted_stats(matches: List[Dict]) -> Dict:
    """
    Son maçlardan ağırlıklı istatistikler hesaplar (gol + korner + kart).
    Yeni maçlara daha fazla ağırlık verir.
    """
    home_stats = {
        'goals_for': [], 'goals_against': [], 
        'corners_for': [], 'corners_against': [],
        'yellow_cards': [], 'red_cards': []
    }
    away_stats = {
        'goals_for': [], 'goals_against': [], 
        'corners_for': [], 'corners_against': [],
        'yellow_cards': [], 'red_cards': []
    }
    
    for match in matches:
        if match['location'] == 'home':
            home_stats['goals_for'].append(match['goals_for'])
            home_stats['goals_against'].append(match['goals_against'])
            # Korner verileri (varsa)
            if match.get('corners_for') is not None:
                home_stats['corners_for'].append(match['corners_for'])
            if match.get('corners_against') is not None:
                home_stats['corners_against'].append(match['corners_against'])
            # Kart verileri (varsa)
            if match.get('yellow_cards') is not None:
                home_stats['yellow_cards'].append(match['yellow_cards'])
            if match.get('red_cards') is not None:
                home_stats['red_cards'].append(match['red_cards'])
        else:
            away_stats['goals_for'].append(match['goals_for'])
            away_stats['goals_against'].append(match['goals_against'])
            # Korner verileri (varsa)
            if match.get('corners_for') is not None:
                away_stats['corners_for'].append(match['corners_for'])
            if match.get('corners_against') is not None:
                away_stats['corners_against'].append(match['corners_against'])
            # Kart verileri (varsa)
            if match.get('yellow_cards') is not None:
                away_stats['yellow_cards'].append(match['yellow_cards'])
            if match.get('red_cards') is not None:
                away_stats['red_cards'].append(match['red_cards'])

    def get_weighted_average(values: List[int]) -> float:
        """Ağırlıklı ortalama - yeni maçlara daha fazla ağırlık"""
        if not values: 
            return 0.0
        weighted_sum, total_weight = 0, 0
        for i, value in enumerate(values):
            weight = i + 1  # En yeni maç en yüksek ağırlık
            weighted_sum += value * weight
            total_weight += weight
        return weighted_sum / total_weight if total_weight > 0 else 0.0

    return {
        'home': {
            'w_avg_goals_for': get_weighted_average(home_stats['goals_for']),
            'w_avg_goals_against': get_weighted_average(home_stats['goals_against']),
            'w_avg_corners_for': get_weighted_average(home_stats['corners_for']),
            'w_avg_corners_against': get_weighted_average(home_stats['corners_against']),
            'w_avg_yellow_cards': get_weighted_average(home_stats['yellow_cards']),
            'w_avg_red_cards': get_weighted_average(home_stats['red_cards'])
        },
        'away': {
            'w_avg_goals_for': get_weighted_average(away_stats['goals_for']),
            'w_avg_goals_against': get_weighted_average(away_stats['goals_against']),
            'w_avg_corners_for': get_weighted_average(away_stats['corners_for']),
            'w_avg_corners_against': get_weighted_average(away_stats['corners_against']),
            'w_avg_yellow_cards': get_weighted_average(away_stats['yellow_cards']),
            'w_avg_red_cards': get_weighted_average(away_stats['red_cards'])
        }
    }

def calculate_form_factor(matches: Optional[List[Dict]], preferred_location: Optional[str] = None) -> float:
    """Son maç sonuçlarına göre form katsayısını hesaplar."""
    if not matches:
        return 1.0

    filtered = [m for m in matches if preferred_location is None or m.get('location') == preferred_location]
    if not filtered:
        filtered = matches

    weighted_points, total_weight = 0.0, 0
    for idx, match in enumerate(filtered, start=1):
        gf, ga = match.get('goals_for'), match.get('goals_against')
        if gf is None or ga is None:
            continue
        points = 3 if gf > ga else 1 if gf == ga else 0
        weight = idx  # daha yeni maçlara daha yüksek ağırlık
        weighted_points += points * weight
        total_weight += weight

    if total_weight == 0:
        return 1.0

    avg_points = weighted_points / total_weight
    baseline = 1.5  # nötr seviye ~1.5 puan/maç
    factor = 1 + ((avg_points - baseline) / 6)
    return max(0.85, min(1.15, round(factor, 3)))

def get_form_string(matches: Optional[List[Dict]], limit: int = 5) -> str:
    """
    Son N maçın form string'ini döner (örn: 'WDLWW')
    W = Win (Galibiyet), D = Draw (Beraberlik), L = Loss (Mağlubiyet)
    """
    if not matches:
        return ""
    
    form_chars = []
    for match in matches[:limit]:  # Son N maç
        gf = match.get('goals_for')
        ga = match.get('goals_against')
        
        if gf is None or ga is None:
            continue
        
        if gf > ga:
            form_chars.append('W')  # Win
        elif gf == ga:
            form_chars.append('D')  # Draw
        else:
            form_chars.append('L')  # Loss
    
    return ''.join(form_chars)

def process_odds_data(odds_response: List[Dict]) -> Optional[Dict]:
    if not odds_response or not odds_response[0].get('bookmakers'): return None
    home_odds, draw_odds, away_odds = [], [], []
    bookmakers = odds_response[0]['bookmakers']
    for bookmaker in bookmakers:
        try:
            match_winner_bet = next(bet for bet in bookmaker['bets'] if bet['name'] == 'Match Winner')
            values = match_winner_bet['values']
            h = float(next(val['odd'] for val in values if val['value'] == 'Home'))
            d = float(next(val['odd'] for val in values if val['value'] == 'Draw'))
            a = float(next(val['odd'] for val in values if val['value'] == 'Away'))
            home_odds.append(h); draw_odds.append(d); away_odds.append(a)
        except (StopIteration, KeyError, IndexError, ValueError): continue
    if not all([home_odds, draw_odds, away_odds]): return None
    avg_home_odd, avg_draw_odd, avg_away_odd = sum(home_odds) / len(home_odds), sum(draw_odds) / len(draw_odds), sum(away_odds) / len(away_odds)
    return {'home': {'odd': avg_home_odd, 'prob': (1 / avg_home_odd) * 100}, 'draw': {'odd': avg_draw_odd, 'prob': (1 / avg_draw_odd) * 100}, 'away': {'odd': avg_away_odd, 'prob': (1 / avg_away_odd) * 100}}

def process_detailed_odds(categorized_odds: Optional[Dict]) -> Dict[str, Any]:
    """
    Detaylı bahis oranlarını işler ve model ile karşılaştırılabilir formata getirir.
    """
    if not categorized_odds:
        return {}
    
    processed = {
        'over_under_2.5': None,
        'btts': None,
        'handicap': {},
        'first_half_winner': None,
        'first_half_over_1.5': None,
        'corners_9.5': None,
        'corners_10.5': None,
        'cards_over_3.5': None,
    }
    
    # 2.5 Üst/Alt işleme
    if categorized_odds.get('over_under'):
        for bet_data in categorized_odds['over_under']:
            bet_name = bet_data.get('bet_name', '').lower()
            if '2.5' in bet_name:
                values = bet_data.get('values', [])
                for val in values:
                    label = val.get('value', '').lower()
                    odd = float(val.get('odd', 0))
                    if 'over' in label and odd > 0:
                        if not processed['over_under_2.5']:
                            processed['over_under_2.5'] = {}
                        processed['over_under_2.5']['over'] = {
                            'odd': odd,
                            'prob': round((1/odd) * 100, 1)
                        }
                    elif 'under' in label and odd > 0:
                        if not processed['over_under_2.5']:
                            processed['over_under_2.5'] = {}
                        processed['over_under_2.5']['under'] = {
                            'odd': odd,
                            'prob': round((1/odd) * 100, 1)
                        }
    
    # BTTS işleme
    if categorized_odds.get('btts'):
        for bet_data in categorized_odds['btts']:
            values = bet_data.get('values', [])
            for val in values:
                label = val.get('value', '').lower()
                odd = float(val.get('odd', 0))
                if 'yes' in label and odd > 0:
                    if not processed['btts']:
                        processed['btts'] = {}
                    processed['btts']['yes'] = {
                        'odd': odd,
                        'prob': round((1/odd) * 100, 1)
                    }
                elif 'no' in label and odd > 0:
                    if not processed['btts']:
                        processed['btts'] = {}
                    processed['btts']['no'] = {
                        'odd': odd,
                        'prob': round((1/odd) * 100, 1)
                    }
    
    # Handikap işleme (Ev sahibi -0.5, -1.5, -2.5)
    if categorized_odds.get('handicap'):
        for bet_data in categorized_odds['handicap']:
            bet_name = bet_data.get('bet_name', '').lower()
            values = bet_data.get('values', [])
            for val in values:
                label = val.get('value', '')
                odd = float(val.get('odd', 0))
                if odd > 0:
                    # Handikap değerini parse et (örn: "Home -0.5")
                    if '-0.5' in label or '-0:1' in label:
                        processed['handicap']['home_minus_0.5'] = {
                            'odd': odd,
                            'prob': round((1/odd) * 100, 1)
                        }
                    elif '-1.5' in label or '-1:2' in label:
                        processed['handicap']['home_minus_1.5'] = {
                            'odd': odd,
                            'prob': round((1/odd) * 100, 1)
                        }
    
    # İlk yarı winner işleme
    if categorized_odds.get('first_half'):
        for bet_data in categorized_odds['first_half']:
            bet_name = bet_data.get('bet_name', '').lower()
            if 'winner' in bet_name or '1x2' in bet_name:
                values = bet_data.get('values', [])
                for val in values:
                    label = val.get('value', '').lower()
                    odd = float(val.get('odd', 0))
                    if 'home' in label and odd > 0:
                        if not processed['first_half_winner']:
                            processed['first_half_winner'] = {}
                        processed['first_half_winner']['home'] = {
                            'odd': odd,
                            'prob': round((1/odd) * 100, 1)
                        }
                    elif 'draw' in label and odd > 0:
                        if not processed['first_half_winner']:
                            processed['first_half_winner'] = {}
                        processed['first_half_winner']['draw'] = {
                            'odd': odd,
                            'prob': round((1/odd) * 100, 1)
                        }
                    elif 'away' in label and odd > 0:
                        if not processed['first_half_winner']:
                            processed['first_half_winner'] = {}
                        processed['first_half_winner']['away'] = {
                            'odd': odd,
                            'prob': round((1/odd) * 100, 1)
                        }
    
    # Korner oranları
    if categorized_odds.get('corners'):
        for bet_data in categorized_odds['corners']:
            bet_name = bet_data.get('bet_name', '').lower()
            values = bet_data.get('values', [])
            if '9.5' in bet_name or '10.5' in bet_name:
                for val in values:
                    label = val.get('value', '').lower()
                    odd = float(val.get('odd', 0))
                    if odd > 0:
                        key = 'corners_9.5' if '9.5' in bet_name else 'corners_10.5'
                        if not processed[key]:
                            processed[key] = {}
                        if 'over' in label:
                            processed[key]['over'] = {
                                'odd': odd,
                                'prob': round((1/odd) * 100, 1)
                            }
                        elif 'under' in label:
                            processed[key]['under'] = {
                                'odd': odd,
                                'prob': round((1/odd) * 100, 1)
                            }
    
    # Kart oranları
    if categorized_odds.get('cards'):
        for bet_data in categorized_odds['cards']:
            bet_name = bet_data.get('bet_name', '').lower()
            if '3.5' in bet_name or '4.5' in bet_name:
                values = bet_data.get('values', [])
                for val in values:
                    label = val.get('value', '').lower()
                    odd = float(val.get('odd', 0))
                    if odd > 0 and 'over' in label:
                        processed['cards_over_3.5'] = {
                            'odd': odd,
                            'prob': round((1/odd) * 100, 1)
                        }
                        break
    
    return processed

def calculate_odds_based_adjustment(odds_data: Optional[Dict], model_win_a: float, model_draw: float, model_win_b: float) -> Dict[str, float]:
    """Bahis oranlarını model tahminleriyle birleştir (70% model + 30% odds)"""
    if not odds_data:
        return {'win_a': model_win_a, 'draw': model_draw, 'win_b': model_win_b}
    
    # Model olasılıkları zaten yüzde formatında (0-100), 0-1 aralığına çevir
    model_win_a_decimal = model_win_a / 100.0
    model_draw_decimal = model_draw / 100.0
    model_win_b_decimal = model_win_b / 100.0
    
    # Bahis oranlarından olasılıkları al (zaten 0-100 formatında, 0-1'e çevir)
    odds_win_a = odds_data['home']['prob'] / 100.0
    odds_draw = odds_data['draw']['prob'] / 100.0
    odds_win_b = odds_data['away']['prob'] / 100.0
    
    # Ağırlıklı ortalama: %70 model + %30 piyasa
    MODEL_WEIGHT = 0.70
    ODDS_WEIGHT = 0.30
    
    adjusted_win_a = (model_win_a_decimal * MODEL_WEIGHT) + (odds_win_a * ODDS_WEIGHT)
    adjusted_draw = (model_draw_decimal * MODEL_WEIGHT) + (odds_draw * ODDS_WEIGHT)
    adjusted_win_b = (model_win_b_decimal * MODEL_WEIGHT) + (odds_win_b * ODDS_WEIGHT)
    
    # Normalize et (toplam 1.0 olsun)
    total = adjusted_win_a + adjusted_draw + adjusted_win_b
    if total > 0:
        adjusted_win_a /= total
        adjusted_draw /= total
        adjusted_win_b /= total
    
    # Yüzde formatına geri çevir (0-100)
    return {
        'win_a': round(adjusted_win_a * 100, 1), 
        'draw': round(adjusted_draw * 100, 1), 
        'win_b': round(adjusted_win_b * 100, 1)
    }

def calculate_h2h_factor(h2h_data: Optional[Dict], team_a_id: int) -> float:
    """Son karşılaşmalarda dominant olan takıma bonus faktör"""
    if not h2h_data or not h2h_data.get('summary'):
        return 1.0
    
    summary = h2h_data['summary']
    total = summary.get('total_matches', 0)
    
    if total < 3:  # En az 3 maç gerekli
        return 1.0
    
    wins_a = summary.get('wins_a', 0)
    wins_b = summary.get('wins_b', 0)
    
    # Galibiyetlerin %80'inden fazlası bir takıma aitse
    if wins_a / total >= 0.8:
        return 1.12  # Team A dominance (arttırıldı 1.08 → 1.12)
    elif wins_b / total >= 0.8:
        return 0.88  # Team B dominance (arttırıldı 0.92 → 0.88)
    elif wins_a / total >= 0.6:
        return 1.06  # Team A slight advantage (arttırıldı 1.04 → 1.06)
    elif wins_b / total >= 0.6:
        return 0.94  # Team B slight advantage (arttırıldı 0.96 → 0.94)
    
    return 1.0

def calculate_referee_factor(referee_stats: Optional[Dict]) -> float:
    """Hakem sertliğine göre gol beklentisi ayarlaması"""
    if not referee_stats:
        return 1.0
    
    yellow_per_game = referee_stats.get('yellow_per_game', 3.5)
    red_per_game = referee_stats.get('red_per_game', 0.1)
    
    # Sert hakem = daha az akıcı oyun = daha az gol
    if yellow_per_game > 5.0 or red_per_game > 0.3:
        return 0.92  # Çok sert hakem
    elif yellow_per_game > 4.0:
        return 0.96  # Sert hakem
    elif yellow_per_game < 2.5 and red_per_game < 0.05:
        return 1.04  # Yumuşak hakem, akıcı oyun
    
    return 1.0

def calculate_corner_probabilities(home_corners_avg: float, away_corners_avg: float, league_avg_corners: float = 10.5) -> Dict[str, float]:
    """
    Korner tahminlerini hesaplar - GELİŞTİRİLMİŞ GERÇEKÇI MODEL.
    
    Args:
        home_corners_avg: Ev sahibi takımın ortalama KAZANDIĞI korner sayısı
        away_corners_avg: Deplasman takımının ortalama KAZANDIĞI korner sayısı
        league_avg_corners: Lig ortalaması toplam korner sayısı (varsayılan 10.5)
    
    Gerçekçi faktörler:
    - Ev sahibi genelde %55-60 korner kazanır
    - Güçlü takımlar daha fazla korner kazanır (hücum baskısı)
    - Zayıf takımlar daha fazla korner yer (savunmaya çekilir)
    """
    # Varsayılan değerler
    if home_corners_avg == 0:
        home_corners_avg = league_avg_corners * 0.55
    if away_corners_avg == 0:
        away_corners_avg = league_avg_corners * 0.45
    
    # Beklenen toplam korner = her iki takımın kazandığı kornerler toplamı
    expected_total = home_corners_avg + away_corners_avg
    
    # Lig ortalaması ile normalize et (aşırı sapmaları önle)
    # Gerçekçi aralık: 6-15 korner
    if expected_total < 6.0:
        expected_total = 6.5  # Minimum gerçekçi değer
    elif expected_total > 15.0:
        expected_total = 14.0  # Maximum gerçekçi değer
    
    # Gerçekçi standart sapma
    std_dev = expected_total * 0.30  # %30 standart sapma
    
    # Normal dağılıma yakın Poisson kullan (kornerlerde daha gerçekçi)
    over_8_5 = 0.0
    over_9_5 = 0.0
    over_10_5 = 0.0
    over_11_5 = 0.0
    
    for total_corners in range(0, 30):  # 0-29 korner aralığı (geniş aralık)
        # Poisson yerine Negative Binomial kullan (daha gerçekçi varyans)
        prob = poisson_pmf(expected_total, total_corners)
        
        if total_corners > 8:
            over_8_5 += prob
        if total_corners > 9:
            over_9_5 += prob
        if total_corners > 10:
            over_10_5 += prob
        if total_corners > 11:
            over_11_5 += prob
    
    # Gerçekçi sınırlar: Çok ekstrem değerleri yumuşat
    def normalize_prob(prob):
        """Olasılığı gerçekçi aralığa çek (%20-%80)"""
        if prob < 0.15:
            return prob * 1.3  # Çok düşük olasılıkları biraz artır
        elif prob > 0.85:
            return 0.75 + (prob - 0.85) * 0.5  # Çok yüksek olasılıkları düşür
        return prob
    
    over_8_5 = normalize_prob(over_8_5)
    over_9_5 = normalize_prob(over_9_5)
    over_10_5 = normalize_prob(over_10_5)
    over_11_5 = normalize_prob(over_11_5)
    
    return {
        'expected_corners': round(expected_total, 1),
        'over_8.5': round(over_8_5 * 100, 1),
        'under_8.5': round((1 - over_8_5) * 100, 1),
        'over_9.5': round(over_9_5 * 100, 1),
        'under_9.5': round((1 - over_9_5) * 100, 1),
        'over_10.5': round(over_10_5 * 100, 1),
        'under_10.5': round((1 - over_10_5) * 100, 1),
        'over_11.5': round(over_11_5 * 100, 1),
        'under_11.5': round((1 - over_11_5) * 100, 1),
    }

def calculate_card_probabilities(referee_yellow_avg: float, referee_red_avg: float, team_a_cards_avg: float = 0, team_b_cards_avg: float = 0) -> Dict[str, float]:
    """
    Kart tahminlerini hesaplar - GELİŞTİRİLMİŞ GERÇEKÇI MODEL.
    
    Args:
        referee_yellow_avg: Hakemin maç başına ortalama sarı kart sayısı
        referee_red_avg: Hakemin maç başına ortalama kırmızı kart sayısı
        team_a_cards_avg: Ev sahibinin ortalama kart sayısı (opsiyonel)
        team_b_cards_avg: Deplasmanın ortalama kart sayısı (opsiyonel)
    
    Gerçekçi faktörler:
    - Hakem %70 etkili, takımlar %30 etkili
    - Derbi maçlarda +%25 daha fazla kart
    - Sıkı maçlarda (yakın skor) daha fazla kart
    - Ortalama maçta 3-5 sarı kart normal
    - Kırmızı kart ortalama %12-18 olasılık (5-6 maçta 1)
    """
    # Gerçekçi varsayılan değerler (futbol istatistiklerine göre)
    LEAGUE_AVG_YELLOW = 4.2  # Lig ortalaması sarı kart
    LEAGUE_AVG_RED = 0.15    # Lig ortalaması kırmızı kart
    
    # Hakem faktörü (en önemli)
    if referee_yellow_avg > 0:
        referee_factor = 0.70  # Hakem %70 etkili
        team_factor = 0.30     # Takımlar %30 etkili
        
        # Takım ortalamaları varsa dahil et
        if team_a_cards_avg > 0 and team_b_cards_avg > 0:
            team_avg = (team_a_cards_avg + team_b_cards_avg) / 2
            expected_yellow = (referee_yellow_avg * referee_factor) + (team_avg * team_factor)
        else:
            expected_yellow = referee_yellow_avg
    else:
        # Hakem verisi yoksa takım ve lig ortalamasını kullan
        if team_a_cards_avg > 0 and team_b_cards_avg > 0:
            expected_yellow = (team_a_cards_avg + team_b_cards_avg) / 2
        else:
            expected_yellow = LEAGUE_AVG_YELLOW
    
    # Gerçekçi sınırlar (aşırı sapmaları önle)
    if expected_yellow < 2.5:
        expected_yellow = 3.0  # Minimum 3 sarı kart beklentisi
    elif expected_yellow > 6.5:
        expected_yellow = 6.0  # Maksimum 6 sarı kart beklentisi
    
    # Kırmızı kart beklentisi
    if referee_red_avg > 0:
        expected_red = referee_red_avg
        # Çok sert hakem varsa sınırla
        if expected_red > 0.35:
            expected_red = 0.30  # Maksimum %30 kırmızı kart olasılığı
    else:
        expected_red = LEAGUE_AVG_RED
    
    # Sarı kart tahminleri (Poisson dağılımı)
    over_2_5_yellow = 0.0
    over_3_5_yellow = 0.0
    over_4_5_yellow = 0.0
    over_5_5_yellow = 0.0
    
    for yellow_count in range(0, 15):
        prob = poisson_pmf(expected_yellow, yellow_count)
        if yellow_count > 2:
            over_2_5_yellow += prob
        if yellow_count > 3:
            over_3_5_yellow += prob
        if yellow_count > 4:
            over_4_5_yellow += prob
        if yellow_count > 5:
            over_5_5_yellow += prob
    
    # Kırmızı kart olasılığı (en az 1 kırmızı kart)
    # P(X >= 1) = 1 - P(X = 0)
    red_card_yes = 1 - poisson_pmf(expected_red, 0)
    
    # Gerçekçi sınırlar: Kırmızı kart olasılığını normalize et
    # Genelde %10-25 arasında olmalı
    if red_card_yes < 0.08:
        red_card_yes = 0.12  # Minimum %12
    elif red_card_yes > 0.30:
        red_card_yes = 0.25  # Maksimum %25
    
    # Sarı kart olasılıklarını yumuşat (çok ekstrem değerleri önle)
    def normalize_card_prob(prob, min_val=0.15, max_val=0.85):
        """Kart olasılığını gerçekçi aralığa çek"""
        if prob < min_val:
            return min_val + (prob * 0.5)
        elif prob > max_val:
            return max_val - ((1 - prob) * 0.5)
        return prob
    
    over_3_5_yellow = normalize_card_prob(over_3_5_yellow, 0.20, 0.80)
    over_4_5_yellow = normalize_card_prob(over_4_5_yellow, 0.15, 0.75)
    over_5_5_yellow = normalize_card_prob(over_5_5_yellow, 0.10, 0.65)
    
    return {
        'expected_yellow_cards': round(expected_yellow, 1),
        'expected_red_cards': round(expected_red, 2),
        'over_2.5_yellow': round(over_2_5_yellow * 100, 1),
        'under_2.5_yellow': round((1 - over_2_5_yellow) * 100, 1),
        'over_3.5_yellow': round(over_3_5_yellow * 100, 1),
        'under_3.5_yellow': round((1 - over_3_5_yellow) * 100, 1),
        'over_4.5_yellow': round(over_4_5_yellow * 100, 1),
        'under_4.5_yellow': round((1 - over_4_5_yellow) * 100, 1),
        'over_5.5_yellow': round(over_5_5_yellow * 100, 1),
        'under_5.5_yellow': round((1 - over_5_5_yellow) * 100, 1),
        'red_card_yes': round(red_card_yes * 100, 1),
        'red_card_no': round((1 - red_card_yes) * 100, 1),
    }

def calculate_first_half_probabilities(s_a: float, s_b: float) -> Dict[str, float]:
    """
    İlk yarı 1X2 tahminlerini hesaplar.
    İlk yarıda genelde maç genelinin %40-45'i kadar gol atılır.
    """
    # İlk yarı lambdaları
    s_a_ht = s_a * 0.42
    s_b_ht = s_b * 0.42
    
    accum_ht = {'win_a': 0.0, 'draw': 0.0}
    
    for i in range(6):  # İlk yarı 0-5 gol aralığı
        for j in range(6):
            prob = poisson_pmf(s_a_ht, i) * poisson_pmf(s_b_ht, j)
            if i > j:
                accum_ht['win_a'] += prob
            elif i == j:
                accum_ht['draw'] += prob
    
    win_b_ht = max(0.0, 1.0 - accum_ht['win_a'] - accum_ht['draw'])
    
    return {
        'ilk_yari_ev_kazanir': round(accum_ht['win_a'] * 100, 1),
        'ilk_yari_beraberlik': round(accum_ht['draw'] * 100, 1),
        'ilk_yari_dep_kazanir': round(win_b_ht * 100, 1),
    }

def calculate_rest_days_factor(last_matches: Optional[List[Dict]]) -> float:
    """Son maçtan bu yana geçen günlere göre dinlenme faktörü"""
    if not last_matches or len(last_matches) == 0:
        return 1.0
    
    try:
        # En son maç tarihini al
        last_match = last_matches[0]  # En son maç (listede ilk sırada)
        last_date_str = last_match.get('date')
        
        if not last_date_str:
            return 1.0
        
        from datetime import datetime, date
        last_date = datetime.strptime(last_date_str, '%Y-%m-%d').date()
        today = date.today()
        rest_days = (today - last_date).days
        
        # Az dinlenme = yorgunluk
        if rest_days < 3:
            return 0.95  # Yorgun takım
        elif rest_days < 4:
            return 0.98
        elif rest_days > 10:
            return 0.97  # Çok uzun ara, ritim kaybı
        
        return 1.0  # Optimal dinlenme
    except Exception:
        return 1.0

def calculate_momentum_factor(last_matches: Optional[List[Dict]], location: str = None) -> float:
    """Son 5 maçtaki gol farkı ve trend analizi"""
    if not last_matches or len(last_matches) < 3:
        return 1.0
    
    recent_5 = last_matches[:5] if len(last_matches) >= 5 else last_matches
    goal_diff_total = 0
    wins_count = 0
    
    for match in recent_5:
        gf = match.get('goals_for', 0)
        ga = match.get('goals_against', 0)
        
        if gf is None or ga is None:
            continue
        
        goal_diff_total += (gf - ga)
        if gf > ga:
            wins_count += 1
    
    # Güçlü momentum: +10 veya daha fazla gol farkı
    if goal_diff_total >= 10:
        return 1.08
    elif goal_diff_total >= 6:
        return 1.04
    elif goal_diff_total <= -10:
        return 0.92
    elif goal_diff_total <= -6:
        return 0.96
    
    return 1.0

def calculate_league_quality_multiplier(league_id: int) -> float:
    """Lig kalitesine göre çarpan (önemli ligler daha öngörülebilir)"""
    LEAGUE_QUALITY = {
        39: 1.00,   # England - Premier League
        140: 1.00,  # Spain - La Liga
        78: 1.00,   # Germany - Bundesliga
        135: 1.00,  # Italy - Serie A
        61: 1.00,   # France - Ligue 1
        2: 0.95,    # UEFA Champions League
        3: 0.95,    # UEFA Europa League
        203: 0.85,  # Turkey - Süper Lig
        88: 0.90,   # Netherlands - Eredivisie
        94: 0.90,   # Portugal - Primeira Liga
        128: 0.80,  # Argentina - Primera División
        71: 0.80,   # Brazil - Serie A
    }
    
    return LEAGUE_QUALITY.get(league_id, 0.85)  # Varsayılan 0.85

def calculate_team_value_factor(elo_rating_a: int, elo_rating_b: int, league_id: int) -> Dict[str, float]:
    """
    Takım değeri faktörü - Elo rating ve lig kalitesine göre tahmini piyasa değeri farkı
    Büyük değer farkları hücum/savunma güçlerini etkiler
    
    Returns:
        Dict: {'value_mult_a': float, 'value_mult_b': float}
    """
    # Elo farkından değer farkını tahmin et
    elo_diff = elo_rating_a - elo_rating_b
    
    # Lig kalitesi çarpanı - üst ligde Elo farkı daha anlamlı
    league_quality = calculate_league_quality_multiplier(league_id)
    adjusted_diff = elo_diff * league_quality
    
    # Değer çarpanı hesapla (büyük fark = daha fazla etki)
    if adjusted_diff > 200:  # Çok büyük fark (örn: Man City vs küçük takım)
        value_mult_a = 1.08
        value_mult_b = 0.93
    elif adjusted_diff > 120:
        value_mult_a = 1.05
        value_mult_b = 0.95
    elif adjusted_diff > 60:
        value_mult_a = 1.03
        value_mult_b = 0.97
    elif adjusted_diff < -200:
        value_mult_a = 0.93
        value_mult_b = 1.08
    elif adjusted_diff < -120:
        value_mult_a = 0.95
        value_mult_b = 1.05
    elif adjusted_diff < -60:
        value_mult_a = 0.97
        value_mult_b = 1.03
    else:  # Dengeli değer
        value_mult_a = 1.0
        value_mult_b = 1.0
    
    return {
        'value_mult_a': value_mult_a,
        'value_mult_b': value_mult_b,
        'value_category': _get_value_category(adjusted_diff)
    }

def _get_value_category(diff: float) -> str:
    """Değer farkı kategorisi"""
    if diff > 200: return "Ev Sahibi Çok Üstün"
    elif diff > 120: return "Ev Sahibi Üstün"
    elif diff > 60: return "Ev Sahibi Hafif Üstün"
    elif diff < -200: return "Deplasman Çok Üstün"
    elif diff < -120: return "Deplasman Üstün"
    elif diff < -60: return "Deplasman Hafif Üstün"
    else: return "Dengeli"

def calculate_xg_adjustment(stats: Dict, location: str) -> float:
    """xG verisi varsa kullan (gerçek goller yanıltıcı olabilir)"""
    # API'den xG verisi gelirse burada işle
    # Şu an için placeholder
    return 1.0

def calculate_injury_factor(injuries: Optional[List[Dict]], team_id: int) -> float:
    """
    Sakatlık ve ceza durumuna göre güç kaybı hesaplar
    
    Args:
        injuries: Sakatlık listesi
        team_id: Takım ID
    
    Returns:
        0.85-1.00 arası çarpan (çok sakatlık varsa düşük)
    """
    if not injuries:
        return 1.0  # Sakatlık yok, etki yok
    
    injury_count = len(injuries)
    
    # Sakatlık sayısına göre ceza
    if injury_count >= 5:
        return 0.85  # Çok ciddi sakatlık krizi
    elif injury_count >= 3:
        return 0.90  # Orta düzey sakatlık
    elif injury_count >= 1:
        return 0.95  # Az sakatlık
    
    return 1.0

def poisson_pmf(l, k):
    if l <= 0 or k < 0: return 0.0
    try: return (l**k) * math.exp(-l) / math.factorial(k)
    except (ValueError, OverflowError): return 0.0

def calculate_match_probabilities(s_a: float, s_b: float) -> Dict[str, float]:
    limits = range(11)
    accum = {'over': 0.0, 'btts': 0.0, 'win_a': 0.0, 'draw': 0.0, 'over_ht': 0.0, 'handicap_home_minus_0_5': 0.0, 'handicap_home_minus_1_5': 0.0, 'handicap_home_minus_2_5': 0.0}
    
    # İlk yarı lambdaları (genelde 40-45% civarı)
    s_a_ht = s_a * 0.42
    s_b_ht = s_b * 0.42
    
    for i in limits:
        for j in limits:
            prob = poisson_pmf(s_a, i) * poisson_pmf(s_b, j)
            accum['over'] += prob if (i + j) > 2 else 0.0
            accum['btts'] += prob if (i > 0 and j > 0) else 0.0
            if i > j:
                accum['win_a'] += prob
            elif i == j:
                accum['draw'] += prob
            
            # Handikap hesaplamaları (ev sahibi -0.5, -1.5, -2.5)
            if (i - j) > 0.5:  # Ev sahibi en az 1 farkla kazanırsa
                accum['handicap_home_minus_0_5'] += prob
            if (i - j) > 1.5:  # Ev sahibi en az 2 farkla kazanırsa
                accum['handicap_home_minus_1_5'] += prob
            if (i - j) > 2.5:  # Ev sahibi en az 3 farkla kazanırsa
                accum['handicap_home_minus_2_5'] += prob
    
    # İlk yarı 1.5 üst hesaplama
    for i in range(6):  # İlk yarı için 0-5 gol aralığı
        for j in range(6):
            prob_ht = poisson_pmf(s_a_ht, i) * poisson_pmf(s_b_ht, j)
            accum['over_ht'] += prob_ht if (i + j) > 1 else 0.0

    win_b = max(0.0, 1.0 - accum['win_a'] - accum['draw'])
    prob_dict = {
        'ust_2.5': round(accum['over'] * 100, 1),
        'alt_2.5': round((1 - accum['over']) * 100, 1),
        'kg_var': round(accum['btts'] * 100, 1),
        'kg_yok': round((1 - accum['btts']) * 100, 1),
        'win_a': round(accum['win_a'] * 100, 1),
        'win_b': round(win_b * 100, 1),
        'draw': round(accum['draw'] * 100, 1),
        # Yeni tahminler
        'ilk_yari_1.5_ust': round(accum['over_ht'] * 100, 1),
        'ilk_yari_1.5_alt': round((1 - accum['over_ht']) * 100, 1),
        'handicap_ev_minus_0.5': round(accum['handicap_home_minus_0_5'] * 100, 1),
        'handicap_ev_minus_1.5': round(accum['handicap_home_minus_1_5'] * 100, 1),
        'handicap_ev_minus_2.5': round(accum['handicap_home_minus_2_5'] * 100, 1),
        'handicap_dep_plus_0.5': round((1 - accum['handicap_home_minus_0_5']) * 100, 1),
        'handicap_dep_plus_1.5': round((1 - accum['handicap_home_minus_1_5']) * 100, 1),
        'handicap_dep_plus_2.5': round((1 - accum['handicap_home_minus_2_5']) * 100, 1),
    }
    return prob_dict

def get_key_players(player_stats: List[Dict[str, Any]]) -> Dict[str, List[int]]:
    if not player_stats: return {'top_scorer_ids': [], 'most_minutes_ids': []}
    max_goals, top_scorers = 0, []
    for p in player_stats:
        goals = p['statistics'][0]['goals']['total'] or 0
        if goals > max_goals:
            max_goals, top_scorers = goals, [p['player']['id']]
        elif goals == max_goals and max_goals > 0:
            top_scorers.append(p['player']['id'])
    player_stats.sort(key=lambda p: p['statistics'][0]['games']['minutes'] or 0, reverse=True)
    most_minutes = [p['player']['id'] for p in player_stats[:4]]
    return {'top_scorer_ids': top_scorers, 'most_minutes_ids': most_minutes}

def generate_prediction_reasons(analysis_data: Dict, team_names: Dict) -> List[str]:
    reasons: List[str] = []
    probs = analysis_data['probs']
    params = analysis_data['params']
    stats = analysis_data['stats']
    diff = analysis_data['diff']
    max_prob_key = max(probs, key=lambda k: probs[k] if 'win' in k or 'draw' in k else -1)
    winner_name = team_names['a'] if max_prob_key == 'win_a' else team_names['b'] if max_prob_key == 'win_b' else ""

    # 🆕 Bahis oranları kullanıldı mı?
    if params.get('odds_used'):
        reasons.append("💡 Model tahmini piyasa oranlarıyla (%30) birleştirildi.")

    if diff > 20 and winner_name:
        reasons.append(f"Model, **{winner_name}** takımını net favori olarak görüyor (olasılık farkı {diff:.1f}%).")
    
    # 🆕 Momentum analizi
    momentum_a = params.get('momentum_a', 1.0)
    momentum_b = params.get('momentum_b', 1.0)
    if momentum_a >= 1.06:
        reasons.append(f"⚡ **{team_names['a']}** güçlü momentum ile geliyor (son 5 maç +10 gol farkı).")
    elif momentum_b >= 1.06:
        reasons.append(f"⚡ **{team_names['b']}** güçlü momentum ile geliyor (son 5 maç +10 gol farkı).")
    
    # 🆕 H2H dominance
    h2h_factor = params.get('h2h_factor', 1.0)
    if h2h_factor >= 1.12:
        reasons.append(f"📊 **{team_names['a']}** son karşılaşmalarda çok dominant (%80+ galibiyet oranı).")
    elif h2h_factor >= 1.06:
        reasons.append(f"📊 **{team_names['a']}** son karşılaşmalarda avantajlı (%60+ galibiyet).")
    elif h2h_factor <= 0.88:
        reasons.append(f"📊 **{team_names['b']}** son karşılaşmalarda çok dominant (%80+ galibiyet oranı).")
    elif h2h_factor <= 0.94:
        reasons.append(f"📊 **{team_names['b']}** son karşılaşmalarda avantajlı (%60+ galibiyet).")
    
    # 🆕 Hakem etkisi
    referee_factor = params.get('referee_factor', 1.0)
    if referee_factor <= 0.94:
        reasons.append("🟨 Sert hakem bekleniyor - akıcı olmayan oyun, daha az gol.")
    elif referee_factor >= 1.03:
        reasons.append("✅ Yumuşak hakem bekleniyor - akıcı oyun, daha fazla gol.")
    
    # 🆕 Sakatlık & Ceza durumu
    injury_factor_a = params.get('injury_factor_a', 1.0)
    injury_factor_b = params.get('injury_factor_b', 1.0)
    injuries_count_a = params.get('injuries_count_a', 0)
    injuries_count_b = params.get('injuries_count_b', 0)
    
    if injury_factor_a <= 0.90:
        reasons.append(f"🏥 **{team_names['a']}** ciddi sakatlık krizi yaşıyor ({injuries_count_a} oyuncu).")
    elif injury_factor_a <= 0.95:
        reasons.append(f"🩹 **{team_names['a']}** sakatlıklardan etkilenmiş ({injuries_count_a} oyuncu).")
    
    if injury_factor_b <= 0.90:
        reasons.append(f"🏥 **{team_names['b']}** ciddi sakatlık krizi yaşıyor ({injuries_count_b} oyuncu).")
    elif injury_factor_b <= 0.95:
        reasons.append(f"🩹 **{team_names['b']}** sakatlıklardan etkilenmiş ({injuries_count_b} oyuncu).")
    
    # 🆕 Takım değeri faktörü
    value_category = params.get('value_category', 'Dengeli')
    value_mult_a = params.get('value_mult_a', 1.0)
    value_mult_b = params.get('value_mult_b', 1.0)
    if value_mult_a >= 1.05:
        reasons.append(f"💰 **{team_names['a']}** kadro değeri açısından üstün ({value_category}).")
    elif value_mult_b >= 1.05:
        reasons.append(f"💰 **{team_names['b']}** kadro değeri açısından üstün ({value_category}).")
    
    # 🆕 Dinlenme süresi
    rest_a = params.get('rest_factor_a', 1.0)
    rest_b = params.get('rest_factor_b', 1.0)
    if rest_a <= 0.96:
        reasons.append(f"😓 **{team_names['a']}** kısa dinlenme süresi nedeniyle yorgun olabilir.")
    elif rest_b <= 0.96:
        reasons.append(f"😓 **{team_names['b']}** kısa dinlenme süresi nedeniyle yorgun olabilir.")

    if max_prob_key == 'win_a' and params['home_att'] > params['away_def'] * 1.4:
        reasons.append(f"**{team_names['a']}** hücum verileri ({params['home_att']:.2f} gol) rakibin savunmasından ({params['away_def']:.2f}) belirgin şekilde üstün.")
    elif max_prob_key == 'win_b' and params['away_att'] > params['home_def'] * 1.4:
        reasons.append(f"**{team_names['b']}** deplasman hücumu ({params['away_att']:.2f} gol), ev sahibi savunmasını ({params['home_def']:.2f}) baskı altına alacak güçte görünüyor.")

    stab_a = stats['a'].get('home', {}).get('Istikrar_Puani', 0)
    stab_b = stats['b'].get('away', {}).get('Istikrar_Puani', 0)
    if abs(stab_a - stab_b) > 15:
        if stab_a > stab_b and max_prob_key == 'win_a':
            reasons.append(f"Ev sahibi istikrar puanı ({stab_a:.1f}), rakibine ({stab_b:.1f}) göre belirgin biçimde yüksek.")
        elif stab_b > stab_a and max_prob_key == 'win_b':
            reasons.append(f"Deplasman istikrarı ({stab_b:.1f}), ev sahibine ({stab_a:.1f}) kıyasla daha güven veriyor.")

    if params['att_mult_b'] < 1.0 and max_prob_key == 'win_a':
        reasons.append(f"**{team_names['b']}** tarafındaki kilit hücum eksikleri, üretkenliklerini düşürüyor.")
    if params['att_mult_a'] < 1.0 and max_prob_key == 'win_b':
        reasons.append(f"**{team_names['a']}** cephesindeki önemli eksikler, ev sahibi avantajını törpülüyor.")

    form_a = params.get('form_factor_a', 1.0)
    form_b = params.get('form_factor_b', 1.0)
    form_diff = form_a - form_b
    if abs(form_diff) >= 0.08:
        if form_diff > 0:
            reasons.append(f"Son maç formu **{team_names['a']}** lehine (x{form_a:.2f} vs x{form_b:.2f}).")
        else:
            reasons.append(f"Güncel form verisi **{team_names['b']}** tarafını öne çıkarıyor (x{form_b:.2f} vs x{form_a:.2f}).")

    elo_diff = params.get('elo_diff', 0)
    if abs(elo_diff) >= 60:
        elo_fav = team_names['a'] if elo_diff > 0 else team_names['b']
        reasons.append(f"Elo farkı {abs(elo_diff):.0f} puan ve {elo_fav} lehine, kalite avantajı yaratıyor.")

    pace_idx = params.get('pace_index', 1.0)
    if pace_idx >= 1.15:
        reasons.append("Tempo beklenenin üzerinde; yüksek ritim favori tarafın lehine sonuç üretme şansını artırıyor.")

    if not reasons and winner_name:
        reasons.append(f"Genel parametre dengesi **{winner_name}** tarafını öne çıkarıyor.")

    return reasons[:5]  # 3'ten 5'e çıkardık - daha fazla faktör göster

@st.cache_data(ttl=300)  # 5 dakika - Elo güncellemeleri için kısa cache
def run_core_analysis(api_key, base_url, id_a, id_b, name_a, name_b, fixture_id, league_info, model_params, default_avg, skip_api_limit=False):
    baselines = get_league_goal_baselines(api_key, base_url, league_info, default_avg, skip_api_limit)
    avg_goals = baselines['total_avg'] or default_avg
    avg_home_goals = baselines['home_avg'] or (avg_goals * 0.55)
    avg_away_goals = baselines['away_avg'] or max(0.4, avg_goals - avg_home_goals)

    stats_a = calculate_general_stats_v2(api_key, base_url, id_a, league_info['league_id'], league_info['season'], skip_api_limit)
    stats_b = calculate_general_stats_v2(api_key, base_url, id_b, league_info['league_id'], league_info['season'], skip_api_limit)
    # Artık her zaman varsayılan değerler dönüyor, None kontrolü gereksiz

    team_home_adv = stats_a.get('team_specific_home_adv', 1.12)
    league_bias = avg_home_goals / max(0.5, avg_away_goals)
    
    # Ev sahibi avantajını takım kalitesine göre ayarla
    ratings = elo_utils.read_ratings()
    rating_home = elo_utils.get_team_rating(id_a, ratings)
    rating_away = elo_utils.get_team_rating(id_b, ratings)
    
    # Güçlü takımlar deplasmanda daha iyi oynar, ev sahibi avantajı azalır
    if rating_away > rating_home + 100:
        quality_adjust = 0.95  # Deplasman takımı çok güçlüyse ev avantajını azalt
    elif rating_away > rating_home + 50:
        quality_adjust = 0.97
    elif rating_home > rating_away + 100:
        quality_adjust = 1.08  # Ev sahibi çok güçlüyse avantaj artır
    elif rating_home > rating_away + 50:
        quality_adjust = 1.05
    else:
        quality_adjust = 1.0
    
    home_advantage = team_home_adv * max(0.96, min(1.12, league_bias)) * quality_adjust
    home_advantage = max(1.02, min(1.20, home_advantage))

    last_matches_a = api_utils.get_team_last_matches_stats(api_key, base_url, id_a, limit=10, skip_limit=skip_api_limit)
    last_matches_b = api_utils.get_team_last_matches_stats(api_key, base_url, id_b, limit=10, skip_limit=skip_api_limit)
    weighted_stats_a = calculate_weighted_stats(last_matches_a) if last_matches_a else {}
    weighted_stats_b = calculate_weighted_stats(last_matches_b) if last_matches_b else {}
    
    # Form string'lerini hesapla (görsel için)
    form_string_a = get_form_string(last_matches_a, limit=5)
    form_string_b = get_form_string(last_matches_b, limit=5)

    FORM_WEIGHT, SEASON_WEIGHT = 0.6, 0.4

    def get_blended_stat(s_stats, w_stats, loc, s_key, w_key):
        season_val = s_stats.get(loc, {}).get(s_key, 0)
        weighted_val = w_stats.get(loc, {}).get(w_key, 0)
        
        # Eğer season verisi varsa ama weighted yoksa, season verisini kullan
        if season_val > 0 and weighted_val == 0:
            weighted_val = season_val
        
        # Eğer weighted verisi varsa ama season yoksa, weighted'ı kullan
        if weighted_val > 0 and season_val == 0:
            season_val = weighted_val
        
        # Her ikisi de yoksa minimum değer döndür
        if season_val == 0 and weighted_val == 0:
            return 0.2
        
        blended = (weighted_val * FORM_WEIGHT) + (season_val * SEASON_WEIGHT)
        return max(0.2, min(blended, 2.5))

    home_att = get_blended_stat(stats_a, weighted_stats_a, 'home', 'Ort. Gol ATILAN', 'w_avg_goals_for')
    home_def = get_blended_stat(stats_a, weighted_stats_a, 'home', 'Ort. Gol YENEN', 'w_avg_goals_against')
    away_att = get_blended_stat(stats_b, weighted_stats_b, 'away', 'Ort. Gol ATILAN', 'w_avg_goals_for')
    away_def = get_blended_stat(stats_b, weighted_stats_b, 'away', 'Ort. Gol YENEN', 'w_avg_goals_against')

    def clamp(value: float, lower: float = 0.55, upper: float = 1.8) -> float:
        return max(lower, min(upper, value))

    home_attack_idx = clamp(home_att / max(0.3, avg_home_goals))
    away_attack_idx = clamp(away_att / max(0.3, avg_away_goals))
    home_def_idx = clamp(home_def / max(0.3, avg_away_goals))
    away_def_idx = clamp(away_def / max(0.3, avg_home_goals))

    injuries, _ = api_utils.get_fixture_injuries(api_key, base_url, fixture_id)
    injured_ids = {p['player']['id'] for p in injuries} if injuries else set()

    p_stats_a, _ = api_utils.get_squad_player_stats(api_key, base_url, id_a, league_info['season'])
    p_stats_b, _ = api_utils.get_squad_player_stats(api_key, base_url, id_b, league_info['season'])
    key_a = get_key_players(p_stats_a) if p_stats_a else {}
    key_b = get_key_players(p_stats_b) if p_stats_b else {}

    injury_impact = model_params['injury_impact']
    max_goals = model_params['max_goals']

    att_mult_a = injury_impact if any(pid in injured_ids for pid in key_a.get('top_scorer_ids', [])) else 1.0
    def_mult_a = (1 / injury_impact) if any(pid in injured_ids for pid in key_a.get('most_minutes_ids', [])) else 1.0
    att_mult_b = injury_impact if any(pid in injured_ids for pid in key_b.get('top_scorer_ids', [])) else 1.0
    def_mult_b = (1 / injury_impact) if any(pid in injured_ids for pid in key_b.get('most_minutes_ids', [])) else 1.0

    form_factor_a = calculate_form_factor(last_matches_a, 'home')
    form_factor_b = calculate_form_factor(last_matches_b, 'away')

    # Önce Elo farkını hesapla ve temel ayarlamayı yap
    elo_diff = rating_home - rating_away
    
    # Elo farkına göre çok daha agresif ayarlama (DÜŞÜK EŞİKLER)
    if elo_diff < -150:  # Deplasman çok güçlü (örn: PSG)
        elo_boost_away = 1.40
        elo_nerf_home = 0.70
    elif elo_diff < -80:
        elo_boost_away = 1.32
        elo_nerf_home = 0.78
    elif elo_diff < -40:  # KÜÇÜK FARKLAR BİLE ETKİLİ
        elo_boost_away = 1.25
        elo_nerf_home = 0.85
    elif elo_diff < -15:  # -15 ile -40 arası (Amed örneği -30)
        elo_boost_away = 1.18
        elo_nerf_home = 0.90
    elif elo_diff > 150:  # Ev sahibi çok güçlü
        elo_boost_away = 0.70
        elo_nerf_home = 1.35
    elif elo_diff > 80:
        elo_boost_away = 0.78
        elo_nerf_home = 1.28
    elif elo_diff > 40:  # KÜÇÜK FARKLAR BİLE ETKİLİ
        elo_boost_away = 0.85
        elo_nerf_home = 1.22
    elif elo_diff > 15:  # +15 ile +40 arası
        elo_boost_away = 0.90
        elo_nerf_home = 1.15
    else:  # -15 ile +15 arası: Gerçekten dengeli
        elo_boost_away = 1.0
        elo_nerf_home = 1.0

    base_lambda_a = avg_home_goals * home_attack_idx * away_def_idx * elo_nerf_home
    base_lambda_b = avg_away_goals * away_attack_idx * home_def_idx * elo_boost_away

    # Ev sahibi avantajını sadece dengeli maçlarda uygula
    if abs(elo_diff) < 80:
        lambda_a = base_lambda_a * att_mult_a * def_mult_b * home_advantage
    else:
        # Büyük kalite farkında ev avantajını minimize et
        reduced_home_adv = 1.0 + ((home_advantage - 1.0) * 0.4)
        lambda_a = base_lambda_a * att_mult_a * def_mult_b * reduced_home_adv
    
    lambda_b = base_lambda_b * att_mult_b * def_mult_a

    lambda_a *= min(1.08, max(0.92, form_factor_a))
    lambda_b *= min(1.08, max(0.92, form_factor_b))
    
    # 🆕 YENİ FAKTÖRLER - Gelişmiş Analiz Sistemi
    
    # Takım değeri faktörü (Elo ve lig bazlı)
    team_value_data = calculate_team_value_factor(rating_home, rating_away, league_info['league_id'])
    value_mult_a = team_value_data['value_mult_a']
    value_mult_b = team_value_data['value_mult_b']
    value_category = team_value_data['value_category']
    lambda_a *= value_mult_a
    lambda_b *= value_mult_b
    
    # Momentum faktörü (son 5 maçtaki trend)
    momentum_a = calculate_momentum_factor(last_matches_a, 'home')
    momentum_b = calculate_momentum_factor(last_matches_b, 'away')
    lambda_a *= momentum_a
    lambda_b *= momentum_b
    
    # Dinlenme süresi faktörü
    rest_factor_a = calculate_rest_days_factor(last_matches_a)
    rest_factor_b = calculate_rest_days_factor(last_matches_b)
    lambda_a *= rest_factor_a
    lambda_b *= rest_factor_b
    
    # H2H faktörü
    h2h_matches, _ = api_utils.get_h2h_matches(api_key, base_url, id_a, id_b, 10)
    h2h_data = process_h2h_data(h2h_matches, id_a)
    h2h_factor = calculate_h2h_factor(h2h_data, id_a)
    lambda_a *= h2h_factor
    lambda_b *= (2.0 - h2h_factor)  # Ters oran
    
    # Hakem faktörü
    fixture_details, _ = api_utils.get_fixture_details(api_key, base_url, fixture_id)
    referee_stats_processed = None
    if fixture_details:
        referee_info = fixture_details.get('fixture', {}).get('referee')
        if isinstance(referee_info, dict):
            referee_id = referee_info.get('id')
            if referee_id:
                referee_data, _ = api_utils.get_referee_stats(api_key, base_url, referee_id, league_info['season'])
                referee_stats_processed = process_referee_data(referee_data)
    
    referee_factor = calculate_referee_factor(referee_stats_processed)
    lambda_a *= referee_factor
    lambda_b *= referee_factor
    
    # Sakatlık & Ceza faktörü
    injuries_a, _ = api_utils.get_team_injuries(api_key, base_url, id_a, fixture_id)
    injuries_b, _ = api_utils.get_team_injuries(api_key, base_url, id_b, fixture_id)
    injury_factor_a = calculate_injury_factor(injuries_a, id_a)
    injury_factor_b = calculate_injury_factor(injuries_b, id_b)
    lambda_a *= injury_factor_a
    lambda_b *= injury_factor_b
    
    # Lig kalitesi çarpanı
    league_quality = calculate_league_quality_multiplier(league_info['league_id'])
    # Lig kalitesi Elo farkının etkisini artırır
    if league_quality >= 1.0:  # Üst düzey ligler
        # Kalite farkı daha belirgin olur
        if abs(elo_diff) > 100:
            if elo_diff > 0:
                lambda_a *= 1.02
                lambda_b *= 0.98
            else:
                lambda_a *= 0.98
                lambda_b *= 1.02

    # Kalite farkı yüksekse regresyonu azalt
    quality_gap = abs(elo_diff)
    if quality_gap > 150:
        regression_factor = 0.90  # Büyük fark varsa modele çok güven
    elif quality_gap > 80:
        regression_factor = 0.87
    else:
        regression_factor = 0.80  # Dengeli maçlarda muhafazakar
    
    lambda_a = (lambda_a * regression_factor) + (avg_home_goals * (1 - regression_factor))
    lambda_b = (lambda_b * regression_factor) + (avg_away_goals * (1 - regression_factor))

    lambda_a = max(0.3, min(lambda_a, max_goals))
    lambda_b = max(0.3, min(lambda_b, max_goals))

    score_a = round(lambda_a, 2)
    score_b = round(lambda_b, 2)

    probs = calculate_match_probabilities(score_a, score_b)
    
    # 🆕 Bahis oranlarıyla model tahminini birleştir (%70 model + %30 odds)
    odds_response, _ = api_utils.get_fixture_odds(api_key, base_url, fixture_id)
    odds_data = process_odds_data(odds_response) if odds_response else None
    
    if odds_data:
        adjusted_probs = calculate_odds_based_adjustment(
            odds_data,
            probs['win_a'],
            probs['draw'],
            probs['win_b']
        )
        # Adjusted probları kullan
        probs['win_a'] = adjusted_probs['win_a']
        probs['draw'] = adjusted_probs['draw']
        probs['win_b'] = adjusted_probs['win_b']
    
    ranking = sorted([probs['win_a'], probs['win_b'], probs['draw']], reverse=True)
    diff = round(ranking[0] - ranking[1], 1)

    stability_a = stats_a.get('home', {}).get('Istikrar_Puani', 0)
    stability_b = stats_b.get('away', {}).get('Istikrar_Puani', 0)
    avg_stab = (stability_a + stability_b) / 2 if stability_a and stability_b else 0

    volatility_ratio = baselines['total_std'] / max(0.3, baselines['total_avg'])
    volatility_ratio = max(0.1, min(1.5, volatility_ratio))
    sample_factor = min(1.0, baselines['sample_size'] / 160) if baselines['sample_size'] else 0.4
    elo_signal = min(0.5, abs(elo_diff) / 320)
    stability_component = 0.55 + (avg_stab / 200)
    confidence_multiplier = stability_component * (0.75 + 0.25 * sample_factor) * (1 - 0.25 * volatility_ratio) * (1 + 0.5 * elo_signal)
    confidence = round(min(100.0, max(5.0, diff * max(0.4, confidence_multiplier))), 1)

    pace_index = (home_att + away_att) / max(0.2, avg_home_goals + avg_away_goals)
    
    # 📊 GERÇEK GÜÇ FARKI HESAPLAMA (ELO + Takım Performansı)
    # ELO farkı sıfır/küçük olduğunda takım performansına göre gerçek farkı bul
    
    # Takım gücü skoru (hücum + savunma indeksleri)
    home_power_score = (home_attack_idx * 60) + ((2.0 - home_def_idx) * 40)  # 0-180 arası
    away_power_score = (away_attack_idx * 60) + ((2.0 - away_def_idx) * 40)
    
    # Performans bazlı "sanal ELO farkı"
    performance_diff = (home_power_score - away_power_score) * 2.5  # -450 ile +450 arası
    
    # ELO farkı küçükse performans farkını kullan
    if abs(elo_diff) < 50:
        # ELO güvenilmez, performans farkını ağırlıkla kullan
        adjusted_elo_diff = (elo_diff * 0.3) + (performance_diff * 0.7)
    elif abs(elo_diff) < 150:
        # Orta güven, 50-50 karışım
        adjusted_elo_diff = (elo_diff * 0.6) + (performance_diff * 0.4)
    else:
        # ELO güvenilir, ama performansı da ekle
        adjusted_elo_diff = (elo_diff * 0.85) + (performance_diff * 0.15)
    
    # 📊 ELO BAZLI DENGELİ SİSTEM (Düzeltilmiş ELO ile)
    # Artık "gerçek güç farkı" kullanılıyor
    elo_dominance = 1.0  # Varsayılan dengeli maç
    
    if abs(adjusted_elo_diff) < 30:
        # Çok dengeli maç (ELO farkı <30)
        match_type = "Çok Dengeli"
        elo_dominance = 1.00
        corner_intensity = 0.95  # Az daha az korner (defensif)
        card_intensity = 1.20    # %20 daha fazla kart (kavgalı)
    elif abs(adjusted_elo_diff) < 80:
        # Dengeli maç (ELO farkı 30-80)
        match_type = "Dengeli"
        elo_dominance = 1.05
        corner_intensity = 1.00  # Normal korner
        card_intensity = 1.10    # %10 daha fazla kart
    elif abs(adjusted_elo_diff) < 150:
        # Orta seviye fark (ELO farkı 80-150)
        match_type = "Hafif Fark"
        elo_dominance = 1.12
        corner_intensity = 1.08  # %8 daha fazla korner (tek taraflı baskı)
        card_intensity = 1.00    # Normal kart
    elif abs(adjusted_elo_diff) < 250:
        # Büyük fark (ELO farkı 150-250)
        match_type = "Büyük Fark"
        elo_dominance = 1.20
        corner_intensity = 1.15  # %15 daha fazla korner (tam baskı)
        card_intensity = 0.90    # %10 daha az kart (tek taraflı)
    else:
        # Çok büyük fark (ELO farkı >250)
        match_type = "Çok Büyük Fark"
        elo_dominance = 1.30
        corner_intensity = 1.25  # %25 daha fazla korner (total baskı)
        card_intensity = 0.80    # %20 daha az kart (kolay maç)
        card_intensity = 0.80    # %20 daha az kart (kolay maç)
    
    # 🆕 KORNER TAHMİNLERİ - GELİŞTİRİLMİŞ FORMÜL (ELO + Gol bazlı)
    # Ev sahibi korner tahmini (maç başına)
    home_base_corners = 3.0  # Ortalama ev sahibi baz
    home_attack_bonus = (home_attack_idx - 1.0) * 2.5  # Güçlü hücum = +korner
    home_press_bonus = (2.0 - away_def_idx) * 1.5  # Zayıf rakip savunma = +korner
    
    # DÜZELTILMIŞ ELO etkisi: Güçlü takım daha fazla korner kazanır
    if adjusted_elo_diff > 0:  # Ev sahibi güçlü
        home_elo_bonus = min(2.0, adjusted_elo_diff / 100)  # Maksimum +2 korner
        away_elo_penalty = -min(1.0, adjusted_elo_diff / 150)  # Maksimum -1 korner
        away_elo_bonus = 0
    else:  # Deplasman güçlü
        home_elo_bonus = max(-1.0, adjusted_elo_diff / 150)  # Maksimum -1 korner
        away_elo_bonus = min(2.0, abs(adjusted_elo_diff) / 100)  # Maksimum +2 korner
        away_elo_penalty = 0
    
    home_corners_raw = home_base_corners + home_attack_bonus + home_press_bonus + home_elo_bonus
    home_corners_avg = max(2.0, min(7.5, home_corners_raw * corner_intensity))
    
    # Deplasman korner tahmini
    away_base_corners = 2.5  # Ortalama deplasman baz
    away_attack_bonus = (away_attack_idx - 1.0) * 2.5
    away_press_bonus = (2.0 - home_def_idx) * 1.5
    
    if adjusted_elo_diff <= 0:  # Deplasman güçlü
        away_corners_raw = away_base_corners + away_attack_bonus + away_press_bonus + away_elo_bonus
    else:  # Ev sahibi güçlü
        away_corners_raw = away_base_corners + away_attack_bonus + away_press_bonus + away_elo_penalty
    
    away_corners_avg = max(1.5, min(6.5, away_corners_raw * corner_intensity))
    
    # Lig ortalamasına göre normalize et
    league_avg_corners = 10.5
    corner_probs = calculate_corner_probabilities(home_corners_avg, away_corners_avg, league_avg_corners)
    
    # 🆕 KART TAHMİNLERİ - ELO BAZLI DENGELI FORMÜL
    # Hakem bazlı tahmin (hakem sertliği en önemli faktör)
    if referee_stats_processed:
        referee_yellow_avg = referee_stats_processed.get('yellow_per_game', 4.0)
        referee_red_avg = referee_stats_processed.get('red_per_game', 0.15)
    else:
        # Hakem verisi yoksa lig ortalaması
        referee_yellow_avg = 3.8  # Gerçekçi ortalama
        referee_red_avg = 0.12   # ~8 maçta 1 kırmızı
    
    # ELO bazlı kart yoğunluğu (yukarıda hesaplandı: card_intensity)
    # Dengeli maç = daha fazla kart, tek taraflı maç = daha az kart
    final_yellow_avg = referee_yellow_avg * card_intensity
    final_red_avg = referee_red_avg * card_intensity
    
    # Gerçekçi sınırlar
    final_yellow_avg = max(2.5, min(6.0, final_yellow_avg))  # 2.5-6.0 arası
    final_red_avg = max(0.05, min(0.30, final_red_avg))      # %5-30 arası
    
    card_probs = calculate_card_probabilities(final_yellow_avg, final_red_avg)
    
    # 🆕 İLK YARI 1X2 TAHMİNLERİ
    first_half_probs = calculate_first_half_probabilities(score_a, score_b)

    analysis_result = {
        'score_a': score_a,
        'score_b': score_b,
        'expected_total': round(lambda_a + lambda_b, 2),
        'goal_spread': round(lambda_a - lambda_b, 2),
        'probs': probs,
        'corner_probs': corner_probs,
        'card_probs': card_probs,
        'first_half_probs': first_half_probs,
        'confidence': confidence,
        'diff': diff,
        'params': {
            'avg_goals': avg_goals,
            'avg_home_goals': avg_home_goals,
            'avg_away_goals': avg_away_goals,
            'home_att': home_att,
            'home_def': home_def,
            'away_att': away_att,
            'away_def': away_def,
            'home_attack_idx': home_attack_idx,
            'away_attack_idx': away_attack_idx,
            'home_def_idx': home_def_idx,
            'away_def_idx': away_def_idx,
            'att_mult_a': att_mult_a,
            'def_mult_a': def_mult_a,
            'att_mult_b': att_mult_b,
            'def_mult_b': def_mult_b,
            'home_advantage': home_advantage,
            'form_factor_a': form_factor_a,
            'form_factor_b': form_factor_b,
            'elo_home': rating_home,
            'elo_away': rating_away,
            'elo_diff': elo_diff,
            'elo_boost_away': elo_boost_away,
            'elo_nerf_home': elo_nerf_home,
            'baseline_std': baselines['total_std'],
            'sample_size': baselines['sample_size'],
            'pace_index': pace_index,
            # 🆕 Yeni faktörler
            'momentum_a': momentum_a,
            'momentum_b': momentum_b,
            'rest_factor_a': rest_factor_a,
            'rest_factor_b': rest_factor_b,
            'h2h_factor': h2h_factor,
            'referee_factor': referee_factor,
            'league_quality': league_quality,
            'odds_used': odds_data is not None,
            'injury_factor_a': injury_factor_a,
            'injury_factor_b': injury_factor_b,
            'injuries_count_a': len(injuries_a) if injuries_a else 0,
            'injuries_count_b': len(injuries_b) if injuries_b else 0,
            'form_string_a': form_string_a,
            'form_string_b': form_string_b,
            'value_mult_a': value_mult_a,
            'value_mult_b': value_mult_b,
            'value_category': value_category,
        },
        'stats': {'a': stats_a, 'b': stats_b},
    }

    reasons = generate_prediction_reasons(analysis_result, {'a': name_a, 'b': name_b})
    analysis_result['reasons'] = reasons

    return analysis_result