"""
Professional Football Analysis Engine
====================================

Gelişmiş futbol analiz motoru - API v3 ile tam entegre
Tüm modern analiz özelliklerini içerir
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date, timedelta
from football_api_v3 import APIFootballV3, APIStatus, APIResponse
import streamlit as st
from dataclasses import dataclass
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

@dataclass
class MatchAnalysisResult:
    """Comprehensive match analysis result"""
    teams: Dict[str, Any]
    statistics: Dict[str, Any]
    h2h_data: Dict[str, Any] 
    predictions: Dict[str, Any]
    injuries: Dict[str, Any]
    form: Dict[str, Any]
    odds: Dict[str, Any]
    venues: Dict[str, Any]
    
class ProfessionalAnalysisEngine:
    """Professional football analysis engine using API v3"""
    
    def __init__(self, api: APIFootballV3):
        self.api = api
        self.current_season = api.get_current_season()
        self._timezones_cache = None
        self._countries_cache = None
    
    def comprehensive_team_analysis(self, team_name: str, 
                                   league_id: Optional[int] = None,
                                   season: Optional[int] = None) -> Optional[Dict]:
        """
        Kapsamlı takım analizi
        """
        season = season or self.current_season
        
        st.info(f"🔍 {team_name} takımı analiz ediliyor...")
        
        # 1. Takımı bul
        team_result = self.api.search_teams(team_name, league_id, season)
        if team_result.status != APIStatus.SUCCESS or not team_result.data:
            st.error(f"❌ '{team_name}' takımı bulunamadı")
            return None
        
        team_data = team_result.data[0]['team']
        team_id = team_data['id']
        
        st.success(f"✅ Takım bulundu: {team_data['name']}")
        
        analysis = {
            'team': team_data,
            'statistics': {},
            'fixtures': {},
            'squad': {},
            'injuries': {},
            'transfers': {},
            'venue': {},
            'trophies': {}
        }
        
        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # 2. Takım istatistikleri
            status_text.text("📊 İstatistikler alınıyor...")
            if league_id:
                stats_result = self.api.get_team_statistics(team_id, league_id, season)
                if stats_result.status == APIStatus.SUCCESS and stats_result.data:
                    analysis['statistics'] = stats_result.data
            progress_bar.progress(20)
            
            # 3. Son maçlar ve gelecek maçlar
            status_text.text("⚽ Maç programı alınıyor...")
            fixtures_result = self.api.get_team_fixtures(team_id, season, league_id, last=5, next=5)
            if fixtures_result.status == APIStatus.SUCCESS:
                analysis['fixtures'] = fixtures_result.data
            progress_bar.progress(40)
            
            # 4. Kadro bilgileri
            status_text.text("👥 Kadro bilgileri alınıyor...")
            squad_result = self.api.get_team_squad(team_id)
            if squad_result.status == APIStatus.SUCCESS:
                analysis['squad'] = squad_result.data
            progress_bar.progress(60)
            
            # 5. Sakatlıklar
            status_text.text("🚑 Sakatlık bilgileri alınıyor...")
            injuries_result = self.api.get_team_injuries(team_id, league_id, season)
            if injuries_result.status == APIStatus.SUCCESS:
                analysis['injuries'] = injuries_result.data
            progress_bar.progress(80)
            
            # 6. Stadyum bilgileri
            status_text.text("🏟️ Stadyum bilgileri alınıyor...")
            venue_result = self.api.get_team_venue(team_id)
            if venue_result.status == APIStatus.SUCCESS:
                analysis['venue'] = venue_result.data
            progress_bar.progress(90)
            
            # 7. Kupalar
            status_text.text("🏆 Kupa bilgileri alınıyor...")
            trophies_result = self.api.get_team_trophies(team_id)
            if trophies_result.status == APIStatus.SUCCESS:
                analysis['trophies'] = trophies_result.data
            progress_bar.progress(100)
            
            status_text.text("✅ Analiz tamamlandı!")
            
        except Exception as e:
            st.error(f"❌ Analiz sırasında hata: {str(e)}")
            
        finally:
            progress_bar.empty()
            status_text.empty()
        
        return analysis
    
    def match_prediction_analysis(self, team1_name: str, team2_name: str,
                                 fixture_id: Optional[int] = None) -> Optional[MatchAnalysisResult]:
        """
        İki takım arası detaylı maç analizi ve tahmini
        """
        st.info(f"🥊 {team1_name} vs {team2_name} maç analizi yapılıyor...")
        
        # Takımları bul
        team1_result = self.api.search_teams(team1_name, season=self.current_season)
        team2_result = self.api.search_teams(team2_name, season=self.current_season)
        
        if (team1_result.status != APIStatus.SUCCESS or not team1_result.data or
            team2_result.status != APIStatus.SUCCESS or not team2_result.data):
            st.error("❌ Takımlardan biri bulunamadı")
            return None
        
        team1_data = team1_result.data[0]['team']
        team2_data = team2_result.data[0]['team']
        
        analysis_data = {
            'teams': {'home': team1_data, 'away': team2_data},
            'statistics': {},
            'h2h_data': {},
            'predictions': {},
            'injuries': {},
            'form': {},
            'odds': {},
            'venues': {}
        }
        
        # Progress tracking
        progress = st.progress(0)
        status = st.empty()
        
        try:
            # H2H data
            status.text("🔄 Karşılaşma geçmişi alınıyor...")
            h2h_result = self.api.get_h2h_fixtures(team1_data['id'], team2_data['id'], 10)
            if h2h_result.status == APIStatus.SUCCESS:
                analysis_data['h2h_data'] = h2h_result.data
            progress.progress(25)
            
            # Team injuries
            status.text("🚑 Sakatlık durumları kontrol ediliyor...")
            team1_injuries = self.api.get_team_injuries(team1_data['id'])
            team2_injuries = self.api.get_team_injuries(team2_data['id'])
            analysis_data['injuries'] = {
                'team1': team1_injuries.data if team1_injuries.status == APIStatus.SUCCESS else [],
                'team2': team2_injuries.data if team2_injuries.status == APIStatus.SUCCESS else []
            }
            progress.progress(50)
            
            # Recent form
            status.text("📈 Son dönem performansları analiz ediliyor...")
            team1_recent = self.api.get_team_fixtures(team1_data['id'], self.current_season, last=10)
            team2_recent = self.api.get_team_fixtures(team2_data['id'], self.current_season, last=10)
            analysis_data['form'] = {
                'team1': team1_recent.data if team1_recent.status == APIStatus.SUCCESS else [],
                'team2': team2_recent.data if team2_recent.status == APIStatus.SUCCESS else []
            }
            progress.progress(75)
            
            # Predictions if fixture_id available
            if fixture_id:
                status.text("🔮 AI tahminleri alınıyor...")
                pred_result = self.api.get_fixture_predictions(fixture_id)
                if pred_result.status == APIStatus.SUCCESS:
                    analysis_data['predictions'] = pred_result.data
                
                # Odds data
                odds_result = self.api.get_fixture_odds(fixture_id)
                if odds_result.status == APIStatus.SUCCESS:
                    analysis_data['odds'] = odds_result.data
            
            progress.progress(100)
            status.text("✅ Analiz tamamlandı!")
            
        except Exception as e:
            st.error(f"❌ Analiz hatası: {str(e)}")
            return None
            
        finally:
            progress.empty()
            status.empty()
        
        return MatchAnalysisResult(**analysis_data)
    
    def live_matches_dashboard(self) -> None:
        """Canlı maçlar dashboard'u"""
        st.subheader("🔴 Canlı Maçlar")
        
        live_result = self.api.get_live_fixtures()
        
        if live_result.status != APIStatus.SUCCESS:
            st.error(f"❌ Canlı maçlar alınamadı: {live_result.error}")
            return
        
        if not live_result.data:
            st.info("ℹ️ Şu anda canlı maç bulunmuyor")
            return
        
        # Live matches in cards
        for fixture in live_result.data[:10]:  # Limit to 10 matches
            with st.expander(
                f"🔴 {fixture['teams']['home']['name']} {fixture['goals']['home']} - "
                f"{fixture['goals']['away']} {fixture['teams']['away']['name']} "
                f"({fixture['fixture']['status']['elapsed']}')", 
                expanded=True
            ):
                col1, col2, col3 = st.columns([2, 1, 2])
                
                with col1:
                    st.image(fixture['teams']['home']['logo'], width=60)
                    st.write(f"**{fixture['teams']['home']['name']}**")
                
                with col2:
                    st.markdown(f"### {fixture['goals']['home']} - {fixture['goals']['away']}")
                    st.write(f"{fixture['fixture']['status']['elapsed']}'")
                
                with col3:
                    st.image(fixture['teams']['away']['logo'], width=60) 
                    st.write(f"**{fixture['teams']['away']['name']}**")
                
                # Get live statistics if available
                stats_result = self.api.get_fixture_statistics(fixture['fixture']['id'])
                if stats_result.status == APIStatus.SUCCESS and stats_result.data:
                    self._display_live_statistics(stats_result.data)
    
    def league_analysis_dashboard(self, league_id: int, season: Optional[int] = None) -> None:
        """Lig analiz dashboard'u"""
        season = season or self.current_season
        
        st.subheader(f"🏆 Lig Analizi - {season} Sezonu")
        
        # League standings
        standings_result = self.api.get_league_standings(league_id, season)
        
        if standings_result.status != APIStatus.SUCCESS:
            st.error(f"❌ Lig bilgileri alınamadı: {standings_result.error}")
            return
        
        if not standings_result.data:
            st.warning("⚠️ Lig verileri bulunamadı")
            return
        
        # Display standings table
        standings = standings_result.data[0]['league']['standings'][0]
        
        standings_df = pd.DataFrame([
            {
                'Sıra': team['rank'],
                'Takım': team['team']['name'],
                'O': team['all']['played'],
                'G': team['all']['win'],
                'B': team['all']['draw'], 
                'M': team['all']['lose'],
                'AG': team['all']['goals']['for'],
                'YG': team['all']['goals']['against'],
                'AV': team['goalsDiff'],
                'P': team['points']
            }
            for team in standings
        ])
        
        st.dataframe(standings_df, use_container_width=True)
        
        # Top scorers
        scorers_result = self.api.get_top_scorers(league_id, season)
        if scorers_result.status == APIStatus.SUCCESS and scorers_result.data:
            st.subheader("⚽ En İyi Golcüler")
            
            scorers_df = pd.DataFrame([
                {
                    'Oyuncu': player['player']['name'],
                    'Takım': player['statistics'][0]['team']['name'],
                    'Gol': player['statistics'][0]['goals']['total'],
                    'Maç': player['statistics'][0]['games']['appearences']
                }
                for player in scorers_result.data[:10]
            ])
            
            st.dataframe(scorers_df, use_container_width=True)
    
    def player_analysis_dashboard(self, player_name: str, 
                                 season: Optional[int] = None) -> None:
        """Oyuncu analiz dashboard'u"""
        season = season or self.current_season
        
        st.subheader(f"👤 Oyuncu Analizi: {player_name}")
        
        # Search player
        player_result = self.api.search_players(player_name, season=season)
        
        if player_result.status != APIStatus.SUCCESS:
            st.error(f"❌ Oyuncu bulunamadı: {player_result.error}")
            return
        
        if not player_result.data:
            st.warning(f"⚠️ '{player_name}' oyuncusu bulunamadı")
            return
        
        player_data = player_result.data[0]['player']
        stats = player_result.data[0]['statistics'][0] if player_result.data[0].get('statistics') else {}
        
        # Player info
        col1, col2 = st.columns([1, 2])
        
        with col1:
            if player_data.get('photo'):
                st.image(player_data['photo'], width=150)
        
        with col2:
            st.write(f"**Ad:** {player_data['name']}")
            st.write(f"**Yaş:** {player_data.get('age', 'Bilinmiyor')}")
            st.write(f"**Boy:** {player_data.get('height', 'Bilinmiyor')}")
            st.write(f"**Kilo:** {player_data.get('weight', 'Bilinmiyor')}")
            st.write(f"**Pozisyon:** {stats.get('games', {}).get('position', 'Bilinmiyor')}")
        
        # Statistics
        if stats:
            st.subheader("📊 İstatistikler")
            
            stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
            
            with stats_col1:
                st.metric("Maç", stats.get('games', {}).get('appearences', 0))
                st.metric("Gol", stats.get('goals', {}).get('total', 0))
            
            with stats_col2:
                st.metric("Asist", stats.get('goals', {}).get('assists', 0))
                st.metric("Sarı Kart", stats.get('cards', {}).get('yellow', 0))
            
            with stats_col3:
                st.metric("Kırmızı Kart", stats.get('cards', {}).get('red', 0))
                st.metric("Oynanan Dakika", stats.get('games', {}).get('minutes', 0))
            
            with stats_col4:
                st.metric("Penaltı Golü", stats.get('penalty', {}).get('scored', 0))
                st.metric("Kaçırılan Penaltı", stats.get('penalty', {}).get('missed', 0))
    
    def _display_live_statistics(self, statistics: List[Dict]) -> None:
        """Display live match statistics"""
        if len(statistics) != 2:
            return
            
        home_stats = statistics[0]
        away_stats = statistics[1]
        
        # Create comparison chart
        stats_to_show = [
            ('Şut', 'Total Shots'),
            ('İsabetli Şut', 'Shots on Goal'), 
            ('Topa Sahip Olma', 'Ball Possession'),
            ('Pas', 'Total passes'),
            ('Faul', 'Fouls')
        ]
        
        for stat_name, stat_key in stats_to_show:
            if (home_stats['statistics'] and away_stats['statistics'] and
                any(s['type'] == stat_key for s in home_stats['statistics']) and
                any(s['type'] == stat_key for s in away_stats['statistics'])):
                
                home_val = next((s['value'] for s in home_stats['statistics'] if s['type'] == stat_key), 0)
                away_val = next((s['value'] for s in away_stats['statistics'] if s['type'] == stat_key), 0)
                
                # Handle percentage values
                if '%' in str(home_val):
                    home_val = int(str(home_val).replace('%', ''))
                    away_val = int(str(away_val).replace('%', ''))
                
                col1, col2, col3 = st.columns([2, 1, 2])
                with col1:
                    st.write(f"{home_val}")
                with col2:
                    st.write(f"**{stat_name}**")
                with col3:
                    st.write(f"{away_val}")
    
    def timezone_management_dashboard(self) -> None:
        """Timezone yönetimi dashboard'u"""
        st.subheader("🌍 Timezone Yönetimi")
        
        # Get available timezones
        if not self._timezones_cache:
            with st.spinner("⏰ Timezone bilgileri alınıyor..."):
                timezone_result = self.api.get_timezones()
                
                if timezone_result.status == APIStatus.SUCCESS:
                    self._timezones_cache = timezone_result.data
                else:
                    st.error(f"❌ Timezone bilgileri alınamadı: {timezone_result.error}")
                    return
        
        if self._timezones_cache:
            # Timezone selection
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Group timezones by continent
                timezone_groups = {}
                for tz in self._timezones_cache:
                    if '/' in tz:
                        continent = tz.split('/')[0]
                        if continent not in timezone_groups:
                            timezone_groups[continent] = []
                        timezone_groups[continent].append(tz)
                
                selected_continent = st.selectbox(
                    "🌍 Kıta Seçin:",
                    list(timezone_groups.keys()),
                    index=list(timezone_groups.keys()).index('Europe') if 'Europe' in timezone_groups else 0
                )
                
                if selected_continent:
                    selected_timezone = st.selectbox(
                        "⏰ Timezone Seçin:",
                        timezone_groups[selected_continent],
                        index=timezone_groups[selected_continent].index('Europe/Istanbul') 
                        if selected_continent == 'Europe' and 'Europe/Istanbul' in timezone_groups[selected_continent] else 0
                    )
                    
                    if selected_timezone:
                        st.success(f"✅ Seçilen Timezone: **{selected_timezone}**")
                        
                        # Store in session state for future use
                        st.session_state['selected_timezone'] = selected_timezone
            
            with col2:
                st.info("""
                **Timezone Kullanım Alanları:**
                - Maç saatlerini yerel saate çevirmek
                - Canlı maç takibi
                - Fixture programları
                - Tarihsel maç analizleri
                """)
        
        # Show current timezone info
        if 'selected_timezone' in st.session_state:
            st.subheader("🕐 Timezone Bilgileri")
            
            current_tz = st.session_state['selected_timezone']
            current_time = datetime.now()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Seçili Timezone", current_tz)
            
            with col2:
                st.metric("Şu Anki Saat", current_time.strftime("%H:%M:%S"))
            
            with col3:
                st.metric("Tarih", current_time.strftime("%d.%m.%Y"))
    
    def countries_dashboard(self) -> None:
        """Ülkeler dashboard'u"""
        st.subheader("🌎 Ülkeler ve Ligler")
        
        # Get countries if not cached
        if not self._countries_cache:
            with st.spinner("🌎 Ülke bilgileri alınıyor..."):
                countries_result = self.api.get_countries()
                
                if countries_result.status == APIStatus.SUCCESS:
                    self._countries_cache = countries_result.data
                else:
                    st.error(f"❌ Ülke bilgileri alınamadı: {countries_result.error}")
                    return
        
        if self._countries_cache:
            # Search functionality
            search_term = st.text_input("🔍 Ülke Ara:", placeholder="Örn: Turkey, England, Spain")
            
            # Filter countries
            filtered_countries = self._countries_cache
            if search_term:
                filtered_countries = [
                    country for country in self._countries_cache
                    if search_term.lower() in country.get('name', '').lower()
                ]
            
            # Display countries in a nice grid
            cols_per_row = 4
            countries_to_show = filtered_countries[:20]  # Limit to 20
            
            for i in range(0, len(countries_to_show), cols_per_row):
                cols = st.columns(cols_per_row)
                
                for j in range(cols_per_row):
                    if i + j < len(countries_to_show):
                        country = countries_to_show[i + j]
                        
                        with cols[j]:
                            # Country card
                            if country.get('flag'):
                                st.image(country['flag'], width=60)
                            
                            st.write(f"**{country.get('name', 'Bilinmiyor')}**")
                            st.write(f"Kod: {country.get('code', 'N/A')}")
                            
                            # Button to get leagues for this country
                            if st.button(f"Ligleri Gör", key=f"country_{country.get('code', i)}"):
                                self._show_country_leagues(country.get('name', ''))
            
            # Show total count
            st.info(f"📊 Toplam {len(self._countries_cache)} ülke mevcut. "
                   f"Gösterilen: {len(countries_to_show)}")
    
    def _show_country_leagues(self, country_name: str) -> None:
        """Belirli bir ülkenin liglerini göster"""
        with st.spinner(f"🏆 {country_name} ligları alınıyor..."):
            leagues_result = self.api.get_all_leagues(country=country_name)
            
            if leagues_result.status == APIStatus.SUCCESS and leagues_result.data:
                st.subheader(f"🏆 {country_name} Ligleri")
                
                leagues_data = []
                for league in leagues_result.data:
                    league_info = league.get('league', {})
                    leagues_data.append({
                        'Lig': league_info.get('name', 'Bilinmiyor'),
                        'Tür': league_info.get('type', 'Bilinmiyor'),
                        'ID': league_info.get('id', 'N/A')
                    })
                
                if leagues_data:
                    df = pd.DataFrame(leagues_data)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.warning(f"❌ {country_name} için lig bulunamadı")
            else:
                st.error(f"❌ {country_name} ligleri alınamadı")

# Global analysis engine instance
analysis_engine: Optional[ProfessionalAnalysisEngine] = None

def initialize_analysis_engine(api: APIFootballV3) -> ProfessionalAnalysisEngine:
    """Initialize global analysis engine"""
    global analysis_engine
    analysis_engine = ProfessionalAnalysisEngine(api)
    return analysis_engine

def get_analysis_engine() -> Optional[ProfessionalAnalysisEngine]:
    """Get global analysis engine instance"""
    return analysis_engine