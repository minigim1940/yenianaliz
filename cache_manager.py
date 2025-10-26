"""
CACHE YÖNETİM SİSTEMİ
SQLite tabanlı hızlı cache - API çağrılarını azaltır
"""
import sqlite3
import json
import time
from datetime import datetime, timedelta
from typing import Optional, Any, Dict
import hashlib
import os

class CacheManager:
    """
    Akıllı cache sistemi - API yanıtlarını önbelleğe alır
    """
    
    def __init__(self, db_path: str = "api_cache.db"):
        """Cache veritabanını başlat"""
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Veritabanı tablolarını oluştur"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Cache tablosu
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                cache_key TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                category TEXT NOT NULL,
                created_at REAL NOT NULL,
                expires_at REAL NOT NULL,
                hit_count INTEGER DEFAULT 0
            )
        """)
        
        # İstatistik tablosu
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                cache_hits INTEGER DEFAULT 0,
                cache_misses INTEGER DEFAULT 0,
                api_calls_saved INTEGER DEFAULT 0
            )
        """)
        
        conn.commit()
        conn.close()
        
        print(f"✅ Cache veritabanı hazır: {self.db_path}")
    
    def _generate_key(self, category: str, **kwargs) -> str:
        """Cache anahtarı oluştur"""
        # Parametreleri sıralı string'e çevir
        params = json.dumps(kwargs, sort_keys=True)
        # Hash ile kısa anahtar oluştur
        hash_obj = hashlib.md5(f"{category}:{params}".encode())
        return hash_obj.hexdigest()
    
    def get(self, category: str, **kwargs) -> Optional[Any]:
        """
        Cache'den veri al
        
        Args:
            category: Veri kategorisi (team_data, transfers, xg, etc.)
            **kwargs: Anahtar parametreleri (team_id, season, etc.)
        
        Returns:
            Cache'deki veri veya None
        """
        cache_key = self._generate_key(category, **kwargs)
        
        conn = sqlite3.connect(self.db_path, timeout=10)
        cursor = conn.cursor()
        
        # Cache'i kontrol et
        cursor.execute("""
            SELECT data, expires_at, hit_count 
            FROM cache 
            WHERE cache_key = ? AND expires_at > ?
        """, (cache_key, time.time()))
        
        result = cursor.fetchone()
        
        if result:
            data_json, expires_at, hit_count = result
            
            # Hit count güncelle
            cursor.execute("""
                UPDATE cache 
                SET hit_count = hit_count + 1 
                WHERE cache_key = ?
            """, (cache_key,))
            
            # İstatistik güncelle (aynı connection kullan)
            self._update_stats('hit', conn)
            
            conn.commit()
            conn.close()
            
            # JSON'dan objeye çevir
            data = json.loads(data_json)
            
            # Kalan süreyi hesapla
            remaining = int(expires_at - time.time())
            print(f"🎯 Cache HIT [{category}] - Kalan süre: {remaining}s")
            
            return data
        else:
            # Cache miss
            conn.close()
            self._update_stats('miss')
            print(f"❌ Cache MISS [{category}] - API çağrısı yapılacak")
            return None
    
    def set(self, category: str, data: Any, ttl_seconds: int = 1800, **kwargs):
        """
        Cache'e veri kaydet
        
        Args:
            category: Veri kategorisi
            data: Kaydedilecek veri
            ttl_seconds: Yaşam süresi (saniye)
            **kwargs: Anahtar parametreleri
        """
        cache_key = self._generate_key(category, **kwargs)
        data_json = json.dumps(data)
        
        now = time.time()
        expires_at = now + ttl_seconds
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Cache'e kaydet (var ise üzerine yaz)
        cursor.execute("""
            INSERT OR REPLACE INTO cache 
            (cache_key, data, category, created_at, expires_at, hit_count)
            VALUES (?, ?, ?, ?, ?, 0)
        """, (cache_key, data_json, category, now, expires_at))
        
        conn.commit()
        conn.close()
        
        print(f"💾 Cache SAVE [{category}] - TTL: {ttl_seconds}s")
    
    def _update_stats(self, stat_type: str, conn=None):
        """İstatistikleri güncelle"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Eğer connection verilmediyse yeni oluştur
        own_conn = False
        if conn is None:
            conn = sqlite3.connect(self.db_path, timeout=10)
            own_conn = True
        
        cursor = conn.cursor()
        
        # Bugünün kaydını bul veya oluştur
        cursor.execute("""
            INSERT OR IGNORE INTO cache_stats (date) VALUES (?)
        """, (today,))
        
        # İstatistiği güncelle
        if stat_type == 'hit':
            cursor.execute("""
                UPDATE cache_stats 
                SET cache_hits = cache_hits + 1,
                    api_calls_saved = api_calls_saved + 1
                WHERE date = ?
            """, (today,))
        else:  # miss
            cursor.execute("""
                UPDATE cache_stats 
                SET cache_misses = cache_misses + 1
                WHERE date = ?
            """, (today,))
        
        conn.commit()
        
        # Sadece kendi açtığımız connection'ı kapat
        if own_conn:
            conn.close()
    
    def clear_expired(self):
        """Süresi dolmuş cache'leri temizle"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM cache WHERE expires_at < ?
        """, (time.time(),))
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        if deleted > 0:
            print(f"🧹 {deleted} süresi dolmuş cache silindi")
        
        return deleted
    
    def clear_category(self, category: str):
        """Belirli bir kategorideki tüm cache'leri temizle"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM cache WHERE category = ?", (category,))
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        print(f"🧹 {category} kategorisinden {deleted} cache silindi")
        return deleted
    
    def clear_all(self):
        """Tüm cache'i temizle"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM cache")
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        print(f"🧹 Toplam {deleted} cache silindi")
        return deleted
    
    def get_stats(self) -> Dict:
        """Cache istatistiklerini getir"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Bugünün istatistikleri
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("""
            SELECT cache_hits, cache_misses, api_calls_saved
            FROM cache_stats
            WHERE date = ?
        """, (today,))
        
        today_stats = cursor.fetchone()
        
        # Toplam cache sayısı
        cursor.execute("SELECT COUNT(*) FROM cache WHERE expires_at > ?", (time.time(),))
        total_active = cursor.fetchone()[0]
        
        # Kategori başına dağılım
        cursor.execute("""
            SELECT category, COUNT(*) 
            FROM cache 
            WHERE expires_at > ?
            GROUP BY category
        """, (time.time(),))
        
        by_category = dict(cursor.fetchall())
        
        conn.close()
        
        if today_stats:
            hits, misses, saved = today_stats
            total = hits + misses
            hit_rate = (hits / total * 100) if total > 0 else 0
        else:
            hits = misses = saved = 0
            hit_rate = 0
        
        return {
            'today': {
                'hits': hits,
                'misses': misses,
                'total': hits + misses,
                'hit_rate': round(hit_rate, 1),
                'api_calls_saved': saved
            },
            'cache': {
                'total_active': total_active,
                'by_category': by_category
            }
        }
    
    def print_stats(self):
        """İstatistikleri güzel formatta yazdır"""
        stats = self.get_stats()
        
        print("\n" + "="*60)
        print("📊 CACHE İSTATİSTİKLERİ")
        print("="*60)
        
        print(f"\n📅 BUGÜN:")
        print(f"  ✅ Cache Hit: {stats['today']['hits']}")
        print(f"  ❌ Cache Miss: {stats['today']['misses']}")
        print(f"  📈 Hit Rate: %{stats['today']['hit_rate']}")
        print(f"  💰 API Tasarrufu: {stats['today']['api_calls_saved']} çağrı")
        
        print(f"\n💾 AKTİF CACHE:")
        print(f"  📦 Toplam: {stats['cache']['total_active']} kayıt")
        
        if stats['cache']['by_category']:
            print(f"\n  📂 Kategoriler:")
            for category, count in stats['cache']['by_category'].items():
                print(f"    • {category}: {count} kayıt")
        
        print("\n" + "="*60)


# Singleton instance
_cache_instance = None

def get_cache() -> CacheManager:
    """Global cache instance'ı getir"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CacheManager()
    return _cache_instance


# Decorator fonksiyonu - kolay kullanım için
def cached(category: str, ttl: int = 1800):
    """
    Cache decorator - fonksiyon sonuçlarını cache'ler
    
    Kullanım:
    @cached('team_data', ttl=1800)
    def get_team_info(team_id):
        # API çağrısı
        return data
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            cache = get_cache()
            
            # Cache anahtarı için parametreleri kullan
            cache_params = {
                'func': func.__name__,
                'args': str(args),
                **kwargs
            }
            
            # Önce cache'e bak
            cached_data = cache.get(category, **cache_params)
            if cached_data is not None:
                return cached_data
            
            # Cache miss - fonksiyonu çalıştır
            result = func(*args, **kwargs)
            
            # Sonucu cache'e kaydet
            if result is not None:
                cache.set(category, result, ttl, **cache_params)
            
            return result
        
        return wrapper
    return decorator


# Test fonksiyonu
if __name__ == "__main__":
    print("🧪 CACHE SİSTEMİ TEST")
    print("="*60)
    
    # Cache instance oluştur
    cache = CacheManager()
    
    # Test verisi
    test_data = {
        'team_id': 645,
        'name': 'Galatasaray',
        'elo': 1850,
        'value': 285.3
    }
    
    # 1. Veriyi kaydet
    print("\n1. Cache'e kaydet:")
    cache.set('team_data', test_data, ttl_seconds=30, team_id=645)
    
    # 2. Veriyi oku (hit olmalı)
    print("\n2. Cache'den oku (HIT bekleniyor):")
    result = cache.get('team_data', team_id=645)
    print(f"   Sonuç: {result}")
    
    # 3. Tekrar oku (yine hit)
    print("\n3. Tekrar oku (HIT bekleniyor):")
    result = cache.get('team_data', team_id=645)
    print(f"   Sonuç: {result}")
    
    # 4. Farklı key (miss olmalı)
    print("\n4. Farklı team_id (MISS bekleniyor):")
    result = cache.get('team_data', team_id=999)
    print(f"   Sonuç: {result}")
    
    # 5. İstatistikler
    print("\n5. İstatistikler:")
    cache.print_stats()
    
    # 6. Temizlik testi
    print("\n6. Cache temizliği:")
    print(f"   Süresi dolmuş: {cache.clear_expired()}")
    print(f"   Toplam silme: {cache.clear_category('team_data')}")
    
    print("\n✅ Test tamamlandı!")
