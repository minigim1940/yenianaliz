from typing import Dict, Optional

# Sample fixture data for when API is limited
SAMPLE_FIXTURES = {
    645: {  # Galatasaray
        'fixture': {
            'id': 1234567,
            'date': '2024-11-02T17:00:00+00:00',
            'status': {'short': 'NS', 'long': 'Not Started'}
        },
        'teams': {
            'home': {'id': 645, 'name': 'Galatasaray', 'logo': None},
            'away': {'id': 609, 'name': 'Istanbul Basaksehir', 'logo': None}
        },
        'league': {
            'id': 203,
            'name': 'Super Lig',
            'country': 'Turkey',
            'season': 2024
        }
    },
    646: {  # Fenerbahçe
        'fixture': {
            'id': 1234568,
            'date': '2024-11-03T17:00:00+00:00',
            'status': {'short': 'NS', 'long': 'Not Started'}
        },
        'teams': {
            'home': {'id': 646, 'name': 'Fenerbahçe', 'logo': None},
            'away': {'id': 558, 'name': 'Antalyaspor', 'logo': None}
        },
        'league': {
            'id': 203,
            'name': 'Super Lig',
            'country': 'Turkey',
            'season': 2024
        }
    },
    644: {  # Beşiktaş
        'fixture': {
            'id': 1234569,
            'date': '2024-11-04T17:00:00+00:00',
            'status': {'short': 'NS', 'long': 'Not Started'}
        },
        'teams': {
            'home': {'id': 644, 'name': 'Beşiktaş', 'logo': None},
            'away': {'id': 643, 'name': 'Trabzonspor', 'logo': None}
        },
        'league': {
            'id': 203,
            'name': 'Super Lig',
            'country': 'Turkey',
            'season': 2024
        }
    }
}

SAMPLE_INJURIES = {
    645: [  # Galatasaray
        {
            'player': {'id': 1, 'name': 'Mauro Icardi', 'type': 'attacker'},
            'injury': {'type': 'Cruciate Ligament', 'reason': 'Injury'},
            'fixture': {'date': '2024-10-20'}
        },
        {
            'player': {'id': 2, 'name': 'Victor Osimhen', 'type': 'attacker'},
            'injury': {'type': 'Fitness', 'reason': 'Fitness'},
            'fixture': {'date': '2024-10-22'}
        }
    ],
    646: [  # Fenerbahçe
        {
            'player': {'id': 3, 'name': 'Dzeko', 'type': 'attacker'},
            'injury': {'type': 'Muscle Injury', 'reason': 'Injury'},
            'fixture': {'date': '2024-10-18'}
        }
    ]
}

def get_sample_fixture(team_id: int):
    """Sample fixture data when API is limited"""
    return SAMPLE_FIXTURES.get(team_id, None)

def get_sample_injuries(team_id: int):
    """Sample injury data when API is limited"""
    return SAMPLE_INJURIES.get(team_id, [])