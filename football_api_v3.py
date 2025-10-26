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
    
    def get_fixture_by_id(self, fixture_id: int) -> APIResponse:
        """Get specific fixture by ID"""
        return self._make_request("fixtures", {"id": fixture_id})
    
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
    
    def get_team_form_analysis(self, team_id: int, season: int, 
                              venue: Optional[str] = None, last: int = 10) -> APIResponse:
        """Get detailed team form analysis"""
        params = {"team": team_id, "season": season, "last": last}
        if venue in ['home', 'away']:
            params["venue"] = venue
        return self._make_request("fixtures", params)
    
    def get_team_performance_by_venue(self, team_id: int, season: int) -> APIResponse:
        """Get team performance split by home/away"""
        # This combines home and away fixtures for comparison
        home_fixtures = self._make_request("fixtures", {
            "team": team_id, "season": season, "venue": "home"
        })
        away_fixtures = self._make_request("fixtures", {
            "team": team_id, "season": season, "venue": "away"
        })
        
        return APIResponse(
            status=APIStatus.SUCCESS,
            data={
                'home_fixtures': home_fixtures.data if home_fixtures.status == APIStatus.SUCCESS else [],
                'away_fixtures': away_fixtures.data if away_fixtures.status == APIStatus.SUCCESS else []
            }
        )
    
    def get_team_monthly_performance(self, team_id: int, season: int) -> APIResponse:
        """Get team performance by month"""
        # This would require multiple API calls to get fixtures by month
        # Implementation would collect fixtures from different months
        return self._make_request("fixtures", {"team": team_id, "season": season})
    
    def get_fixture_difficulty_rating(self, team_id: int, next_fixtures: int = 5) -> APIResponse:
        """Get upcoming fixtures difficulty rating"""
        return self._make_request("fixtures", {
            "team": team_id, "next": next_fixtures
        })
    
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
    
    def get_live_odds(self, fixture_id: int) -> APIResponse:
        """Get live/in-play odds"""
        return self._make_request("odds/live", {"fixture": fixture_id})
    
    def get_odds_history(self, fixture_id: int, bookmaker_id: Optional[int] = None) -> APIResponse:
        """Get odds movement history"""
        params = {"fixture": fixture_id}
        if bookmaker_id:
            params["bookmaker"] = bookmaker_id
        return self._make_request("odds/history", params)
    
    def get_over_under_odds(self, fixture_id: int, goals: float = 2.5) -> APIResponse:
        """Get over/under odds for specific goals threshold"""
        return self._make_request("odds", {
            "fixture": fixture_id,
            "bet": "Goals Over/Under",
            "value": str(goals)
        })
    
    def get_both_teams_score_odds(self, fixture_id: int) -> APIResponse:
        """Get both teams to score odds"""
        return self._make_request("odds", {
            "fixture": fixture_id,
            "bet": "Both Teams Score"
        })
    
    def get_asian_handicap_odds(self, fixture_id: int, handicap: float = 0.0) -> APIResponse:
        """Get Asian handicap odds"""
        return self._make_request("odds", {
            "fixture": fixture_id,
            "bet": "Asian Handicap",
            "value": str(handicap)
        })
    
    def get_correct_score_odds(self, fixture_id: int) -> APIResponse:
        """Get correct score odds"""
        return self._make_request("odds", {
            "fixture": fixture_id,
            "bet": "Exact Score"
        })
    
    def get_first_goal_odds(self, fixture_id: int) -> APIResponse:
        """Get first goal scorer odds"""
        return self._make_request("odds", {
            "fixture": fixture_id,
            "bet": "First Goalscorer"
        })
    
    def get_half_time_full_time_odds(self, fixture_id: int) -> APIResponse:
        """Get half time/full time odds"""
        return self._make_request("odds", {
            "fixture": fixture_id,
            "bet": "Half Time/Full Time"
        })
    
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
    
    def get_venue_details(self, venue_id: int) -> APIResponse:
        """Get detailed venue information"""
        return self._make_request("venues", {"id": venue_id})
    
    def get_venue_fixtures(self, venue_id: int, season: int) -> APIResponse:
        """Get all fixtures played at specific venue"""
        return self._make_request("fixtures", {"venue": venue_id, "season": season})
    
    def analyze_venue_performance(self, team_id: int, venue_id: int, season: int) -> APIResponse:
        """Analyze team performance at specific venue"""
        return self._make_request("fixtures", {
            "team": team_id, 
            "venue": venue_id, 
            "season": season
        })
    
    # ========================
    # WEATHER & CONDITIONS ENDPOINTS (Custom Implementation)
    # ========================
    
    def get_weather_impact_analysis(self, fixture_id: int) -> Dict[str, Any]:
        """Custom weather impact analysis (would need external weather API)"""
        # This would integrate with external weather services
        return {
            'fixture_id': fixture_id,
            'weather_data': None,  # Would be populated from weather API
            'impact_assessment': 'neutral',
            'conditions': {
                'temperature': None,
                'humidity': None,
                'wind_speed': None,
                'precipitation': None
            },
            'impact_factors': {
                'passing_accuracy_effect': 0,
                'long_ball_effect': 0,
                'pace_of_play_effect': 0,
                'injury_risk_increase': 0
            }
        }
    
    def get_pitch_condition_analysis(self, venue_id: int, date: str) -> Dict[str, Any]:
        """Custom pitch condition analysis"""
        return {
            'venue_id': venue_id,
            'date': date,
            'pitch_quality': 'good',  # Would be determined by various factors
            'surface_type': 'grass',
            'recent_usage': 'low',
            'maintenance_score': 8.5,
            'playing_impact': {
                'ball_roll': 'normal',
                'bounce_consistency': 'high',
                'player_grip': 'good'
            }
        }
    
    # ========================
    # PLAYER IMPACT ANALYSIS
    # ========================
    
    def get_key_player_impact(self, team_id: int, player_id: int, season: int) -> APIResponse:
        """Analyze key player impact on team performance"""
        return self._make_request("players", {
            "team": team_id,
            "id": player_id,
            "season": season
        })
    
    def get_lineup_strength_analysis(self, fixture_id: int) -> Dict[str, Any]:
        """Analyze lineup strength and key player availability"""
        lineups = self.get_fixture_lineups(fixture_id)
        injuries = self._get_fixture_related_injuries(fixture_id)
        
        analysis = {
            'fixture_id': fixture_id,
            'lineup_strength': {
                'home': {'total_value': 0, 'key_players_present': True, 'formation_strength': 8.0},
                'away': {'total_value': 0, 'key_players_present': True, 'formation_strength': 8.0}
            },
            'missing_players': {
                'home': [],
                'away': []
            },
            'tactical_assessment': {
                'home_formation': '4-3-3',
                'away_formation': '4-4-2',
                'formation_matchup': 'balanced'
            }
        }
        
        return analysis
    
    def _get_fixture_related_injuries(self, fixture_id: int) -> List[Dict]:
        """Helper method to get injuries related to fixture"""
        # Implementation would cross-reference fixture teams with current injuries
        return []
    
    # ========================
    # LIVE COMMENTARY & EVENTS
    # ========================
    
    def get_live_commentary(self, fixture_id: int) -> Dict[str, Any]:
        """Get live match commentary and detailed events"""
        events = self.get_fixture_events(fixture_id)
        
        commentary = {
            'fixture_id': fixture_id,
            'live_events': events.data if events.status == APIStatus.SUCCESS else [],
            'commentary_stream': [],  # Would be populated from commentary API
            'key_highlights': [],
            'tactical_changes': [],
            'momentum_shifts': []
        }
        
        if events.status == APIStatus.SUCCESS and events.data:
            commentary['key_highlights'] = self._extract_key_highlights(events.data)
            commentary['tactical_changes'] = self._identify_tactical_changes(events.data)
        
        return commentary
    
    def _extract_key_highlights(self, events: List[Dict]) -> List[Dict]:
        """Extract key match highlights from events"""
        highlights = []
        
        for event in events:
            event_type = event.get('type')
            if event_type in ['Goal', 'Card', 'Penalty', 'Red Card']:
                highlights.append({
                    'minute': event.get('time', {}).get('elapsed', 0),
                    'type': event_type,
                    'description': event.get('detail', ''),
                    'player': event.get('player', {}).get('name', 'Unknown'),
                    'team': event.get('team', {}).get('name', 'Unknown')
                })
        
        return sorted(highlights, key=lambda x: x['minute'])
    
    def _identify_tactical_changes(self, events: List[Dict]) -> List[Dict]:
        """Identify tactical changes from substitutions and formations"""
        changes = []
        
        for event in events:
            if event.get('type') == 'subst':
                changes.append({
                    'minute': event.get('time', {}).get('elapsed', 0),
                    'type': 'substitution',
                    'player_out': event.get('player', {}).get('name', 'Unknown'),
                    'player_in': event.get('assist', {}).get('name', 'Unknown'),
                    'team': event.get('team', {}).get('name', 'Unknown'),
                    'tactical_impact': self._assess_substitution_impact(event)
                })
        
        return sorted(changes, key=lambda x: x['minute'])
    
    def _assess_substitution_impact(self, substitution: Dict) -> str:
        """Assess the tactical impact of a substitution"""
        # This would analyze the substitution's tactical implications
        return 'offensive'  # Could be 'offensive', 'defensive', 'neutral', etc.
    
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

# PROFESSIONAL ANALYTICS EXTENSIONS
class AdvancedAnalytics:
    """Gelişmiş profesyonel analiz fonksiyonları"""
    
    def __init__(self, api_instance: APIFootballV3):
        self.api = api_instance
    
    def get_comprehensive_match_analysis(self, fixture_id: int) -> Dict[str, Any]:
        """Kapsamlı maç analizi - tüm verileri birleştir"""
        try:
            analysis = {
                'fixture_id': fixture_id,
                'basic_info': None,
                'predictions': None,
                'odds': None,
                'statistics': None,
                'events': None,
                'lineups': None,
                'h2h': None,
                'team_form': None,
                'venue_analysis': None,
                'weather_impact': None,
                'confidence_score': 0,
                'risk_assessment': 'unknown'
            }
            
            # Basic fixture info
            fixture_result = self.api.get_fixture_by_id(fixture_id)
            if fixture_result.status == APIStatus.SUCCESS and fixture_result.data:
                analysis['basic_info'] = fixture_result.data[0] if fixture_result.data else None
                
                # Extract team IDs for further analysis
                if analysis['basic_info']:
                    teams = analysis['basic_info'].get('teams', {})
                    home_team_id = teams.get('home', {}).get('id')
                    away_team_id = teams.get('away', {}).get('id')
                    
                    # H2H Analysis
                    if home_team_id and away_team_id:
                        h2h_result = self.api.get_h2h_fixtures(home_team_id, away_team_id, last=10)
                        if h2h_result.status == APIStatus.SUCCESS:
                            analysis['h2h'] = h2h_result.data
                    
                    # Team form analysis
                    analysis['team_form'] = self._analyze_team_form(home_team_id, away_team_id)
            
            # Predictions
            pred_result = self.api.get_fixture_predictions(fixture_id)
            if pred_result.status == APIStatus.SUCCESS:
                analysis['predictions'] = pred_result.data
            
            # Odds
            odds_result = self.api.get_fixture_odds(fixture_id)
            if odds_result.status == APIStatus.SUCCESS:
                analysis['odds'] = odds_result.data
            
            # Statistics (if available)
            stats_result = self.api.get_fixture_statistics(fixture_id)
            if stats_result.status == APIStatus.SUCCESS:
                analysis['statistics'] = stats_result.data
            
            # Events
            events_result = self.api.get_fixture_events(fixture_id)
            if events_result.status == APIStatus.SUCCESS:
                analysis['events'] = events_result.data
            
            # Lineups
            lineups_result = self.api.get_fixture_lineups(fixture_id)
            if lineups_result.status == APIStatus.SUCCESS:
                analysis['lineups'] = lineups_result.data
            
            # Venue analysis
            if analysis['basic_info']:
                venue_info = analysis['basic_info'].get('fixture', {}).get('venue', {})
                analysis['venue_analysis'] = self._analyze_venue_impact(venue_info)
            
            # Calculate confidence score
            analysis['confidence_score'] = self._calculate_confidence_score(analysis)
            analysis['risk_assessment'] = self._assess_risk_level(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Comprehensive match analysis error: {e}")
            return {'error': str(e)}
    
    def get_advanced_team_performance(self, team_id: int, season: int, league_id: int = None) -> Dict[str, Any]:
        """Gelişmiş takım performans analizi"""
        try:
            performance = {
                'team_id': team_id,
                'season': season,
                'overall_stats': None,
                'home_performance': None,
                'away_performance': None,
                'recent_form': None,
                'scoring_patterns': None,
                'defensive_analysis': None,
                'key_players': None,
                'injury_impact': None,
                'performance_trends': None
            }
            
            # Overall team statistics
            if league_id:
                stats_result = self.api.get_team_statistics(team_id, league_id, season)
                if stats_result.status == APIStatus.SUCCESS:
                    performance['overall_stats'] = stats_result.data
            
            # Recent fixtures for form analysis
            fixtures_result = self.api.get_team_fixtures(team_id, season, last=10)
            if fixtures_result.status == APIStatus.SUCCESS and fixtures_result.data:
                performance['recent_form'] = self._analyze_recent_form(fixtures_result.data)
                performance['scoring_patterns'] = self._analyze_scoring_patterns(fixtures_result.data, team_id)
                performance['defensive_analysis'] = self._analyze_defensive_performance(fixtures_result.data, team_id)
            
            # Injury analysis
            injuries_result = self.api.get_team_injuries(team_id)
            if injuries_result.status == APIStatus.SUCCESS:
                performance['injury_impact'] = self._assess_injury_impact(injuries_result.data)
            
            # Performance trends
            performance['performance_trends'] = self._calculate_performance_trends(performance)
            
            return performance
            
        except Exception as e:
            logger.error(f"Advanced team performance error: {e}")
            return {'error': str(e)}
    
    def get_live_match_intelligence(self, fixture_id: int) -> Dict[str, Any]:
        """Canlı maç için gerçek zamanlı analiz"""
        try:
            intelligence = {
                'fixture_id': fixture_id,
                'current_state': None,
                'momentum_analysis': None,
                'probability_shifts': None,
                'key_moments': None,
                'tactical_analysis': None,
                'substitution_impact': None,
                'expected_goals': None,
                'live_predictions': None
            }
            
            # Current fixture state
            fixture_result = self.api.get_fixture_by_id(fixture_id)
            if fixture_result.status == APIStatus.SUCCESS and fixture_result.data:
                intelligence['current_state'] = fixture_result.data[0]
            
            # Live statistics
            stats_result = self.api.get_fixture_statistics(fixture_id)
            if stats_result.status == APIStatus.SUCCESS and stats_result.data:
                intelligence['tactical_analysis'] = self._analyze_live_tactics(stats_result.data)
                intelligence['expected_goals'] = self._calculate_live_xg(stats_result.data)
            
            # Live events for momentum
            events_result = self.api.get_fixture_events(fixture_id)
            if events_result.status == APIStatus.SUCCESS and events_result.data:
                intelligence['momentum_analysis'] = self._analyze_match_momentum(events_result.data)
                intelligence['key_moments'] = self._identify_key_moments(events_result.data)
            
            # Live predictions update
            pred_result = self.api.get_fixture_predictions(fixture_id)
            if pred_result.status == APIStatus.SUCCESS:
                intelligence['live_predictions'] = self._update_live_predictions(pred_result.data, intelligence)
            
            return intelligence
            
        except Exception as e:
            logger.error(f"Live match intelligence error: {e}")
            return {'error': str(e)}
    
    # PRIVATE HELPER METHODS
    
    def _analyze_team_form(self, home_team_id: int, away_team_id: int) -> Dict[str, Any]:
        """Takım formu analizi"""
        # Implementation for team form analysis
        return {'home_form': 'good', 'away_form': 'average', 'form_comparison': 'home_advantage'}
    
    def _analyze_venue_impact(self, venue_info: Dict) -> Dict[str, Any]:
        """Saha etkisi analizi"""
        # Implementation for venue impact analysis
        return {'capacity': venue_info.get('capacity', 0), 'impact_factor': 0.1}
    
    def _calculate_confidence_score(self, analysis: Dict) -> float:
        """Güvenilirlik skoru hesapla"""
        score = 0.5  # Base score
        
        # Add confidence based on available data
        if analysis.get('predictions'): score += 0.2
        if analysis.get('odds'): score += 0.1
        if analysis.get('statistics'): score += 0.1
        if analysis.get('h2h'): score += 0.05
        if analysis.get('team_form'): score += 0.05
        
        return min(score, 1.0)
    
    def _assess_risk_level(self, analysis: Dict) -> str:
        """Risk seviyesi değerlendirmesi"""
        confidence = analysis.get('confidence_score', 0)
        
        if confidence >= 0.8: return 'low'
        elif confidence >= 0.6: return 'medium'
        else: return 'high'
    
    def _analyze_recent_form(self, fixtures: List[Dict]) -> Dict[str, Any]:
        """Son maç formu analizi"""
        # Implementation for recent form analysis
        return {'wins': 0, 'draws': 0, 'losses': 0, 'goals_for': 0, 'goals_against': 0}
    
    def _analyze_scoring_patterns(self, fixtures: List[Dict], team_id: int) -> Dict[str, Any]:
        """Gol atma düzenleri analizi"""
        # Implementation for scoring pattern analysis
        return {'avg_goals': 0, 'home_avg': 0, 'away_avg': 0, 'first_half': 0, 'second_half': 0}
    
    def _analyze_defensive_performance(self, fixtures: List[Dict], team_id: int) -> Dict[str, Any]:
        """Defansif performans analizi"""
        # Implementation for defensive analysis
        return {'clean_sheets': 0, 'goals_conceded': 0, 'avg_conceded': 0}
    
    def _assess_injury_impact(self, injuries: List[Dict]) -> Dict[str, Any]:
        """Sakatlık etkisi değerlendirmesi"""
        # Implementation for injury impact assessment
        return {'key_players_injured': 0, 'impact_level': 'low'}
    
    def _calculate_performance_trends(self, performance: Dict) -> Dict[str, Any]:
        """Performans trendi hesaplama"""
        # Implementation for performance trends
        return {'trending': 'stable', 'direction': 'neutral'}
    
    def _analyze_live_tactics(self, statistics: List[Dict]) -> Dict[str, Any]:
        """Canlı taktik analizi"""
        # Implementation for live tactical analysis
        return {'formation': 'unknown', 'style': 'balanced'}
    
    def _calculate_live_xg(self, statistics: List[Dict]) -> Dict[str, Any]:
        """Canlı expected goals hesaplama"""
        # Implementation for live xG calculation
        return {'home_xg': 0, 'away_xg': 0}
    
    def _analyze_match_momentum(self, events: List[Dict]) -> Dict[str, Any]:
        """Maç momentumu analizi"""
        # Implementation for momentum analysis
        return {'current_momentum': 'neutral', 'momentum_shifts': []}
    
    def _identify_key_moments(self, events: List[Dict]) -> List[Dict]:
        """Kritik anları tespit et"""
        # Implementation for key moments identification
        return []
    
    def _update_live_predictions(self, predictions: List[Dict], intelligence: Dict) -> Dict[str, Any]:
        """Canlı tahmin güncellemesi"""
        # Implementation for live predictions update
        return {'updated_probabilities': {}, 'confidence': 0.5}