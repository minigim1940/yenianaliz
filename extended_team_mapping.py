from typing import Dict, Optional

def get_extended_team_mappings() -> Dict[str, Dict]:
    """Genişletilmiş takım mapping'i - API limit durumunda kullanılır"""
    return {
        'galatasaray': {'id': 645, 'name': 'Galatasaray', 'country': 'Turkey', 'founded': 1905, 'logo': None},
        'gala': {'id': 645, 'name': 'Galatasaray', 'country': 'Turkey', 'founded': 1905, 'logo': None},
        'gs': {'id': 645, 'name': 'Galatasaray', 'country': 'Turkey', 'founded': 1905, 'logo': None},
        'fenerbahce': {'id': 646, 'name': 'Fenerbahçe', 'country': 'Turkey', 'founded': 1907, 'logo': None},
        'fenerbahçe': {'id': 646, 'name': 'Fenerbahçe', 'country': 'Turkey', 'founded': 1907, 'logo': None},
        'fener': {'id': 646, 'name': 'Fenerbahçe', 'country': 'Turkey', 'founded': 1907, 'logo': None},
        'fb': {'id': 646, 'name': 'Fenerbahçe', 'country': 'Turkey', 'founded': 1907, 'logo': None},
        'besiktas': {'id': 644, 'name': 'Beşiktaş', 'country': 'Turkey', 'founded': 1903, 'logo': None},
        'beşiktaş': {'id': 644, 'name': 'Beşiktaş', 'country': 'Turkey', 'founded': 1903, 'logo': None},
        'bjk': {'id': 644, 'name': 'Beşiktaş', 'country': 'Turkey', 'founded': 1903, 'logo': None},
        'trabzonspor': {'id': 643, 'name': 'Trabzonspor', 'country': 'Turkey', 'founded': 1967, 'logo': None},
        'trabzon': {'id': 643, 'name': 'Trabzonspor', 'country': 'Turkey', 'founded': 1967, 'logo': None},
    }

def find_team_in_extended_mapping(team_query: str, mappings: Dict) -> Optional[Dict]:
    """Genişletilmiş mapping'de takım ara"""
    if team_query in mappings:
        team_data = mappings[team_query]
        return {
            'id': team_data['id'],
            'name': team_data['name'],
            'country': team_data['country'],
            'founded': team_data['founded'],
            'logo': team_data['logo']
        }
    return None