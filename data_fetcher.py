"""
VERİ TOPLAMA MODÜLü - PARALEL + CACHE
Ana sistem için optimize edilmiş veri çekme
"""
import asyncio
import aiohttp
import time
from typing import Dict, Optional, Tuple
from cache_manager import get_cache
from parallel_api import ParallelAPIClient


class DataFetcher:
    """
    Akıllı veri çekici - Cache + Paralel API
    """
    
    def __init__(self):
        self.cache = get_cache()
        self.api_client = ParallelAPIClient()
    
    async def _fetch_all_team_data_async(self, session: aiohttp.ClientSession,
                                         team_id: int, league_id: int, 
                                         season: int) -> Dict:
        """
        Bir takımın TÜM verilerini paralel çek
        """
        return await self.api_client.fetch_team_data(
            session, team_id, league_id, season
        )
    
    def get_team_complete_data(self, team_id: int, league_id: int = 203, 
                               season: int = 2025) -> Dict:
        """
        Takım verilerini getir (cache-first)
        """
        # Cache kontrol
        cache_key = f"team_complete_{team_id}_{league_id}_{season}"
        cached = self.cache.get('team_data', key=cache_key)
        if cached:
            return cached
        
        # API'den çek
        async def fetch():
            async with aiohttp.ClientSession(
                headers=self.api_client.headers
            ) as session:
                return await self._fetch_all_team_data_async(
                    session, team_id, league_id, season
                )
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            data = loop.run_until_complete(fetch())
            
            # Cache'e kaydet (30 dakika)
            self.cache.set('team_data', data, 1800, key=cache_key)
            
            return data
        finally:
            loop.close()
    
    def get_match_analysis_data(self, team1_id: int, team2_id: int,
                                league_id: int = 203, season: int = 2025) -> Dict:
        """
        Maç analizi için gerekli TÜM verileri çek
        PARALEL + CACHE optimizasyonlu
        """
        cache_key = f"match_data_{team1_id}_{team2_id}_{league_id}_{season}"
        
        # Cache kontrol
        cached = self.cache.get('match_analysis', key=cache_key)
        if cached:
            print(f"🎯 Maç verileri cache'den alındı")
            return cached
        
        print(f"🔄 Maç verileri API'den çekiliyor (PARALEL)...")
        start = time.time()
        
        # Paralel veri çekimi
        async def fetch_all():
            async with aiohttp.ClientSession(
                headers=self.api_client.headers
            ) as session:
                # 4 ana veri grubu paralel
                tasks = [
                    self._fetch_all_team_data_async(
                        session, team1_id, league_id, season
                    ),
                    self._fetch_all_team_data_async(
                        session, team2_id, league_id, season
                    ),
                    self.api_client.fetch(session, 'fixtures/headtohead', {
                        'h2h': f'{team1_id}-{team2_id}',
                        'last': 10
                    }),
                    self.api_client.fetch(session, 'fixtures', {
                        'league': league_id,
                        'season': season,
                        'last': 50
                    })
                ]
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                return {
                    'team1': results[0] if not isinstance(results[0], Exception) else None,
                    'team2': results[1] if not isinstance(results[1], Exception) else None,
                    'h2h': results[2] if not isinstance(results[2], Exception) else None,
                    'league_fixtures': results[3] if not isinstance(results[3], Exception) else None
                }
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            data = loop.run_until_complete(fetch_all())
            elapsed = time.time() - start
            
            print(f"✅ Paralel veri çekimi tamamlandı: {elapsed:.2f}s")
            
            # Cache'e kaydet (30 dakika)
            self.cache.set('match_analysis', data, 1800, key=cache_key)
            
            return data
            
        finally:
            loop.close()
    
    def fetch_teams_parallel(self, team_names: list) -> tuple:
        """
        Birden fazla takımın verilerini paralel olarak çek
        
        Args:
            team_names: Takım isimleri listesi (örn: ['Barcelona', 'Real Madrid'])
            
        Returns:
            tuple: Her takım için veri dict'leri
        """
        from real_time_data import get_complete_team_data
        
        print(f"📡 {len(team_names)} takım verisi paralel çekiliyor...")
        
        # Her takım için veri çek (senkron API fonksiyonunu kullan)
        results = []
        for team_name in team_names:
            print(f"   🔄 {team_name}...")
            team_data = get_complete_team_data(team_name)
            results.append(team_data)
        
        print(f"✅ {len(results)} takım verisi alındı")
        return tuple(results)
    
    def parse_team_data(self, raw_data: Dict) -> Dict:
        """
        API yanıtını analiz edilebilir formata dönüştür
        """
        if not raw_data:
            return {}
        
        parsed = {}
        
        # Team info
        if raw_data.get('team_info'):
            team_info, _ = raw_data['team_info']
            if team_info and team_info.get('response'):
                parsed['team_info'] = team_info['response'][0]
        
        # Standings
        if raw_data.get('standings'):
            standings, _ = raw_data['standings']
            if standings and standings.get('response'):
                parsed['standings'] = standings['response'][0]
        
        # Fixtures (son 10 maç)
        if raw_data.get('fixtures'):
            fixtures, _ = raw_data['fixtures']
            if fixtures and fixtures.get('response'):
                parsed['fixtures'] = fixtures['response']
        
        # Injuries
        if raw_data.get('injuries'):
            injuries, _ = raw_data['injuries']
            if injuries and injuries.get('response'):
                parsed['injuries'] = injuries['response']
        
        # Transfers
        if raw_data.get('transfers'):
            transfers, _ = raw_data['transfers']
            if transfers and transfers.get('response'):
                parsed['transfers'] = transfers['response']
        
        return parsed


# Singleton instance
_fetcher_instance = None

def get_fetcher() -> DataFetcher:
    """
    Global DataFetcher instance
    """
    global _fetcher_instance
    if _fetcher_instance is None:
        _fetcher_instance = DataFetcher()
    return _fetcher_instance


# Test
if __name__ == "__main__":
    print("="*70)
    print("🧪 DATA FETCHER TEST")
    print("="*70)
    
    fetcher = get_fetcher()
    
    # Test 1: Tek takım
    print("\n1️⃣ TEK TAKIM VERİSİ")
    print("-"*70)
    start = time.time()
    team_data = fetcher.get_team_complete_data(645)  # Galatasaray
    elapsed = time.time() - start
    
    print(f"✅ Veri çekildi: {elapsed:.2f}s")
    if team_data:
        print(f"📦 Data paketleri: {len(team_data)} endpoint")
    
    # Test 2: Maç analizi (paralel)
    print("\n2️⃣ MAÇ ANALİZİ VERİSİ (PARALEL)")
    print("-"*70)
    start = time.time()
    match_data = fetcher.get_match_analysis_data(645, 611)  # GS vs FB
    elapsed = time.time() - start
    
    print(f"✅ Maç verileri: {elapsed:.2f}s")
    if match_data:
        print(f"📊 Veri grupları:")
        print(f"   - Takım 1: {'✅' if match_data.get('team1') else '❌'}")
        print(f"   - Takım 2: {'✅' if match_data.get('team2') else '❌'}")
        print(f"   - H2H: {'✅' if match_data.get('h2h') else '❌'}")
        print(f"   - Lig: {'✅' if match_data.get('league_fixtures') else '❌'}")
    
    # Test 3: Cache test (aynı veriyi tekrar çek)
    print("\n3️⃣ CACHE TESTİ")
    print("-"*70)
    start = time.time()
    match_data2 = fetcher.get_match_analysis_data(645, 611)
    cache_time = time.time() - start
    
    print(f"✅ Cache süresi: {cache_time:.2f}s")
    print(f"⚡ Hız artışı: {(elapsed/cache_time):.1f}x")
    
    # Test 4: Parse test
    print("\n4️⃣ DATA PARSE TESTİ")
    print("-"*70)
    if match_data and match_data.get('team1'):
        parsed = fetcher.parse_team_data(match_data['team1'])
        print(f"✅ Parse edildi:")
        print(f"   - Team info: {'✅' if parsed.get('team_info') else '❌'}")
        print(f"   - Standings: {'✅' if parsed.get('standings') else '❌'}")
        print(f"   - Fixtures: {'✅' if parsed.get('fixtures') else '❌'}")
        print(f"   - Injuries: {'✅' if parsed.get('injuries') else '❌'}")
        print(f"   - Transfers: {'✅' if parsed.get('transfers') else '❌'}")
    
    print("\n" + "="*70)
    print("✅ TEST TAMAMLANDI!")
    print("="*70)
