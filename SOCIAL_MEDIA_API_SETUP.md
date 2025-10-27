# Sosyal Medya API Kurulum Rehberi

Bu rehber, Streamlit uygulamanızda gerçek Twitter ve Reddit verilerini kullanmak için API anahtarlarını nasıl alacağınızı ve yapılandıracağınızı açıklar.

## 🐦 Twitter API Kurulumu (Ücretsiz)

### 1. Twitter Developer Hesabı Oluşturma

1. **developer.twitter.com** adresine gidin
2. "Sign up" butonuna tıklayın
3. Twitter hesabınızla giriş yapın
4. Başvuru formunu doldurun:
   - Use case: Hobbyist > Exploring the API
   - App name: Football Sentiment Analysis
   - App description: Analyzing football team sentiment from social media

### 2. App Oluşturma

1. Developer Portal'da "Projects & Apps" bölümüne gidin
2. "Create App" butonuna tıklayın
3. App adını girin (örn: `football-analysis`)
4. **Bearer Token**'ı kopyalayın ve güvenli bir yere kaydedin

### 3. API Limitleri (Free Tier)

- **1,500 tweet/ay** (yaklaşık 50 tweet/gün)
- Son 7 günlük veriye erişim
- Rate limit: 15 istek/15 dakika

### 4. Streamlit'e Ekleme

**.streamlit/secrets.toml** dosyası oluşturun:

```toml
TWITTER_BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAABearerTokenBuraya..."
```

---

## 🤖 Reddit API Kurulumu (Ücretsiz & Sınırsız)

### 1. Reddit App Oluşturma

1. **reddit.com/prefs/apps** adresine gidin
2. Reddit hesabınızla giriş yapın
3. Sayfayı en alta kaydırın ve "create another app..." butonuna tıklayın

### 2. App Bilgileri

Formu doldurun:
- **name**: football-sentiment-app
- **App type**: script seçeneğini işaretleyin
- **description**: Football sentiment analysis
- **about url**: (boş bırakabilirsiniz)
- **redirect uri**: http://localhost:8501

"create app" butonuna tıklayın

### 3. Credentials Alma

Oluşturulan app kutusunda:
- **Client ID**: App adının altındaki rastgele string (örn: `abc123xyz`)
- **Client Secret**: "secret" yazan satırdaki string

### 4. API Limitleri (Free)

- **Sınırsız** istek (rate limit var ama yüksek)
- 60 istek/dakika
- Tüm geçmiş veriye erişim

### 5. Streamlit'e Ekleme

**.streamlit/secrets.toml** dosyasına ekleyin:

```toml
REDDIT_CLIENT_ID = "abc123xyz"
REDDIT_CLIENT_SECRET = "secretkeyburaya"
```

---

## 📁 Secrets Dosyası Yapısı

Projenizde `.streamlit/secrets.toml` dosyası oluşturun:

```toml
# Twitter API
TWITTER_BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAABearerTokenBuraya..."

# Reddit API
REDDIT_CLIENT_ID = "abc123xyz"
REDDIT_CLIENT_SECRET = "secretkeyburaya"

# Diğer API anahtarları
API_KEY = "6336fb21e17dea87880d3b133132a13f"
```

**Not:** `.streamlit/secrets.toml` dosyasını `.gitignore`'a ekleyin!

---

## 🔧 Gerekli Kütüphanelerin Kurulumu

Terminal'de şu komutları çalıştırın:

```bash
pip install tweepy
pip install praw
```

Veya `requirements.txt`'e ekleyin:

```txt
tweepy>=4.14.0
praw>=7.7.1
```

---

## ✅ Test Etme

1. Streamlit uygulamanızı çalıştırın:
   ```bash
   streamlit run app.py
   ```

2. Sentiment Analizi sayfasına gidin (📱 butonu)

3. API durumu mesajını kontrol edin:
   - ✅ **API Aktif**: Gerçek veriler çekilecek
   - ℹ️ **API yok**: Mock data kullanılacak

4. Bir takım adı girin ve "Analizi Başlat" butonuna tıklayın

5. Console'da şu mesajları görmelisiniz:
   ```
   ✅ Twitter API bağlantısı başarılı
   ✅ Reddit API bağlantısı başarılı
   🐦 Twitter'dan 'Galatasaray' aranıyor...
   ✅ Twitter'dan 47 tweet çekildi
   🤖 Reddit'ten 'Galatasaray' aranıyor...
   ✅ Reddit'ten 23 post çekildi
   ```

---

## ⚠️ Önemli Notlar

### Twitter API
- Free tier'da **aylık 1500 tweet** limiti vardır
- Aşırı kullanımdan kaçının
- Son 7 günlük veriye erişim
- Eğer limit aşılırsa mock data otomatik kullanılır

### Reddit API
- Gerçekten sınırsız ve ücretsiz
- Rate limit: 60 istek/dakika
- User agent önemli: değiştirmeyin

### Güvenlik
- API anahtarlarını **asla** GitHub'a push etmeyin
- `.gitignore` dosyasına `.streamlit/secrets.toml` ekleyin
- Streamlit Cloud'a deploy ederken secrets'ı platform üzerinden ekleyin

---

## 🚀 Production (Streamlit Cloud) Deployment

Streamlit Cloud'a deploy ederken:

1. Streamlit Cloud dashboard'a gidin
2. App ayarlarından "Secrets" bölümüne gidin
3. secrets.toml içeriğini buraya yapıştırın
4. Save edin

**Not:** Yerel `secrets.toml` dosyası cloud'da kullanılmaz, manuel eklemeniz gerekir.

---

## 🆘 Sorun Giderme

### "tweepy kurulu değil" hatası
```bash
pip install tweepy
```

### "Twitter API bağlantı hatası"
- Bearer Token'ı kontrol edin (boşluk yok, tam kopyalandı mı?)
- `secrets.toml` dosyası doğru konumda mı? (`.streamlit/secrets.toml`)
- Token aktif mi? (developer.twitter.com'dan kontrol edin)

### "Reddit API bağlantı hatası"
- Client ID ve Secret'ı kontrol edin
- App type "script" olarak seçildi mi?
- `praw` kütüphanesi kurulu mu?

### API çalışmıyor ama hata yok
- Console çıktılarını kontrol edin
- "ℹ️ Mock data kullanılıyor" mesajı varsa API credentials eksik
- Streamlit'i yeniden başlatın (`Ctrl+C` sonra tekrar `streamlit run app.py`)

---

## 📊 Kullanım İstatistikleri

API olmadan:
- ✅ Tüm özellikler çalışır
- 🎲 Demo data kullanılır
- ⚡ Anında sonuç

API ile:
- ✅ Gerçek sosyal medya verileri
- 📡 2-5 saniye bekleme
- 🎯 Daha doğru sentiment analizi

---

## 💡 İpuçları

1. **Hybrid Kullanım**: Bazı aramalar için API, bazıları için mock kullanabilirsiniz
2. **Cache**: Sık aranan takımlar için cache mekanizması eklenebilir
3. **Rate Limit**: Twitter limitini aşmamak için günlük kullanımı takip edin
4. **Multi-Language**: İngilizce aramalar için `lang:en` ekleyin

---

## 📚 Kaynaklar

- Twitter API Docs: https://developer.twitter.com/en/docs
- Reddit API Docs: https://www.reddit.com/dev/api
- tweepy Docs: https://docs.tweepy.org
- praw Docs: https://praw.readthedocs.io

---

✅ **Kurulum tamamlandı!** Artık gerçek sosyal medya verilerini analiz edebilirsiniz.
