"""
Enhanced display functions for professional analysis
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime

def display_comprehensive_team_analysis(analysis: Dict[str, Any]) -> None:
    """Display comprehensive team analysis with modern UI"""
    
    team_data = analysis['team']
    statistics = analysis.get('statistics', {})
    fixtures = analysis.get('fixtures', [])
    squad = analysis.get('squad', [])
    injuries = analysis.get('injuries', [])
    venue = analysis.get('venue', [])
    trophies = analysis.get('trophies', [])
    
    # Team Header
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if team_data.get('logo'):
            st.image(team_data['logo'], width=120)
        st.markdown(f"<h1 style='text-align: center'>{team_data['name']}</h1>", unsafe_allow_html=True)
        if team_data.get('country'):
            st.markdown(f"<p style='text-align: center'>{team_data['country']} | Kuruluş: {team_data.get('founded', 'Bilinmiyor')}</p>", unsafe_allow_html=True)
    
    # Tabs for different sections
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 İstatistikler", "⚽ Maçlar", "👥 Kadro", 
        "🚑 Sakatlıklar", "🏟️ Stadyum", "🏆 Kupalar"
    ])
    
    with tab1:
        display_team_statistics(statistics)
    
    with tab2:
        display_team_fixtures(fixtures)
    
    with tab3:
        display_team_squad(squad)
    
    with tab4:
        display_team_injuries(injuries)
    
    with tab5:
        display_team_venue(venue, team_data)
    
    with tab6:
        display_team_trophies(trophies)

def display_team_statistics(statistics: Dict[str, Any]) -> None:
    """Display team statistics with charts"""
    
    if not statistics:
        st.info("📊 Bu sezon için istatistik verisi bulunamadı")
        return
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    fixtures_data = statistics.get('fixtures', {})
    goals_data = statistics.get('goals', {})
    
    with col1:
        played = fixtures_data.get('played', {}).get('total', 0)
        st.metric("Oynanan Maç", played)
        
    with col2:
        wins = fixtures_data.get('wins', {}).get('total', 0)
        win_percentage = (wins / played * 100) if played > 0 else 0
        st.metric("Galibiyet", f"{wins} (%{win_percentage:.1f})")
    
    with col3:
        goals_for = goals_data.get('for', {}).get('total', {}).get('total', 0)
        st.metric("Atılan Gol", goals_for)
    
    with col4:
        goals_against = goals_data.get('against', {}).get('total', {}).get('total', 0)
        st.metric("Yenilen Gol", goals_against)
    
    # Performance charts
    if fixtures_data:
        st.subheader("📈 Performans Dağılımı")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Win/Draw/Loss pie chart
            wins = fixtures_data.get('wins', {}).get('total', 0)
            draws = fixtures_data.get('draws', {}).get('total', 0)
            loses = fixtures_data.get('loses', {}).get('total', 0)
            
            if wins + draws + loses > 0:
                fig_pie = px.pie(
                    values=[wins, draws, loses],
                    names=['Galibiyet', 'Beraberlik', 'Mağlubiyet'],
                    colors=['green', 'orange', 'red'],
                    title="Maç Sonuçları Dağılımı"
                )
                st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Home vs Away performance
            home_wins = fixtures_data.get('wins', {}).get('home', 0)
            away_wins = fixtures_data.get('wins', {}).get('away', 0)
            home_draws = fixtures_data.get('draws', {}).get('home', 0)
            away_draws = fixtures_data.get('draws', {}).get('away', 0)
            
            fig_bar = go.Figure(data=[
                go.Bar(name='Ev Sahibi', x=['Galibiyet', 'Beraberlik'], y=[home_wins, home_draws]),
                go.Bar(name='Deplasman', x=['Galibiyet', 'Beraberlik'], y=[away_wins, away_draws])
            ])
            fig_bar.update_layout(title="Ev Sahibi vs Deplasman Performansı")
            st.plotly_chart(fig_bar, use_container_width=True)

def display_team_fixtures(fixtures: List[Dict]) -> None:
    """Display team fixtures (past and upcoming)"""
    
    if not fixtures:
        st.info("⚽ Maç programı verisi bulunamadı")
        return
    
    # Separate past and future fixtures
    now = datetime.now()
    past_fixtures = []
    future_fixtures = []
    
    for fixture in fixtures:
        fixture_date = datetime.fromtimestamp(fixture['fixture']['timestamp'])
        if fixture_date < now:
            past_fixtures.append(fixture)
        else:
            future_fixtures.append(fixture)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📅 Gelecek Maçlar")
        if future_fixtures:
            for fixture in future_fixtures[:5]:
                display_fixture_card(fixture, is_future=True)
        else:
            st.info("Yaklaşan maç bulunamadı")
    
    with col2:
        st.subheader("📋 Son Maçlar")
        if past_fixtures:
            for fixture in past_fixtures[-5:]:
                display_fixture_card(fixture, is_future=False)
        else:
            st.info("Geçmiş maç verisi bulunamadı")

def display_fixture_card(fixture: Dict, is_future: bool = True) -> None:
    """Display individual fixture card"""
    
    teams = fixture.get('teams', {})
    home_team = teams.get('home', {})
    away_team = teams.get('away', {})
    score = fixture.get('score', {}).get('fulltime', {})
    
    if not home_team or not away_team:
        return
    
    fixture_date = datetime.fromtimestamp(fixture['fixture']['timestamp'])
    date_str = fixture_date.strftime('%d.%m.%Y %H:%M')
    
    if is_future:
        # Future match
        st.markdown(f"""
        <div style='border: 1px solid #ddd; border-radius: 10px; padding: 15px; margin: 10px 0;'>
            <div style='text-align: center;'>
                <strong>{home_team['name']} vs {away_team['name']}</strong><br>
                📅 {date_str}<br>
                🏆 {fixture.get('league', {}).get('name', 'Bilinmiyor')}
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Past match
        home_score = score.get('home', 0) if score else 0
        away_score = score.get('away', 0) if score else 0
        
        st.markdown(f"""
        <div style='border: 1px solid #ddd; border-radius: 10px; padding: 15px; margin: 10px 0;'>
            <div style='text-align: center;'>
                <strong>{home_team['name']} {home_score} - {away_score} {away_team['name']}</strong><br>
                📅 {date_str}<br>
                🏆 {fixture.get('league', {}).get('name', 'Bilinmiyor')}
            </div>
        </div>
        """, unsafe_allow_html=True)

def display_team_squad(squad: List[Dict]) -> None:
    """Display team squad information"""
    
    if not squad:
        st.info("👥 Kadro bilgisi bulunamadı")
        return
    
    squad_data = squad[0] if squad else {}
    players = squad_data.get('players', [])
    
    if not players:
        st.info("👥 Oyuncu listesi bulunamadı")
        return
    
    # Group by position
    positions = {}
    for player in players:
        pos = player.get('position', 'Bilinmiyor')
        if pos not in positions:
            positions[pos] = []
        positions[pos].append(player)
    
    # Display by position
    for position, player_list in positions.items():
        st.subheader(f"{position} ({len(player_list)} oyuncu)")
        
        # Create DataFrame for position
        df_data = []
        for player in player_list:
            df_data.append({
                'Ad': player.get('name', 'Bilinmiyor'),
                'Yaş': player.get('age', 'Bilinmiyor'),
                'Numara': player.get('number', '-')
            })
        
        if df_data:
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True, hide_index=True)

def display_team_injuries(injuries: List[Dict]) -> None:
    """Display team injuries"""
    
    if not injuries:
        st.success("🎉 Aktif sakatlık bulunmuyor!")
        return
    
    st.warning(f"⚠️ {len(injuries)} oyuncuda sakatlık var")
    
    injury_data = []
    for injury in injuries:
        player = injury.get('player', {})
        injury_data.append({
            'Oyuncu': player.get('name', 'Bilinmiyor'),
            'Sakatlık': injury.get('player', {}).get('reason', 'Belirtilmemiş'),
            'Tür': injury.get('player', {}).get('type', 'Bilinmiyor')
        })
    
    if injury_data:
        df = pd.DataFrame(injury_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

def display_team_venue(venue: List[Dict], team_data: Dict) -> None:
    """Display team venue information"""
    
    if not venue:
        st.info("🏟️ Stadyum bilgisi bulunamadı")
        return
    
    venue_data = venue[0] if venue else {}
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if venue_data.get('image'):
            st.image(venue_data['image'], caption=venue_data.get('name', 'Stadyum'))
    
    with col2:
        st.write(f"**Stadyum:** {venue_data.get('name', 'Bilinmiyor')}")
        st.write(f"**Kapasite:** {venue_data.get('capacity', 'Bilinmiyor'):,}" if venue_data.get('capacity') else "**Kapasite:** Bilinmiyor")
        st.write(f"**Şehir:** {venue_data.get('city', 'Bilinmiyor')}")
        st.write(f"**Yüzey:** {venue_data.get('surface', 'Bilinmiyor')}")
        
        if venue_data.get('address'):
            st.write(f"**Adres:** {venue_data['address']}")

def display_team_trophies(trophies: List[Dict]) -> None:
    """Display team trophies"""
    
    if not trophies:
        st.info("🏆 Kupa bilgisi bulunamadı")
        return
    
    st.success(f"🏆 {len(trophies)} kupa kazanmış!")
    
    # Group by trophy name
    trophy_counts = {}
    for trophy in trophies:
        name = trophy.get('league', 'Bilinmiyor')
        if name not in trophy_counts:
            trophy_counts[name] = 0
        trophy_counts[name] += 1
    
    # Display trophy counts
    trophy_data = []
    for trophy_name, count in trophy_counts.items():
        trophy_data.append({
            'Kupa': trophy_name,
            'Sayı': count
        })
    
    if trophy_data:
        df = pd.DataFrame(trophy_data)
        df = df.sort_values('Sayı', ascending=False)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Show recent trophies
        st.subheader("🗓️ Son Kazanılan Kupalar")
        recent_trophies = sorted(trophies, key=lambda x: x.get('season', ''), reverse=True)[:5]
        
        for trophy in recent_trophies:
            st.write(f"🏆 **{trophy.get('league', 'Bilinmiyor')}** - {trophy.get('season', 'Bilinmiyor')} sezonu")