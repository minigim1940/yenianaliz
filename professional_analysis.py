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

    def coaches_dashboard(self):
        """Antrenör yönetimi dashboard'u"""
        st.header("👨‍💼 Antrenör Yönetimi")
        
        # Arama seçenekleri
        search_type = st.selectbox(
            "Arama Türü",
            ["Takım ID ile", "İsim ile Arama"],
            key="coach_search_type"
        )
        
        if search_type == "Takım ID ile":
            team_id = st.number_input("Takım ID girin:", min_value=1, key="coach_team_id")
            
            if st.button("🔍 Antrenörü Bul", key="find_coach_by_team"):
                with st.spinner("Antrenör aranıyor..."):
                    result = self.api.get_coaches(team_id=team_id)
                    
                    if result.status == APIStatus.SUCCESS and result.data:
                        for coach in result.data:
                            coach_info = coach
                            
                            col1, col2, col3 = st.columns([1, 2, 1])
                            
                            with col1:
                                photo_url = coach_info.get('photo')
                                if photo_url:
                                    st.image(photo_url, width=100)
                            
                            with col2:
                                st.subheader(f"👨‍💼 {coach_info.get('name', 'Bilinmiyor')}")
                                st.write(f"**📅 Yaş:** {coach_info.get('age', 'N/A')}")
                                st.write(f"**🌍 Uyruk:** {coach_info.get('nationality', 'N/A')}")
                                
                                birth = coach_info.get('birth', {})
                                if birth:
                                    st.write(f"**🎂 Doğum:** {birth.get('date', 'N/A')}")
                                    st.write(f"**📍 Doğum Yeri:** {birth.get('place', 'N/A')}, {birth.get('country', 'N/A')}")
                            
                            with col3:
                                st.write(f"**📏 Boy:** {coach_info.get('height', 'N/A')}")
                                st.write(f"**⚖️ Kilo:** {coach_info.get('weight', 'N/A')}")
                    else:
                        st.error("❌ Antrenör bulunamadı")
        
        else:  # İsim ile arama
            coach_name = st.text_input("Antrenör adını girin:", key="coach_search_name")
            
            if st.button("🔍 Antrenör Ara", key="search_coach_by_name") and coach_name:
                with st.spinner(f"{coach_name} aranıyor..."):
                    result = self.api.get_coaches(search=coach_name)
                    
                    if result.status == APIStatus.SUCCESS and result.data:
                        st.success(f"✅ {len(result.data)} antrenör bulundu")
                        
                        for idx, coach in enumerate(result.data, 1):
                            with st.expander(f"👨‍💼 {coach.get('name', f'Antrenör {idx}')}", expanded=(idx==1)):
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    photo_url = coach.get('photo')
                                    if photo_url:
                                        st.image(photo_url, width=150)
                                    
                                    st.write(f"**📅 Yaş:** {coach.get('age', 'N/A')}")
                                    st.write(f"**🌍 Uyruk:** {coach.get('nationality', 'N/A')}")
                                
                                with col2:
                                    birth = coach.get('birth', {})
                                    if birth:
                                        st.write(f"**🎂 Doğum Tarihi:** {birth.get('date', 'N/A')}")
                                        st.write(f"**📍 Doğum Yeri:** {birth.get('place', 'N/A')}")
                                        st.write(f"**🏴 Ülke:** {birth.get('country', 'N/A')}")
                                    
                                    st.write(f"**📏 Boy:** {coach.get('height', 'N/A')}")
                                    st.write(f"**⚖️ Kilo:** {coach.get('weight', 'N/A')}")
                    else:
                        st.error("❌ Antrenör bulunamadı")

    def venues_dashboard(self):
        """Stad yönetimi dashboard'u"""
        st.header("🏟️ Stad Yönetimi")
        
        # Arama seçenekleri
        search_type = st.selectbox(
            "Arama Türü",
            ["Stad ID ile", "İsim ile", "Şehir ile", "Ülke ile"],
            key="venue_search_type"
        )
        
        if search_type == "Stad ID ile":
            venue_id = st.number_input("Stad ID girin:", min_value=1, key="venue_id_input")
            
            if st.button("🔍 Stadı Bul", key="find_venue_by_id"):
                with st.spinner("Stad aranıyor..."):
                    result = self.api.get_venues(venue_id=venue_id)
                    self._display_venues(result)
        
        elif search_type == "İsim ile":
            venue_name = st.text_input("Stad adını girin:", key="venue_name_input")
            
            if st.button("🔍 Stad Ara", key="search_venue_by_name") and venue_name:
                with st.spinner(f"{venue_name} aranıyor..."):
                    result = self.api.get_venues(name=venue_name)
                    self._display_venues(result)
        
        elif search_type == "Şehir ile":
            city_name = st.text_input("Şehir adını girin:", key="venue_city_input")
            
            if st.button("🏙️ Şehirdeki Stadları Bul", key="search_venue_by_city") and city_name:
                with st.spinner(f"{city_name} stadları aranıyor..."):
                    result = self.api.get_venues(city=city_name)
                    self._display_venues(result)
        
        else:  # Ülke ile
            country_name = st.text_input("Ülke adını girin:", key="venue_country_input")
            
            if st.button("🌍 Ülkedeki Stadları Bul", key="search_venue_by_country") and country_name:
                with st.spinner(f"{country_name} stadları aranıyor..."):
                    result = self.api.get_venues(country=country_name)
                    self._display_venues(result)

    def _display_venues(self, result: APIResponse):
        """Stad sonuçlarını görüntüle"""
        if result.status == APIStatus.SUCCESS and result.data:
            st.success(f"✅ {len(result.data)} stad bulundu")
            
            for idx, venue in enumerate(result.data, 1):
                with st.expander(f"🏟️ {venue.get('name', f'Stad {idx}')}", expanded=(idx==1)):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        venue_image = venue.get('image')
                        if venue_image:
                            st.image(venue_image, use_column_width=True)
                        else:
                            st.info("📷 Resim mevcut değil")
                    
                    with col2:
                        st.write(f"**🆔 ID:** {venue.get('id', 'N/A')}")
                        st.write(f"**📍 Adres:** {venue.get('address', 'N/A')}")
                        st.write(f"**🏙️ Şehir:** {venue.get('city', 'N/A')}")
                        st.write(f"**🌍 Ülke:** {venue.get('country', 'N/A')}")
                        st.write(f"**👥 Kapasite:** {venue.get('capacity', 'N/A'):,}")
                        st.write(f"**🌿 Zemin:** {venue.get('surface', 'N/A')}")
        else:
            st.error("❌ Stad bulunamadı")

    def predictions_dashboard(self):
        """Tahmin dashboard'u"""
        st.header("🔮 Maç Tahminleri")
        
        fixture_id = st.number_input("Maç ID girin:", min_value=1, key="prediction_fixture_id")
        
        if st.button("🔮 Tahmin Al", key="get_prediction"):
            with st.spinner("Tahmin alınıyor..."):
                result = self.api.get_predictions(fixture_id)
                
                if result.status == APIStatus.SUCCESS and result.data:
                    prediction_data = result.data[0] if result.data else None
                    
                    if prediction_data:
                        # Genel tahmin bilgileri
                        st.subheader("🎯 Genel Tahmin")
                        
                        predictions = prediction_data.get('predictions', {})
                        
                        # Kazanan tahmini
                        winner = predictions.get('winner', {})
                        if winner:
                            st.success(f"🏆 **Kazanan Tahmini:** {winner.get('name', 'Bilinmiyor')}")
                            st.info(f"💬 **Yorum:** {winner.get('comment', 'Yorum yok')}")
                        
                        # Yüzde tahminleri
                        percent = predictions.get('percent', {})
                        if percent:
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.metric("🏠 Ev Sahibi", f"{percent.get('home', 0)}%")
                            with col2:
                                st.metric("🤝 Beraberlik", f"{percent.get('draw', 0)}%")
                            with col3:
                                st.metric("✈️ Deplasman", f"{percent.get('away', 0)}%")
                        
                        # Gol tahminleri
                        goals = predictions.get('goals', {})
                        if goals:
                            st.subheader("⚽ Gol Tahminleri")
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write(f"🏠 **Ev Sahibi Gol:** {goals.get('home', 'N/A')}")
                            with col2:
                                st.write(f"✈️ **Deplasman Gol:** {goals.get('away', 'N/A')}")
                        
                        # Öneriler
                        advice = predictions.get('advice', 'Tavsiye mevcut değil')
                        st.subheader("💡 Tavsiye")
                        st.info(advice)
                
                else:
                    st.error("❌ Tahmin alınamadı")

    def odds_dashboard(self):
        """Bahis oranları dashboard'u"""
        st.header("💰 Bahis Oranları")
        
        # Arama türü seçimi
        search_type = st.selectbox(
            "Arama Türü",
            ["Maç ID ile", "Lig ile", "Tarih ile"],
            key="odds_search_type"
        )
        
        if search_type == "Maç ID ile":
            fixture_id = st.number_input("Maç ID girin:", min_value=1, key="odds_fixture_id")
            
            if st.button("💰 Oranları Al", key="get_odds_by_fixture"):
                with st.spinner("Oranlar alınıyor..."):
                    result = self.api.get_odds(fixture_id=fixture_id)
                    self._display_odds(result)
        
        elif search_type == "Lig ile":
            col1, col2 = st.columns(2)
            
            with col1:
                league_id = st.number_input("Lig ID girin:", min_value=1, key="odds_league_id")
            with col2:
                season = st.number_input("Sezon girin:", min_value=2000, max_value=2025, 
                                       value=2024, key="odds_season")
            
            if st.button("💰 Lig Oranlarını Al", key="get_odds_by_league"):
                with st.spinner("Lig oranları alınıyor..."):
                    result = self.api.get_odds(league_id=league_id, season=season)
                    self._display_odds(result)
        
        else:  # Tarih ile
            date_input = st.date_input("Tarih seçin:", key="odds_date_input")
            
            if st.button("💰 Günün Oranlarını Al", key="get_odds_by_date"):
                date_str = date_input.strftime("%Y-%m-%d")
                with st.spinner(f"{date_str} oranları alınıyor..."):
                    result = self.api.get_odds(date_str=date_str)
                    self._display_odds(result)
        
        # Bookmaker ve bet türlerini göster
        st.subheader("📊 Mevcut Bookmaker'lar ve Bahis Türleri")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📚 Bookmaker'ları Görüntüle", key="show_bookmakers"):
                with st.spinner("Bookmaker'lar alınıyor..."):
                    result = self.api.get_odds_bookmakers()
                    if result.status == APIStatus.SUCCESS and result.data:
                        st.subheader("📚 Bookmaker'lar")
                        for bookmaker in result.data[:10]:  # İlk 10 tanesi
                            st.write(f"- **{bookmaker.get('name', 'N/A')}** (ID: {bookmaker.get('id', 'N/A')})")
        
        with col2:
            if st.button("🎲 Bahis Türlerini Görüntüle", key="show_bet_types"):
                with st.spinner("Bahis türleri alınıyor..."):
                    result = self.api.get_odds_bets()
                    if result.status == APIStatus.SUCCESS and result.data:
                        st.subheader("🎲 Bahis Türleri")
                        for bet in result.data[:10]:  # İlk 10 tanesi
                            st.write(f"- **{bet.get('name', 'N/A')}** (ID: {bet.get('id', 'N/A')})")

    def _display_odds(self, result: APIResponse):
        """Bahis oranlarını görüntüle"""
        if result.status == APIStatus.SUCCESS and result.data:
            st.success(f"✅ {len(result.data)} maç için oran bulundu")
            
            for idx, fixture_odds in enumerate(result.data[:5], 1):  # İlk 5 maç
                fixture = fixture_odds.get('fixture', {})
                bookmakers = fixture_odds.get('bookmakers', [])
                
                with st.expander(f"⚽ Maç {idx}: {fixture.get('id', 'N/A')}", expanded=(idx==1)):
                    if bookmakers:
                        for bookmaker in bookmakers[:3]:  # İlk 3 bookmaker
                            st.write(f"**📚 {bookmaker.get('name', 'Bookmaker')}**")
                            
                            bets = bookmaker.get('bets', [])
                            for bet in bets:
                                bet_name = bet.get('name', 'Bahis')
                                values = bet.get('values', [])
                                
                                if values:
                                    st.write(f"🎲 **{bet_name}:**")
                                    for value in values[:3]:  # İlk 3 değer
                                        st.write(f"  - {value.get('value', 'N/A')}: {value.get('odd', 'N/A')}")
                    else:
                        st.warning("Bu maç için oran bulunmuyor")
        else:
            st.error("❌ Oran bulunamadı")

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