"""
Sosyal Medya Sentiment Analizi Modülü
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import re
from collections import Counter


@dataclass
class SentimentScore:
    """Sentiment skoru"""
    positive: float  # 0-1 arası
    negative: float  # 0-1 arası
    neutral: float   # 0-1 arası
    compound: float  # -1 ile +1 arası (genel sentiment)
    
    def get_sentiment_label(self) -> str:
        """Sentiment etiketini döndür"""
        if self.compound >= 0.5:
            return "Çok Pozitif"
        elif self.compound >= 0.1:
            return "Pozitif"
        elif self.compound <= -0.5:
            return "Çok Negatif"
        elif self.compound <= -0.1:
            return "Negatif"
        else:
            return "Nötr"
    
    def get_emoji(self) -> str:
        """Sentiment emojisi"""
        if self.compound >= 0.5:
            return "🟢😊"
        elif self.compound >= 0.1:
            return "🟢🙂"
        elif self.compound <= -0.5:
            return "🔴😢"
        elif self.compound <= -0.1:
            return "🔴😕"
        else:
            return "🟡😐"


@dataclass
class SocialPost:
    """Sosyal medya gönderisi"""
    text: str
    source: str  # twitter, reddit, etc.
    timestamp: datetime
    author: str
    likes: int = 0
    retweets: int = 0
    sentiment: SentimentScore = None
    
    def calculate_engagement_score(self) -> float:
        """Engagement skoru hesapla"""
        return (self.likes * 1.0 + self.retweets * 2.0) / 10


class TurkishSentimentAnalyzer:
    """
    Türkçe sentiment analizi
    Kural tabanlı - API gerektirmez
    """
    
    def __init__(self):
        """Sentiment sözlüklerini yükle"""
        
        # Pozitif kelimeler (futbol özelinde)
        self.positive_words = {
            # Genel pozitif
            'harika', 'muhteşem', 'süper', 'mükemmel', 'enfes', 'inanılmaz',
            'güzel', 'başarılı', 'kazandı', 'galibiyet', 'zafer', 'şampiyon',
            'lider', 'birinci', 'rekor', 'tarihi', 'efsane', 'yıldız',
            
            # Futbol özgü pozitif
            'gol', 'asist', 'kurtarış', 'şampiyonluk', 'kupa', 'galibiyet',
            'performans', 'dominant', 'üstün', 'kaliteli', 'yetenekli', 'hızlı',
            'güçlü', 'teknik', 'taktik', 'organize', 'disiplinli', 'formda',
            'yükseliş', 'patlama', 'form', 'ivme', 'momentumda', 'ateşli',
            
            # Türkçe duygu ifadeleri
            'bravo', 'tebrik', 'aferin', 'vay', 'wow', 'oley', 'yaşa',
            'alkış', 'saygı', 'gurur', 'övgü', 'takdir', 'sevgi', 'aşk'
        }
        
        # Negatif kelimeler (futbol özelinde)
        self.negative_words = {
            # Genel negatif
            'kötü', 'berbat', 'rezil', 'rezalet', 'fiyasko', 'utanç',
            'kaybetti', 'yenilgi', 'mağlubiyet', 'düştü', 'çöktü', 'battı',
            'hata', 'yanlış', 'başarısız', 'yetersiz', 'zayıf', 'kötü',
            
            # Futbol özgü negatif
            'penaltı kaçırdı', 'kırmızı kart', 'sakatlık', 'ceza', 'faul',
            'formsuz', 'kötü gidiş', 'düşüş', 'kayıp', 'olumsuz', 'kriz',
            'dağınık', 'savunmasız', 'etkisiz', 'pasif', 'yavaş', 'yorgun',
            
            # Türkçe olumsuz ifadeler
            'ah', 'of', 'yazık', 'vah', 'eyvah', 'kötü', 'kızdım', 'sinir',
            'hayal kırıklığı', 'üzgün', 'mutsuz', 'kırgın', 'öfkeli'
        }
        
        # Güçlendirici kelimeler (intensifiers)
        self.intensifiers = {
            'çok': 1.5,
            'aşırı': 1.8,
            'son derece': 2.0,
            'gerçekten': 1.3,
            'kesinlikle': 1.5,
            'tamamen': 1.6,
            'fazla': 1.4,
            'oldukça': 1.3,
            'fevkalade': 2.0
        }
        
        # Olumsuzluk ekleyicileri (negators)
        self.negators = {
            'değil', 'yok', 'asla', 'hiç', 'hiçbir',
            'hayır', 'olmaz', 'mümkün değil'
        }
        
        # Emoji sentiment sözlüğü
        self.emoji_sentiment = {
            '😊': 1.0, '😃': 1.0, '😄': 1.0, '😁': 0.8, '🙂': 0.5,
            '❤️': 1.2, '💚': 1.0, '💙': 1.0, '🔥': 0.8, '👏': 0.7,
            '🎉': 0.9, '🎊': 0.9, '⭐': 0.6, '✨': 0.5, '💪': 0.7,
            
            '😢': -1.0, '😭': -1.2, '😡': -1.5, '😠': -1.3, '😤': -0.8,
            '💔': -1.2, '😞': -0.7, '😔': -0.6, '😕': -0.5, '🙁': -0.6,
            '👎': -0.8, '💩': -1.0, '🤮': -1.5, '🤬': -1.8
        }
    
    def normalize_turkish(self, text: str) -> str:
        """Türkçe karakterleri normalize et"""
        replacements = {
            'ı': 'i', 'İ': 'I', 'ş': 's', 'Ş': 'S',
            'ğ': 'g', 'Ğ': 'G', 'ü': 'u', 'Ü': 'U',
            'ö': 'o', 'Ö': 'O', 'ç': 'c', 'Ç': 'C'
        }
        
        normalized = text.lower()
        for tr_char, en_char in replacements.items():
            normalized = normalized.replace(tr_char, en_char)
        
        return normalized
    
    def extract_emojis(self, text: str) -> List[str]:
        """Emojileri çıkar"""
        # Basit emoji pattern (gerçek implementasyon daha karmaşık olur)
        emoji_pattern = re.compile("["
                                   u"\U0001F600-\U0001F64F"  # emoticons
                                   u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                                   u"\U0001F680-\U0001F6FF"  # transport & map symbols
                                   u"\U0001F1E0-\U0001F1FF"  # flags
                                   u"\U00002702-\U000027B0"
                                   u"\U000024C2-\U0001F251"
                                   "]+", flags=re.UNICODE)
        
        return emoji_pattern.findall(text)
    
    def analyze(self, text: str) -> SentimentScore:
        """
        Metni analiz et ve sentiment skoru döndür
        
        Args:
            text: Analiz edilecek metin
        
        Returns:
            SentimentScore
        """
        if not text or not text.strip():
            return SentimentScore(0.33, 0.33, 0.34, 0.0)
        
        # Metni normalize et
        normalized = self.normalize_turkish(text)
        words = normalized.split()
        
        # Emoji analizini ekle
        emojis = self.extract_emojis(text)
        emoji_score = sum(self.emoji_sentiment.get(e, 0) for e in emojis)
        
        positive_score = 0.0
        negative_score = 0.0
        
        # Kelime bazlı analiz
        for i, word in enumerate(words):
            # Önceki kelime olumsuzluk ekleyici mi?
            has_negator = i > 0 and words[i-1] in self.negators
            
            # Pozitif kelime kontrolü
            if word in self.positive_words:
                score = 1.0
                
                # Güçlendirici kontrol
                if i > 0 and words[i-1] in self.intensifiers:
                    score *= self.intensifiers[words[i-1]]
                
                # Olumsuzluk kontrolü (tersine çevir)
                if has_negator:
                    negative_score += score
                else:
                    positive_score += score
            
            # Negatif kelime kontrolü
            elif word in self.negative_words:
                score = 1.0
                
                # Güçlendirici kontrol
                if i > 0 and words[i-1] in self.intensifiers:
                    score *= self.intensifiers[words[i-1]]
                
                # Olumsuzluk kontrolü (tersine çevir)
                if has_negator:
                    positive_score += score
                else:
                    negative_score += score
        
        # Emoji skorunu ekle
        if emoji_score > 0:
            positive_score += emoji_score
        elif emoji_score < 0:
            negative_score += abs(emoji_score)
        
        # Toplam
        total = positive_score + negative_score
        
        if total == 0:
            # Nötr metin
            return SentimentScore(0.0, 0.0, 1.0, 0.0)
        
        # Normalize et (0-1 arası)
        pos_normalized = positive_score / total
        neg_normalized = negative_score / total
        
        # Compound score (-1 ile +1 arası)
        compound = (positive_score - negative_score) / (total + 1)
        
        # Neutral score
        neutral = 1.0 - (pos_normalized + neg_normalized)
        
        return SentimentScore(
            positive=pos_normalized,
            negative=neg_normalized,
            neutral=max(0, neutral),
            compound=compound
        )
    
    def analyze_batch(self, texts: List[str]) -> List[SentimentScore]:
        """Çoklu metin analizi"""
        return [self.analyze(text) for text in texts]
    
    def get_aggregate_sentiment(self, texts: List[str]) -> SentimentScore:
        """Toplu sentiment (tüm metinlerin ortalaması)"""
        if not texts:
            return SentimentScore(0.33, 0.33, 0.34, 0.0)
        
        scores = self.analyze_batch(texts)
        
        avg_positive = sum(s.positive for s in scores) / len(scores)
        avg_negative = sum(s.negative for s in scores) / len(scores)
        avg_neutral = sum(s.neutral for s in scores) / len(scores)
        avg_compound = sum(s.compound for s in scores) / len(scores)
        
        return SentimentScore(avg_positive, avg_negative, avg_neutral, avg_compound)


class SocialMediaMockData:
    """
    Sosyal medya verisi simülatörü
    Gerçek API yerine demo veri üretir
    """
    
    @staticmethod
    def generate_team_posts(team_name: str, count: int = 50) -> List[SocialPost]:
        """Takım için örnek postlar üret"""
        
        # Örnek tweet şablonları
        templates = [
            # Pozitif
            f"{team_name} harika oynuyor! 🔥",
            f"{team_name} muhteşem bir performans 👏",
            f"{team_name} şampiyonluk yolunda ilerliyor ⭐",
            f"Bu sezon {team_name} çok iyi! 😊",
            f"{team_name} rekor kırıyor 💪",
            f"Bravo {team_name}! Harika galibiyet ❤️",
            f"{team_name} formu yakaladı 🚀",
            f"Efsane {team_name} performansı!",
            
            # Nötr
            f"{team_name} bugün maç var",
            f"{team_name} sahaya çıkıyor",
            f"{team_name} transferi açıklandı",
            f"{team_name} antrenman yaptı",
            
            # Negatif
            f"{team_name} çok kötü oynuyor 😢",
            f"{team_name} yine kaybetti 💔",
            f"Hayal kırıklığı {team_name} 😞",
            f"{team_name} ne yapıyor böyle?! 😡",
            f"{team_name} formsuz 👎",
            f"Berbat {team_name} performansı",
        ]
        
        import random
        from datetime import datetime, timedelta
        
        posts = []
        base_time = datetime.now()
        
        for i in range(count):
            template = random.choice(templates)
            
            post = SocialPost(
                text=template,
                source=random.choice(['twitter', 'reddit']),
                timestamp=base_time - timedelta(hours=random.randint(1, 48)),
                author=f"user{random.randint(1000, 9999)}",
                likes=random.randint(0, 500),
                retweets=random.randint(0, 100)
            )
            
            posts.append(post)
        
        return posts
    
    @staticmethod
    def generate_player_posts(player_name: str, count: int = 30) -> List[SocialPost]:
        """Oyuncu için örnek postlar üret"""
        
        templates = [
            # Pozitif
            f"{player_name} efsane! 🌟",
            f"{player_name} harika gol attı! ⚽",
            f"{player_name} yıldız oyuncu 💫",
            f"Bravo {player_name}! 👏",
            
            # Nötr
            f"{player_name} sahada",
            f"{player_name} ilk 11'de",
            
            # Negatif
            f"{player_name} kötü oynuyor 😞",
            f"{player_name} penaltı kaçırdı 💔",
        ]
        
        import random
        from datetime import datetime, timedelta
        
        posts = []
        base_time = datetime.now()
        
        for i in range(count):
            template = random.choice(templates)
            
            post = SocialPost(
                text=template,
                source=random.choice(['twitter', 'reddit']),
                timestamp=base_time - timedelta(hours=random.randint(1, 24)),
                author=f"user{random.randint(1000, 9999)}",
                likes=random.randint(0, 300),
                retweets=random.randint(0, 50)
            )
            
            posts.append(post)
        
        return posts


# Test
if __name__ == "__main__":
    analyzer = TurkishSentimentAnalyzer()
    
    # Test cümleleri
    test_texts = [
        "Galatasaray harika oynuyor! 🔥",
        "Fenerbahçe çok kötü bir performans sergiledi 😢",
        "Beşiktaş bugün maç var",
        "Messi efsane bir gol attı! Muhteşem! ⚽❤️",
        "Ronaldo penaltı kaçırdı. Hayal kırıklığı 💔",
    ]
    
    for text in test_texts:
        score = analyzer.analyze(text)
        print(f"\nMetin: {text}")
        print(f"Sentiment: {score.get_sentiment_label()} {score.get_emoji()}")
        print(f"Compound: {score.compound:.2f}")
        print(f"Pos: {score.positive:.2f} | Neg: {score.negative:.2f} | Neutral: {score.neutral:.2f}")
    
    print("\n" + "="*50)
    print("✅ Sentiment Analyzer hazır!")
