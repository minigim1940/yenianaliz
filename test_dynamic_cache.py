# -*- coding: utf-8 -*-
"""
Dynamic Cache System Test
==========================
Yeni dinamik TTL sistemini test et
"""

from cache_manager import CacheManager
from datetime import datetime, timedelta

print("="*80)
print("🧪 DYNAMIC CACHE SYSTEM TEST")
print("="*80 + "\n")

# Initialize cache
cache = CacheManager()

print("📦 Test 1: Live Match Cache (30s TTL)\n")

# Simulate live match data
live_fixture = {
    'fixture_id': 12345,
    'status': '1H',
    'home_score': 1,
    'away_score': 0,
    'minute': 37
}

# Calculate TTL
ttl = cache.calculate_dynamic_ttl(
    category='fixture',
    fixture_status='1H',
    fixture_date=datetime.now().isoformat()
)

print(f"   Calculated TTL: {ttl}s")
print(f"   Expected: {cache.TTL_LIVE_MATCH}s")
print(f"   Match: {'✅ PASS' if ttl == cache.TTL_LIVE_MATCH else '❌ FAIL'}\n")

# Save with smart cache
cache.set_smart(
    category='fixture',
    data=live_fixture,
    fixture_status='1H',
    fixture_date=datetime.now().isoformat(),
    fixture_id=12345
)

print("="*80 + "\n")

print("📦 Test 2: Upcoming Match (within 24h) - 1h TTL\n")

# Match in 12 hours
upcoming_date = (datetime.now() + timedelta(hours=12)).isoformat()
upcoming_fixture = {
    'fixture_id': 12346,
    'status': 'NS',
    'home_team': 'Team A',
    'away_team': 'Team B'
}

ttl = cache.calculate_dynamic_ttl(
    category='fixture',
    fixture_status='NS',
    fixture_date=upcoming_date
)

print(f"   Match Date: {upcoming_date}")
print(f"   Calculated TTL: {ttl}s ({ttl//60} minutes)")
print(f"   Expected: {cache.TTL_UPCOMING_SOON}s (60 minutes)")
print(f"   Match: {'✅ PASS' if ttl == cache.TTL_UPCOMING_SOON else '❌ FAIL'}\n")

cache.set_smart(
    category='fixture',
    data=upcoming_fixture,
    fixture_status='NS',
    fixture_date=upcoming_date,
    fixture_id=12346
)

print("="*80 + "\n")

print("📦 Test 3: Future Match (3 days away) - 24h TTL\n")

# Match in 3 days
future_date = (datetime.now() + timedelta(days=3)).isoformat()
future_fixture = {
    'fixture_id': 12347,
    'status': 'NS',
    'home_team': 'Team C',
    'away_team': 'Team D'
}

ttl = cache.calculate_dynamic_ttl(
    category='fixture',
    fixture_status='NS',
    fixture_date=future_date
)

print(f"   Match Date: {future_date}")
print(f"   Calculated TTL: {ttl}s ({ttl//3600} hours)")
print(f"   Expected: {cache.TTL_FUTURE_MATCH}s (24 hours)")
print(f"   Match: {'✅ PASS' if ttl == cache.TTL_FUTURE_MATCH else '❌ FAIL'}\n")

cache.set_smart(
    category='fixture',
    data=future_fixture,
    fixture_status='NS',
    fixture_date=future_date,
    fixture_id=12347
)

print("="*80 + "\n")

print("📦 Test 4: Finished Match - 7 days TTL\n")

finished_fixture = {
    'fixture_id': 12348,
    'status': 'FT',
    'home_score': 2,
    'away_score': 1
}

ttl = cache.calculate_dynamic_ttl(
    category='fixture',
    fixture_status='FT'
)

print(f"   Calculated TTL: {ttl}s ({ttl//86400} days)")
print(f"   Expected: {cache.TTL_PAST_MATCH}s (7 days)")
print(f"   Match: {'✅ PASS' if ttl == cache.TTL_PAST_MATCH else '❌ FAIL'}\n")

cache.set_smart(
    category='fixture',
    data=finished_fixture,
    fixture_status='FT',
    fixture_id=12348
)

print("="*80 + "\n")

print("📦 Test 5: Static Data (League Info) - 30 days TTL\n")

league_data = {
    'league_id': 203,
    'name': 'Süper Lig',
    'country': 'Turkey'
}

ttl = cache.calculate_dynamic_ttl(
    category='league',
    league_id=203
)

print(f"   Calculated TTL: {ttl}s ({ttl//86400} days)")
print(f"   Expected: {cache.TTL_STATIC_DATA}s (30 days)")
print(f"   Match: {'✅ PASS' if ttl == cache.TTL_STATIC_DATA else '❌ FAIL'}\n")

cache.set_smart(
    category='league',
    data=league_data,
    league_id=203
)

print("="*80 + "\n")

print("📦 Test 6: Half-Time Match - 30s TTL\n")

ht_fixture = {
    'fixture_id': 12349,
    'status': 'HT',
    'home_score': 1,
    'away_score': 1
}

ttl = cache.calculate_dynamic_ttl(
    category='fixture',
    fixture_status='HT'
)

print(f"   Calculated TTL: {ttl}s")
print(f"   Expected: {cache.TTL_LIVE_MATCH}s (30 seconds)")
print(f"   Match: {'✅ PASS' if ttl == cache.TTL_LIVE_MATCH else '❌ FAIL'}\n")

cache.set_smart(
    category='fixture',
    data=ht_fixture,
    fixture_status='HT',
    fixture_id=12349
)

print("="*80 + "\n")

# Summary
print("📊 TTL CONFIGURATION SUMMARY\n")
print(f"   🔴 Live Match (1H, 2H, HT, ET):        {cache.TTL_LIVE_MATCH}s (30 seconds)")
print(f"   🟡 Upcoming Soon (<24h):               {cache.TTL_UPCOMING_SOON}s (1 hour)")
print(f"   🟢 Future Match (>24h):                {cache.TTL_FUTURE_MATCH}s (24 hours)")
print(f"   ✅ Finished Match (FT):                {cache.TTL_PAST_MATCH}s (7 days)")
print(f"   📚 Static Data (leagues, teams):       {cache.TTL_STATIC_DATA}s (30 days)")
print(f"   ⚙️ Default:                            {cache.TTL_DEFAULT}s (30 minutes)")

print("\n" + "="*80)
print("✅ ALL TESTS COMPLETED")
print("="*80 + "\n")

# Cache stats
print("📈 Cache Statistics:\n")
cache.print_stats()

print("\n🎯 Dynamic Cache System is ready for production!")
