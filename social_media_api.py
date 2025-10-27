"""
Sosyal Medya API Entegrasyonu
Twitter (X) ve Reddit gerçek veri çekme
"""

import os
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from sentiment_analyzer import SocialPost
import json


class TwitterAPIClient:
    """
    Twitter API v2 istemcisi
    Ücretsiz tier: 1500 tweet/ay
    """
    
    def __init__(self, bearer_token: Optional[str] = None):
        """
        Args:
            bearer_token: Twitter API Bearer Token
        """
        self.bearer_token = bearer_token or os.getenv('TWITTER_BEARER_TOKEN')
        self.api_available = self.bearer_token is not None
        
        if self.api_available:
            try:
                import tweepy
                self.tweepy = tweepy
                self.client = tweepy.Client(bearer_token=self.bearer_token)
                print("✅ Twitter API bağlantısı başarılı")
            except ImportError:
                print("⚠️ tweepy kurulu değil. pip install tweepy")
                self.api_available = False
            except Exception as e:
                print(f"⚠️ Twitter API bağlantı hatası: {e}")
                self.api_available = False
        else:
            print("ℹ️ Twitter API token yok, mock data kullanılacak")
    
    def search_tweets(self, query: str, max_results: int = 100) -> List[SocialPost]:
        """
        Twitter'da arama yap
        
        Args:
            query: Arama sorgusu (örn: "Galatasaray")
            max_results: Maksimum tweet sayısı (10-100 arası)
        
        Returns:
            SocialPost listesi
        """
        if not self.api_available:
            return self._mock_tweets(query, max_results)
        
        try:
            # API v2 search (son 7 gün)
            response = self.client.search_recent_tweets(
                query=f"{query} lang:tr -is:retweet",
                max_results=min(max_results, 100),
                tweet_fields=['created_at', 'public_metrics', 'author_id'],
                expansions=['author_id'],
                user_fields=['username']
            )
            
            if not response.data:
                print(f"⚠️ '{query}' için tweet bulunamadı")
                return self._mock_tweets(query, max_results)
            
            # Users dict oluştur
            users = {}
            if response.includes and 'users' in response.includes:
                users = {user.id: user.username for user in response.includes['users']}
            
            posts = []
            for tweet in response.data:
                # Metrikleri al
                metrics = tweet.public_metrics
                
                # Author username
                author = users.get(tweet.author_id, f"user_{tweet.author_id}")
                
                post = SocialPost(
                    text=tweet.text,
                    source='twitter',
                    timestamp=tweet.created_at,
                    author=author,
                    likes=metrics['like_count'],
                    retweets=metrics['retweet_count']
                )
                posts.append(post)
            
            print(f"✅ Twitter'dan {len(posts)} tweet çekildi")
            return posts
            
        except Exception as e:
            print(f"❌ Twitter API hatası: {e}")
            return self._mock_tweets(query, max_results)
    
    def _mock_tweets(self, query: str, count: int) -> List[SocialPost]:
        """Mock tweet data üret"""
        from sentiment_analyzer import SocialMediaMockData
        print(f"ℹ️ Mock data kullanılıyor ({count} tweet)")
        return SocialMediaMockData.generate_team_posts(query, count)


class RedditAPIClient:
    """
    Reddit API istemcisi
    PRAW (Python Reddit API Wrapper) kullanır
    """
    
    def __init__(self, client_id: Optional[str] = None, 
                 client_secret: Optional[str] = None,
                 user_agent: str = "football_analysis_bot"):
        """
        Args:
            client_id: Reddit App Client ID
            client_secret: Reddit App Secret
            user_agent: User agent string
        """
        self.client_id = client_id or os.getenv('REDDIT_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('REDDIT_CLIENT_SECRET')
        self.user_agent = user_agent
        self.api_available = self.client_id and self.client_secret
        
        if self.api_available:
            try:
                import praw
                self.praw = praw
                self.reddit = praw.Reddit(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    user_agent=self.user_agent
                )
                print("✅ Reddit API bağlantısı başarılı")
            except ImportError:
                print("⚠️ praw kurulu değil. pip install praw")
                self.api_available = False
            except Exception as e:
                print(f"⚠️ Reddit API bağlantı hatası: {e}")
                self.api_available = False
        else:
            print("ℹ️ Reddit API credentials yok, mock data kullanılacak")
    
    def search_posts(self, query: str, subreddit: str = 'soccer', 
                     limit: int = 100) -> List[SocialPost]:
        """
        Reddit'te arama yap
        
        Args:
            query: Arama sorgusu
            subreddit: Subreddit adı (varsayılan: soccer)
            limit: Maksimum post sayısı
        
        Returns:
            SocialPost listesi
        """
        if not self.api_available:
            return self._mock_posts(query, limit)
        
        try:
            # Subreddit'i al
            sub = self.reddit.subreddit(subreddit)
            
            # Arama yap
            posts = []
            for submission in sub.search(query, limit=limit, time_filter='week'):
                # Post + üst yorumları al
                post = SocialPost(
                    text=f"{submission.title}\n{submission.selftext}",
                    source='reddit',
                    timestamp=datetime.fromtimestamp(submission.created_utc),
                    author=str(submission.author),
                    likes=submission.score,
                    retweets=submission.num_comments
                )
                posts.append(post)
                
                # İlk 3 yorumu da ekle
                submission.comments.replace_more(limit=0)
                for comment in list(submission.comments)[:3]:
                    comment_post = SocialPost(
                        text=comment.body,
                        source='reddit',
                        timestamp=datetime.fromtimestamp(comment.created_utc),
                        author=str(comment.author),
                        likes=comment.score,
                        retweets=0
                    )
                    posts.append(comment_post)
            
            print(f"✅ Reddit'ten {len(posts)} post çekildi")
            return posts
            
        except Exception as e:
            print(f"❌ Reddit API hatası: {e}")
            return self._mock_posts(query, limit)
    
    def _mock_posts(self, query: str, count: int) -> List[SocialPost]:
        """Mock Reddit data üret"""
        from sentiment_analyzer import SocialMediaMockData
        print(f"ℹ️ Mock data kullanılıyor ({count} post)")
        return SocialMediaMockData.generate_team_posts(query, count)


class SocialMediaAggregator:
    """
    Birden fazla sosyal medya kaynağını birleştir
    """
    
    def __init__(self, twitter_token: Optional[str] = None,
                 reddit_id: Optional[str] = None,
                 reddit_secret: Optional[str] = None):
        """
        Args:
            twitter_token: Twitter Bearer Token
            reddit_id: Reddit Client ID
            reddit_secret: Reddit Client Secret
        """
        self.twitter = TwitterAPIClient(twitter_token)
        self.reddit = RedditAPIClient(reddit_id, reddit_secret)
    
    def fetch_all(self, query: str, max_per_source: int = 50) -> List[SocialPost]:
        """
        Tüm kaynaklardan veri çek
        
        Args:
            query: Arama sorgusu
            max_per_source: Her kaynaktan maksimum post
        
        Returns:
            Birleştirilmiş SocialPost listesi
        """
        all_posts = []
        
        # Twitter
        print(f"\n🐦 Twitter'dan '{query}' aranıyor...")
        twitter_posts = self.twitter.search_tweets(query, max_per_source)
        all_posts.extend(twitter_posts)
        
        # Reddit
        print(f"\n🤖 Reddit'ten '{query}' aranıyor...")
        reddit_posts = self.reddit.search_posts(query, limit=max_per_source)
        all_posts.extend(reddit_posts)
        
        # Zamana göre sırala (en yeni önce)
        all_posts.sort(key=lambda p: p.timestamp, reverse=True)
        
        print(f"\n✅ Toplam {len(all_posts)} post çekildi")
        print(f"   - Twitter: {len([p for p in all_posts if p.source == 'twitter'])}")
        print(f"   - Reddit: {len([p for p in all_posts if p.source == 'reddit'])}")
        
        return all_posts
    
    def get_api_status(self) -> Dict[str, bool]:
        """API durumlarını kontrol et"""
        return {
            'twitter': self.twitter.api_available,
            'reddit': self.reddit.api_available,
            'any_available': self.twitter.api_available or self.reddit.api_available
        }


# Streamlit için kolay import
def create_social_aggregator() -> SocialMediaAggregator:
    """
    Streamlit secrets'tan veya environment'tan API credentials alarak
    aggregator oluştur
    """
    try:
        import streamlit as st
        
        # Streamlit secrets'tan al
        twitter_token = st.secrets.get("TWITTER_BEARER_TOKEN")
        reddit_id = st.secrets.get("REDDIT_CLIENT_ID")
        reddit_secret = st.secrets.get("REDDIT_CLIENT_SECRET")
        
    except Exception:
        # Environment variables'dan al
        twitter_token = os.getenv('TWITTER_BEARER_TOKEN')
        reddit_id = os.getenv('REDDIT_CLIENT_ID')
        reddit_secret = os.getenv('REDDIT_CLIENT_SECRET')
    
    return SocialMediaAggregator(twitter_token, reddit_id, reddit_secret)


# Test
if __name__ == "__main__":
    print("="*60)
    print("Sosyal Medya API Testi")
    print("="*60)
    
    # Aggregator oluştur
    aggregator = SocialMediaAggregator()
    
    # API durumu
    status = aggregator.get_api_status()
    print(f"\n📊 API Durumu:")
    print(f"   Twitter: {'✅ Aktif' if status['twitter'] else '❌ Pasif (mock kullanılacak)'}")
    print(f"   Reddit: {'✅ Aktif' if status['reddit'] else '❌ Pasif (mock kullanılacak)'}")
    
    # Test sorgusu
    query = "Galatasaray"
    print(f"\n🔍 Test sorgusu: '{query}'")
    
    posts = aggregator.fetch_all(query, max_per_source=10)
    
    print(f"\n📱 İlk 3 Post:")
    for i, post in enumerate(posts[:3], 1):
        print(f"\n{i}. {post.source.upper()} - @{post.author}")
        print(f"   {post.text[:100]}...")
        print(f"   ❤️ {post.likes} | 🔄 {post.retweets}")
    
    print("\n" + "="*60)
    print("✅ Sosyal Medya API modülü hazır!")
    print("="*60)
