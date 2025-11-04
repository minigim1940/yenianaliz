# 🔍 DEBUG REHBERİ - Advanced Metrics

## Sorun: "Gerçek verilerle çalışmıyor"

### Kontrol Listesi:

#### 1. Streamlit Terminal Çıktısını Kontrol Edin

Tarayıcıda Advanced Metrics tab'ını açtığınızda terminal'de şu mesajları aramalısınız:

```
📡 [Takım Adı] için son maçlar çekiliyor...
✅ [Takım Adı]: X maç parse edildi
```

**Eğer görmüyorsanız:**
- API çağrısı yapılmıyor demektir
- `enhanced_match_analysis.py` çalışmıyor olabilir

**Eğer "⚠️ fixtures hatası" görüyorsanız:**
- API rate limit veya yetkilendirme hatası
- 429 Too Many Requests = Dakikalık limit aşıldı

#### 2. Gerçek Veri Kontrolü

Advanced Metrics tab'ını açın ve şu değerleri kontrol edin:

**Beklenen (Gerçek Veri):**
- Overall Rating: 40-80 arası değişken değerler (her takım farklı)
- Form String: "WWDWL" gibi gerçek form
- xG değerleri: Takıma özel (1.2, 1.8, vb.)
- Strengths/Weaknesses: API'den gelen verilerle hesaplanmış

**Mock Veri Belirtileri:**
- Overall Rating: Hep aynı (örn. her zaman 52.4)
- Form String: Yok veya hep "WWDDD"
- xG: Hep aynı değer (1.5)
- Strengths: "İleri Oyun Kalitesi" gibi generic ifadeler

#### 3. Debug Modunu Aktifleştirin

Terminal'de şu komutu çalıştırın:

```bash
# Windows
set PYTHONUNBUFFERED=1
streamlit run app.py

# Linux/Mac
PYTHONUNBUFFERED=1 streamlit run app.py
```

Bu tüm print() çıktılarını anında gösterir.

#### 4. Manuel API Test

```python
python test_advanced_metrics_realtime.py
```

Bu test:
- ✅ API çağrısı yapıyor mu?
- ✅ Fixture verisi parse ediliyor mu?
- ✅ Advanced metrics hesaplanıyor mu?

#### 5. Bilinen Sorunlar & Çözümler

**Sorun:** API Rate Limit (429)
**Çözüm:** 1 dakika bekleyin veya farklı bir maç seçin

**Sorun:** "Advanced analysis oluşturulamadı"
**Çözüm:** `league_id` parametresi hatası - FIXED ✅

**Sorun:** Recent matches boş
**Çözüm:** `fixture_parser.py` kullanılıyor - FIXED ✅

**Sorun:** Hep aynı rating (52.4)
**Çözüm:** Fallback değerler kullanılıyor - API verisi gelmiyor demektir

#### 6. Gerçek Veri Akışı

```
1. User selects match → app.py
2. show_advanced_metrics_if_available() called
3. get_enhanced_match_analysis() → enhanced_match_analysis.py
4. API calls:
   a. calculate_general_stats_v2() → team statistics
   b. make_api_request('fixtures') → recent matches
5. parse_fixtures_to_matches() → convert to internal format
6. AdvancedMetricsManager.get_comprehensive_team_analysis()
   - Form calculator
   - xG calculator
   - Pressing calculator
   - Progressive calculator
   - xA calculator
7. display_advanced_metrics_dashboard() → show in UI
```

#### 7. Hızlı Test Komutu

Web uygulamasında Python console açın (F12 → Console):

```javascript
// Streamlit'in rerun etmesini tetikle
window.location.reload();
```

Ya da direkt tarayıcıda F5 / Ctrl+R

---

## ✅ ÇÖZÜLMELİ DURUMDA

Şu anda sistemiçin yapıldı:
- ✅ `fixture_parser.py` eklendi
- ✅ `enhanced_match_analysis.py` güncellendi
- ✅ API çağrıları gerçek veri çekiyor
- ✅ Print statements debug için eklendi

**Web'de test etmek için:**
1. Tarayıcıyı yenileyin (F5)
2. Bir maç seçin
3. Advanced Metrics tab'ını açın
4. Terminal çıktısına bakın (API çağrıları görünmeli)

**Eğer hala mock veri görüyorsanız:**
- API rate limit aşılmış olabilir (429 hatası)
- Kullanıcı girişi gerekiyor olabilir (API key)
- Terminal'de hata mesajlarını kontrol edin

---

**Son Güncelleme:** 4 Kasım 2025  
**Durum:** Kod hazır, API rate limit kontrol edilmeli
