# -*- coding: utf-8 -*-
"""
Smart API Cache Wrapper
=======================
API fonksiyonlarını otomatik cache ile saran wrapper

Usage:
    from smart_api_cache import smart_cached_api
    
    @smart_cached_api(category='fixture')
    def get_fixture_data(api_key, fixture_id):
        # Your API call here
        return api_response
"""

from functools import wraps
from typing import Callable, Optional, Any, Dict
from datetime import datetime
from cache_manager import CacheManager

# Global cache instance
_cache = CacheManager()


def smart_cached_api(
    category: str,
    extract_status: Optional[Callable] = None,
    extract_date: Optional[Callable] = None,
    key_params: Optional[list] = None
):
    """
    Akıllı API cache decorator - otomatik dinamik TTL
    
    Args:
        category: Cache kategorisi
        extract_status: Fixture status çıkarma fonksiyonu (optional)
        extract_date: Fixture date çıkarma fonksiyonu (optional)
        key_params: Cache key için kullanılacak parametre isimleri (optional)
    
    Example:
        @smart_cached_api(
            category='fixture',
            extract_status=lambda result: result.get('fixture', {}).get('status', {}).get('short'),
            extract_date=lambda result: result.get('fixture', {}).get('date'),
            key_params=['fixture_id']
        )
        def get_fixture(api_key, fixture_id):
            # API call
            return response
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract cache key parameters
            cache_params = {}
            
            if key_params:
                # Get from kwargs
                for param in key_params:
                    if param in kwargs:
                        cache_params[param] = kwargs[param]
                
                # If not in kwargs, try positional args based on function signature
                import inspect
                sig = inspect.signature(func)
                param_names = list(sig.parameters.keys())
                
                for i, param in enumerate(key_params):
                    if param not in cache_params and i < len(args):
                        cache_params[param] = args[i]
            
            # Try to get from cache
            cached_data = _cache.get(category, **cache_params)
            if cached_data is not None:
                return cached_data
            
            # Cache miss - call API
            result = func(*args, **kwargs)
            
            if result is not None:
                # Extract fixture status and date if extractors provided
                fixture_status = None
                fixture_date = None
                
                if extract_status:
                    try:
                        fixture_status = extract_status(result)
                    except:
                        pass
                
                if extract_date:
                    try:
                        fixture_date = extract_date(result)
                    except:
                        pass
                
                # Save with smart TTL
                _cache.set_smart(
                    category=category,
                    data=result,
                    fixture_status=fixture_status,
                    fixture_date=fixture_date,
                    **cache_params
                )
            
            return result
        
        return wrapper
    return decorator


def get_cache_manager() -> CacheManager:
    """Get global cache manager instance"""
    return _cache


# Convenience functions
def clear_live_cache():
    """Clear all live match caches (for manual refresh)"""
    # This would need category filtering in cache_manager
    print("🗑️ Clearing live match caches...")
    # Implementation depends on cache_manager capabilities


# Example usage functions
def example_fixture_api_call(api_key: str, fixture_id: int) -> Dict:
    """Example fixture API call with smart caching"""
    
    @smart_cached_api(
        category='fixture',
        extract_status=lambda r: r.get('fixture', {}).get('status', {}).get('short'),
        extract_date=lambda r: r.get('fixture', {}).get('date'),
        key_params=['fixture_id']
    )
    def _get_fixture(fixture_id: int) -> Dict:
        # Simulate API call
        import requests
        # response = requests.get(f"https://api.example.com/fixtures/{fixture_id}")
        # return response.json()
        
        # Mock data for example
        return {
            'fixture': {
                'id': fixture_id,
                'status': {'short': '1H'},
                'date': datetime.now().isoformat()
            }
        }
    
    return _get_fixture(fixture_id=fixture_id)


def example_team_api_call(api_key: str, team_id: int, season: int) -> Dict:
    """Example team stats API call with smart caching"""
    
    @smart_cached_api(
        category='team',  # Static data - 30 days cache
        key_params=['team_id', 'season']
    )
    def _get_team_stats(team_id: int, season: int) -> Dict:
        # Simulate API call
        return {
            'team_id': team_id,
            'season': season,
            'stats': {'goals': 50, 'wins': 20}
        }
    
    return _get_team_stats(team_id=team_id, season=season)


# Test
if __name__ == "__main__":
    print("🧪 SMART API CACHE WRAPPER TEST\n")
    
    # Test 1: Fixture API with live match
    print("📦 Test 1: Live Match Fixture")
    result1 = example_fixture_api_call(api_key="test", fixture_id=12345)
    print(f"   Result: {result1}")
    print()
    
    # Test 2: Same fixture (should hit cache)
    print("📦 Test 2: Same Fixture (Cache Hit Expected)")
    result2 = example_fixture_api_call(api_key="test", fixture_id=12345)
    print(f"   Result: {result2}")
    print()
    
    # Test 3: Team stats (static data)
    print("📦 Test 3: Team Stats (Static Data)")
    result3 = example_team_api_call(api_key="test", team_id=645, season=2024)
    print(f"   Result: {result3}")
    print()
    
    # Stats
    print("📊 Cache Stats:")
    _cache.print_stats()
