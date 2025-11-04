# -*- coding: utf-8 -*-
"""
Enhanced get_fixture_details with Goals
=========================================
API'den goals bilgisini de çeker
"""

def get_fixture_details_with_goals(
    api_key: str,
    base_url: str,
    fixture_id: int,
    skip_limit: bool = False
) -> tuple:
    """
    Maç istatistiklerini VE goals bilgisini getirir
    
    Returns:
        (stats_data, goals_data, error)
        goals_data = {
            'home_goals': int,
            'away_goals': int
        }
    """
    from api_utils import make_api_request
    
    # Get fixture statistics
    stats_response, stats_error = make_api_request(
        api_key, base_url, "fixtures/statistics",
        {'fixture': fixture_id},
        skip_limit=skip_limit
    )
    
    if stats_error:
        return None, None, stats_error
    
    # Get fixture details for goals
    fixture_response, fixture_error = make_api_request(
        api_key, base_url, "fixtures",
        {'id': fixture_id},
        skip_limit=skip_limit
    )
    
    if fixture_error:
        return stats_response, None, None  # Return stats even if goals fail
    
    # Extract goals
    goals_data = {'home_goals': 0, 'away_goals': 0}
    
    try:
        if fixture_response and 'response' in fixture_response:
            fixture_info = fixture_response['response'][0]
            goals = fixture_info.get('goals', {})
            goals_data['home_goals'] = goals.get('home', 0) or 0
            goals_data['away_goals'] = goals.get('away', 0) or 0
    except (IndexError, KeyError, TypeError):
        pass  # Keep default 0-0
    
    return stats_response, goals_data, None


if __name__ == "__main__":
    print("Enhanced fixture details function created!")
    print("Usage:")
    print("  stats, goals, error = get_fixture_details_with_goals(api_key, base_url, fixture_id)")
    print("  home_goals = goals['home_goals']")
    print("  away_goals = goals['away_goals']")
