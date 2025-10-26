"""
API-Football v3 Professional Wrapper
====================================

Modern ve kapsamlı API-Football v3 wrapper modülü.
Tüm endpoint'leri destekler ve gelişmiş hata yönetimi sağlar.

Desteklenen Endpoint'ler:
- Teams (search, statistics, seasons)
- Fixtures (live, finished, statistics, events, lineups, players) 
- Leagues (all leagues, seasons, standings)
- Players (search, statistics, transfers, injuries)
- Coaches (search, career)
- Venues (search, information)
- Standings (league standings)
- Predictions (match predictions)
- Odds (betting odds)
- Trophies (team trophies)
- Injuries (player injuries)
- Transfers (player transfers)
- Sidelined (injured players)
"""

import requests
import json
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, date
from dataclasses import dataclass
from enum import Enum
import logging

# Logger yapılandırması
logger = logging.getLogger(__name__)

class APIStatus(Enum):
    """API request status codes"""
    SUCCESS = "success"
    ERROR = "error" 
    RATE_LIMIT = "rate_limit"
    NO_DATA = "no_data"

@dataclass
class APIResponse:
    """API response wrapper"""
    status: APIStatus
    data: Optional[Any] = None
    error: Optional[str] = None
    rate_limit_info: Optional[Dict] = None
    raw_response: Optional[Dict] = None

class APIFootballV3:
    """Professional API-Football v3 wrapper"""
    
    BASE_URL = "https://v3.football.api-sports.io"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            'x-rapidapi-key': api_key,
            'x-rapidapi-host': 'v3.football.api-sports.io'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def _make_request(self, endpoint: str, params: Dict = None) -> APIResponse:
        """Base request method with comprehensive error handling"""
        try:
            url = f"{self.BASE_URL}/{endpoint}"
            
            logger.info(f"API Request: {endpoint} with params: {params}")
            
            response = self.session.get(url, params=params or {}, timeout=30)
            
            # Rate limit bilgilerini yakala
            rate_limit_info = {
                'requests_limit': response.headers.get('x-ratelimit-requests-limit'),
                'requests_remaining': response.headers.get('x-ratelimit-requests-remaining'),  
                'requests_reset': response.headers.get('x-ratelimit-requests-reset')
            }
            
            # HTTP status kontrolleri
            if response.status_code == 429:
                return APIResponse(
                    status=APIStatus.RATE_LIMIT,
                    error="Rate limit exceeded",
                    rate_limit_info=rate_limit_info
                )
            
            response.raise_for_status()
            
            data = response.json()
            
            # API response format kontrolü
            if not isinstance(data, dict) or 'response' not in data:
                return APIResponse(
                    status=APIStatus.ERROR,
                    error="Invalid API response format",
                    raw_response=data
                )
            
            # Error kontrolü
            if data.get('errors') and len(data['errors']) > 0:
                error_msg = "; ".join([str(err) for err in data['errors']])
                return APIResponse(
                    status=APIStatus.ERROR,
                    error=error_msg,
                    raw_response=data
                )
            
            # Success response
            return APIResponse(
                status=APIStatus.SUCCESS,
                data=data['response'],
                rate_limit_info=rate_limit_info,
                raw_response=data
            )
            
        except requests.exceptions.Timeout:
            return APIResponse(status=APIStatus.ERROR, error="Request timeout")
        except requests.exceptions.ConnectionError:
            return APIResponse(status=APIStatus.ERROR, error="Connection error")
        except requests.exceptions.HTTPError as e:
            return APIResponse(status=APIStatus.ERROR, error=f"HTTP error: {e}")
        except Exception as e:
            return APIResponse(status=APIStatus.ERROR, error=f"Unexpected error: {e}")
    
    # ========================
    # TEAMS ENDPOINTS
    # ========================
    
    def search_teams(self, query: str, league_id: Optional[int] = None, 
                     season: Optional[int] = None) -> APIResponse:
        """
        Search teams by name
        
        Args:
            query: Team name to search
            league_id: Filter by league ID
            season: Filter by season (required for most leagues)
        """
        params = {"search": query}
        if league_id:
            params["league"] = league_id
        if season:
            params["season"] = season
            
        return self._make_request("teams", params)
    
    def get_team_by_id(self, team_id: int, season: Optional[int] = None) -> APIResponse:
        """Get team by ID with optional season"""
        params = {"id": team_id}
        if season:
            params["season"] = season
        return self._make_request("teams", params)
    
    def get_team_statistics(self, team_id: int, league_id: int, season: int) -> APIResponse:
        """
        Get comprehensive team statistics
        
        Args:
            team_id: Team ID
            league_id: League ID 
            season: Season year (required)
        """
        params = {
            "team": team_id,
            "league": league_id, 
            "season": season
        }
        return self._make_request("teams/statistics", params)
    
    def get_teams_by_league(self, league_id: int, season: int) -> APIResponse:
        """Get all teams in a league for specific season"""
        params = {
            "league": league_id,
            "season": season
        }
        return self._make_request("teams", params)
    
    # ========================
    # FIXTURES ENDPOINTS  
    # ========================
    
    def get_fixtures_by_date(self, date_str: str, 
                            league_id: Optional[int] = None,
                            team_id: Optional[int] = None) -> APIResponse:
        """Get fixtures by date (YYYY-MM-DD)"""
        params = {"date": date_str}
        if league_id:
            params["league"] = league_id
        if team_id:
            params["team"] = team_id
        return self._make_request("fixtures", params)
    
    def get_team_fixtures(self, team_id: int, season: int,
                         league_id: Optional[int] = None,
                         last: Optional[int] = None,
                         next: Optional[int] = None) -> APIResponse:
        """
        Get team fixtures
        
        Args:
            team_id: Team ID
            season: Season year
            league_id: Filter by league
            last: Last N fixtures
            next: Next N fixtures
        """
        params = {"team": team_id, "season": season}
        if league_id:
            params["league"] = league_id
        if last:
            params["last"] = last
        if next:
            params["next"] = next
        return self._make_request("fixtures", params)
    
    def get_fixture_statistics(self, fixture_id: int) -> APIResponse:
        """Get detailed fixture statistics"""
        return self._make_request("fixtures/statistics", {"fixture": fixture_id})
    
    def get_fixture_events(self, fixture_id: int) -> APIResponse:
        """Get fixture events (goals, cards, etc.)"""  
        return self._make_request("fixtures/events", {"fixture": fixture_id})
    
    def get_fixture_lineups(self, fixture_id: int) -> APIResponse:
        """Get fixture lineups"""
        return self._make_request("fixtures/lineups", {"fixture": fixture_id})
    
    def get_fixture_players(self, fixture_id: int) -> APIResponse:
        """Get fixture player statistics"""
        return self._make_request("fixtures/players", {"fixture": fixture_id})
    
    def get_live_fixtures(self) -> APIResponse:
        """Get live fixtures"""
        return self._make_request("fixtures", {"live": "all"})
    
    def get_h2h_fixtures(self, team1_id: int, team2_id: int, 
                        last: Optional[int] = 10) -> APIResponse:
        """Get head-to-head fixtures between two teams"""
        params = {"h2h": f"{team1_id}-{team2_id}"}
        if last:
            params["last"] = last
        return self._make_request("fixtures/headtohead", params)
    
    # ========================
    # LEAGUES ENDPOINTS
    # ========================
    
    def get_all_leagues(self, season: Optional[int] = None, 
                       country: Optional[str] = None) -> APIResponse:
        """Get all available leagues"""
        params = {}
        if season:
            params["season"] = season
        if country:
            params["country"] = country
        return self._make_request("leagues", params)
    
    def get_league_seasons(self, league_id: int) -> APIResponse:
        """Get available seasons for a league"""
        return self._make_request("leagues/seasons", {"league": league_id})
    
    # ========================
    # STANDINGS ENDPOINTS
    # ========================
    
    def get_league_standings(self, league_id: int, season: int,
                            team_id: Optional[int] = None) -> APIResponse:
        """Get league standings"""
        params = {"league": league_id, "season": season}
        if team_id:
            params["team"] = team_id
        return self._make_request("standings", params)
    
    # ========================
    # PLAYERS ENDPOINTS
    # ========================
    
    def search_players(self, query: str, league_id: Optional[int] = None,
                      season: Optional[int] = None, 
                      team_id: Optional[int] = None) -> APIResponse:
        """Search players"""
        params = {"search": query}
        if league_id:
            params["league"] = league_id
        if season:
            params["season"] = season
        if team_id:
            params["team"] = team_id
        return self._make_request("players", params)
    
    def get_player_statistics(self, player_id: int, season: int,
                             league_id: Optional[int] = None) -> APIResponse:
        """Get player statistics"""
        params = {"id": player_id, "season": season}
        if league_id:
            params["league"] = league_id
        return self._make_request("players", params)
    
    def get_team_squad(self, team_id: int) -> APIResponse:
        """Get team squad"""
        return self._make_request("players/squads", {"team": team_id})
    
    def get_top_scorers(self, league_id: int, season: int) -> APIResponse:
        """Get top scorers in a league"""
        return self._make_request("players/topscorers", {
            "league": league_id, 
            "season": season
        })
    
    def get_top_assists(self, league_id: int, season: int) -> APIResponse:
        """Get top assists in a league"""
        return self._make_request("players/topassists", {
            "league": league_id,
            "season": season
        })
    
    # ========================
    # INJURIES ENDPOINTS
    # ========================
    
    def get_team_injuries(self, team_id: int, 
                         league_id: Optional[int] = None,
                         season: Optional[int] = None) -> APIResponse:
        """Get team injuries"""
        params = {"team": team_id}
        if league_id:
            params["league"] = league_id
        if season:
            params["season"] = season
        return self._make_request("injuries", params)
    
    def get_fixture_injuries(self, fixture_id: int) -> APIResponse:
        """Get fixture injuries"""
        return self._make_request("injuries", {"fixture": fixture_id})
    
    # ========================
    # TRANSFERS ENDPOINTS
    # ========================
    
    def get_player_transfers(self, player_id: int) -> APIResponse:
        """Get player transfer history"""
        return self._make_request("transfers", {"player": player_id})
    
    def get_team_transfers(self, team_id: int) -> APIResponse:
        """Get team transfers"""
        return self._make_request("transfers", {"team": team_id})
    
    # ========================
    # PREDICTIONS ENDPOINTS
    # ========================
    
    def get_fixture_predictions(self, fixture_id: int) -> APIResponse:
        """Get fixture predictions"""
        return self._make_request("predictions", {"fixture": fixture_id})
    
    # ========================
    # ODDS ENDPOINTS
    # ========================
    
    def get_fixture_odds(self, fixture_id: int, 
                        bookmaker_id: Optional[int] = None) -> APIResponse:
        """Get fixture odds"""
        params = {"fixture": fixture_id}
        if bookmaker_id:
            params["bookmaker"] = bookmaker_id
        return self._make_request("odds", params)
    
    def get_pre_match_odds(self, fixture_id: int) -> APIResponse:
        """Get pre-match odds"""
        return self._make_request("odds/pre-match", {"fixture": fixture_id})
    
    # ========================
    # TROPHIES ENDPOINTS
    # ========================
    
    def get_team_trophies(self, team_id: int) -> APIResponse:
        """Get team trophies"""
        return self._make_request("trophies", {"team": team_id})
    
    def get_coach_trophies(self, coach_id: int) -> APIResponse:
        """Get coach trophies"""
        return self._make_request("trophies", {"coach": coach_id})
    
    # ========================
    # COACHES ENDPOINTS
    # ========================
    
    def search_coaches(self, query: str, team_id: Optional[int] = None) -> APIResponse:
        """Search coaches"""
        params = {"search": query}
        if team_id:
            params["team"] = team_id
        return self._make_request("coachs", params)
    
    def get_team_coach(self, team_id: int) -> APIResponse:
        """Get team coach"""
        return self._make_request("coachs", {"team": team_id})
    
    # ========================
    # VENUES ENDPOINTS
    # ========================
    
    def search_venues(self, query: str, city: Optional[str] = None) -> APIResponse:
        """Search venues"""
        params = {"search": query}
        if city:
            params["city"] = city
        return self._make_request("venues", params)
    
    def get_team_venue(self, team_id: int) -> APIResponse:
        """Get team venue"""
        return self._make_request("venues", {"team": team_id})
    
    # ========================
    # UTILITY METHODS
    # ========================
    
    def get_api_status(self) -> APIResponse:
        """Get API status and subscription info"""
        return self._make_request("status")
    
    def get_timezones(self) -> APIResponse:
        """
        Get all available timezones
        
        Returns:
            APIResponse with list of timezone strings
            
        Example response:
            ["Africa/Abidjan", "Africa/Accra", "Europe/Istanbul", ...]
        """
        return self._make_request("timezone")
    
    def get_countries(self) -> APIResponse:
        """
        Get all available countries
        
        Returns:
            APIResponse with list of country objects containing:
            - name: Country name
            - code: Country code (2 letters)
            - flag: Country flag URL
        """
        return self._make_request("countries")
    
    # ========================================================================
    # COACHES ENDPOINTS
    # ========================================================================
    
    def get_coaches(self, team_id: Optional[int] = None, search: Optional[str] = None) -> APIResponse:
        """
        Get coaches information
        
        Args:
            team_id: Filter by team ID
            search: Search coaches by name
            
        Returns:
            APIResponse with coaches data including:
            - id, name, firstname, lastname
            - age, birth (date, place, country)
            - nationality, height, weight
            - photo
        """
        params = {}
        if team_id:
            params['team'] = team_id
        if search:
            params['search'] = search
            
        return self._make_request("coachs", params)
    
    # ========================================================================
    # VENUES ENDPOINTS  
    # ========================================================================
    
    def get_venues(self, venue_id: Optional[int] = None, 
                   name: Optional[str] = None,
                   city: Optional[str] = None,
                   country: Optional[str] = None) -> APIResponse:
        """
        Get venue/stadium information
        
        Args:
            venue_id: Specific venue ID
            name: Search by venue name
            city: Filter by city
            country: Filter by country
            
        Returns:
            APIResponse with venue data including:
            - id, name, address, city, country
            - capacity, surface, image
        """
        params = {}
        if venue_id:
            params['id'] = venue_id
        if name:
            params['name'] = name
        if city:
            params['city'] = city
        if country:
            params['country'] = country
            
        return self._make_request("venues", params)
    
    # ========================================================================
    # PREDICTIONS ENDPOINTS
    # ========================================================================
    
    def get_predictions(self, fixture_id: int) -> APIResponse:
        """
        Get match predictions
        
        Args:
            fixture_id: Fixture ID to get predictions for
            
        Returns:
            APIResponse with predictions including:
            - winner (id, name, comment)
            - win_or_draw (bool)  
            - under_over (under, over, goals)
            - goals (home, away)
            - advice, percent
            - league statistics, teams statistics
        """
        return self._make_request("predictions", {"fixture": fixture_id})
    
    # ========================================================================
    # ODDS ENDPOINTS
    # ========================================================================
    
    def get_odds(self, fixture_id: Optional[int] = None,
                 league_id: Optional[int] = None,
                 season: Optional[int] = None,
                 date_str: Optional[str] = None,
                 bookmaker_id: Optional[int] = None,
                 bet_id: Optional[int] = None,
                 page: Optional[int] = None) -> APIResponse:
        """
        Get betting odds
        
        Args:
            fixture_id: Specific fixture ID
            league_id: Filter by league
            season: Filter by season  
            date_str: Filter by date (YYYY-MM-DD)
            bookmaker_id: Filter by bookmaker
            bet_id: Filter by bet type
            page: Pagination
            
        Returns:
            APIResponse with odds data from various bookmakers
        """
        params = {}
        if fixture_id:
            params['fixture'] = fixture_id
        if league_id:
            params['league'] = league_id
        if season:
            params['season'] = season
        if date_str:
            params['date'] = date_str
        if bookmaker_id:
            params['bookmaker'] = bookmaker_id
        if bet_id:
            params['bet'] = bet_id
        if page:
            params['page'] = page
            
        return self._make_request("odds", params)
    
    def get_odds_bookmakers(self) -> APIResponse:
        """Get all available bookmakers"""
        return self._make_request("odds/bookmakers")
    
    def get_odds_bets(self) -> APIResponse:
        """Get all available bet types"""
        return self._make_request("odds/bets")
    
    # ========================================================================
    # TROPHIES ENDPOINTS
    # ========================================================================
    
    def get_trophies(self, player_id: Optional[int] = None, 
                     coach_id: Optional[int] = None) -> APIResponse:
        """
        Get trophies won by player or coach
        
        Args:
            player_id: Get trophies for specific player
            coach_id: Get trophies for specific coach
            
        Returns:
            APIResponse with trophies data including:
            - league, country, season
            - place (winner, runner-up, etc.)
        """
        params = {}
        if player_id:
            params['player'] = player_id
        if coach_id:
            params['coach'] = coach_id
            
        return self._make_request("trophies", params)
    
    # ========================================================================
    # SIDELINED ENDPOINTS (Comprehensive Injuries)
    # ========================================================================
    
    def get_sidelined(self, player_id: Optional[int] = None,
                      coach_id: Optional[int] = None,
                      team_id: Optional[int] = None) -> APIResponse:
        """
        Get comprehensive sidelined information (injuries, suspensions, etc.)
        
        Args:
            player_id: Get sidelined info for specific player
            coach_id: Get sidelined info for specific coach
            team_id: Get all sidelined players/coaches for team
            
        Returns:
            APIResponse with sidelined data including:
            - type (injury, suspension, etc.)
            - start, end dates
            - reason, description
        """
        params = {}
        if player_id:
            params['player'] = player_id
        if coach_id:
            params['coach'] = coach_id
        if team_id:
            params['team'] = team_id
            
        return self._make_request("sidelined", params)
    
    # ========================================================================
    # ADDITIONAL UTILITY METHODS
    # ========================================================================
    
    def get_current_season(self) -> int:
        """Get current season year"""
        return datetime.now().year if datetime.now().month >= 7 else datetime.now().year - 1

# Global API instance (will be initialized in main app)
api_v3: Optional[APIFootballV3] = None

def initialize_api(api_key: str) -> APIFootballV3:
    """Initialize global API instance"""
    global api_v3
    api_v3 = APIFootballV3(api_key)
    return api_v3

def get_api() -> Optional[APIFootballV3]:
    """Get global API instance"""
    return api_v3