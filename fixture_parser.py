# -*- coding: utf-8 -*-
"""
Fixture Data Parser - API verisini Advanced Metrics formatına çevir
"""

from typing import Dict, List, Optional

def parse_fixtures_to_matches(fixtures: List[Dict], team_id: int) -> List[Dict]:
    """
    API'den gelen fixture verilerini advanced metrics için gerekli formata çevir
    
    Args:
        fixtures: API'den gelen fixture listesi
        team_id: İlgili takım ID
    
    Returns:
        List of match dicts with format:
        {
            'goals_for': int,
            'goals_against': int,
            'opponent_id': int,
            'opponent_name': str,
            'location': 'home' | 'away',
            'result': 'W' | 'D' | 'L',
            'date': str,
            'league_id': int
        }
    """
    matches = []
    
    for fixture in fixtures:
        try:
            # Fixture temel bilgileri
            fixture_data = fixture.get('fixture', {})
            teams_data = fixture.get('teams', {})
            goals_data = fixture.get('goals', {})
            league_data = fixture.get('league', {})
            
            # Maç bitti mi kontrol et
            status = fixture_data.get('status', {}).get('short', '')
            if status not in ['FT', 'AET', 'PEN']:  # Sadece tamamlanmış maçlar
                continue
            
            # Ev sahibi mi deplasman mı?
            home_team = teams_data.get('home', {})
            away_team = teams_data.get('away', {})
            
            is_home = home_team.get('id') == team_id
            
            # Goller
            home_goals = goals_data.get('home')
            away_goals = goals_data.get('away')
            
            if home_goals is None or away_goals is None:
                continue
            
            # Takım perspektifinden goller
            if is_home:
                goals_for = home_goals
                goals_against = away_goals
                opponent_id = away_team.get('id')
                opponent_name = away_team.get('name')
                location = 'home'
            else:
                goals_for = away_goals
                goals_against = home_goals
                opponent_id = home_team.get('id')
                opponent_name = home_team.get('name')
                location = 'away'
            
            # Sonuç
            if goals_for > goals_against:
                result = 'W'
            elif goals_for == goals_against:
                result = 'D'
            else:
                result = 'L'
            
            # Match dict oluştur
            match_dict = {
                'goals_for': int(goals_for),
                'goals_against': int(goals_against),
                'opponent_id': opponent_id,
                'opponent_name': opponent_name,
                'location': location,
                'result': result,
                'date': fixture_data.get('date', ''),
                'league_id': league_data.get('id', 0),
                'fixture_id': fixture_data.get('id', 0)
            }
            
            matches.append(match_dict)
            
        except Exception as e:
            print(f"⚠️ Fixture parse hatası: {e}")
            continue
    
    return matches


def get_opponent_strengths_from_api(
    api_key: str,
    base_url: str,
    opponent_ids: List[int],
    league_id: int,
    season: int
) -> List[float]:
    """
    Rakip takımların güç seviyelerini API'den al
    
    Returns:
        List of strength scores (0.0-1.0) for each opponent
    """
    import api_utils
    
    strengths = []
    
    for opponent_id in opponent_ids:
        try:
            # Rakip istatistiklerini al
            stats_data, error = api_utils.get_team_statistics(
                api_key=api_key,
                base_url=base_url,
                team_id=opponent_id,
                league_id=league_id,
                season=season,
                skip_limit=True
            )
            
            if error or not stats_data:
                # Varsayılan: ortalama güç
                strengths.append(0.5)
                continue
            
            # Basit güç hesabı: PPG (points per game)
            fixtures_played = stats_data.get('fixtures', {}).get('played', {}).get('total', 0)
            wins = stats_data.get('fixtures', {}).get('wins', {}).get('total', 0)
            draws = stats_data.get('fixtures', {}).get('draws', {}).get('total', 0)
            
            if fixtures_played > 0:
                ppg = (wins * 3 + draws) / fixtures_played
                # Normalize to 0-1 (3 PPG = 1.0, 0 PPG = 0.0)
                strength = ppg / 3.0
                strengths.append(strength)
            else:
                strengths.append(0.5)
                
        except Exception as e:
            print(f"⚠️ Opponent strength hesaplama hatası: {e}")
            strengths.append(0.5)
    
    return strengths


# Test
if __name__ == "__main__":
    # Örnek fixture verisi (API formatı)
    sample_fixture = {
        'fixture': {
            'id': 1234,
            'date': '2024-11-01T20:00:00+00:00',
            'status': {'short': 'FT'}
        },
        'league': {
            'id': 203,
            'name': 'Süper Lig'
        },
        'teams': {
            'home': {'id': 645, 'name': 'Galatasaray'},
            'away': {'id': 610, 'name': 'Fenerbahçe'}
        },
        'goals': {
            'home': 2,
            'away': 1
        }
    }
    
    # Parse et
    fixtures_list = [sample_fixture]
    matches = parse_fixtures_to_matches(fixtures_list, team_id=645)
    
    print("✅ Parsed Matches:")
    for m in matches:
        print(f"   {m['opponent_name']}: {m['goals_for']}-{m['goals_against']} ({m['result']}) - {m['location']}")
