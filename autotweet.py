import os
import random
import tweepy
import requests
from bs4 import BeautifulSoup
import sys
import tempfile

# Konfigurasi
TWEETS_FILE = 'tweets_media.txt'
MAX_TWEET_LENGTH = 250
TRENDING_LIMIT = 5
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'

class TwitterBot:
    def __init__(self):
        self.client = self.authenticate()
        self.api_v1 = self.authenticate_v1()

    def authenticate(self):
        try:
            return tweepy.Client(
                consumer_key=os.getenv('TWITTER_API_KEY'),
                consumer_secret=os.getenv('TWITTER_API_SECRET'),
                access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
                access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
            )
        except Exception as e:
            print(f"❌ Gagal autentikasi (v2): {str(e)}")
            sys.exit(1)

    def authenticate_v1(self):
        try:
            auth = tweepy.OAuthHandler(
                os.getenv('TWITTER_API_KEY'),
                os.getenv('TWITTER_API_SECRET')
            )
            auth.set_access_token(
                os.getenv('TWITTER_ACCESS_TOKEN'),
                os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
            )
            return tweepy.API(auth)
        except Exception as e:
            print(f"❌ Gagal autentikasi (v1.1): {str(e)}")
            return None

    def get_twitter_trends(self):
        """
        --- TIDAK DIUBAH SAMA SEKALI DARI VERSI ANDA ---
        Menggunakan logika scraping yang sudah terbukti berhasil.
        """
        print("🔍 Mengambil tren dari trends24.in (menggunakan logika asli Anda)...")
        try:
            url = "https://www.trends24.in/indonesia/"
            headers = {'User-Agent': USER_AGENT}
            response = requests.get(url, headers=headers, timeout=20)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            trends = []
            
            # Menggunakan selector luas yang terbukti bisa mendapatkan data
            for item in soup.select('.trend-card__list a'):
                text = item.get_text(strip=True)
                if text:
                    trends.append(text)

            print(f"✅ Berhasil mendapatkan {len(trends)} item mentah dari trends24.in.")
            
            # Mengambil dari atas sesuai limit, tanpa diacak.
            return trends[:TRENDING_LIMIT]
        except Exception as e:
            print(f"⚠️ Gagal mengambil trending: {str(e)}")
            return ['#Trending', '#Viral'] # Fallback jika gagal

    def parse_tweets_file(self):
        """Membaca file dan menangani format multi-baris."""
        print("📖 Membaca file tweets_media.txt...")
        tweets = []
        try:
            with open(TWEETS_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
            tweet_blocks = content.strip().split('---')
            for block in tweet_blocks:
                if not block.strip(): continue
                lines = block.strip().split('\n')
                current_tweet = {}
                current_key = None
                buffer = {}
                for line in lines:
                    parts = line.split(':', 1)
                    if len(parts) == 2 and parts[0].lower() in ['text', 'media', 'hashtags']:
                        current_key = parts[0].lower()
                        buffer[current_key] = [parts[1].strip()]
                    elif current_key:
                        buffer[current_key].append(line)
                for key, value_lines in buffer.items():
                    current_tweet[key] = "\n".join(value_lines).strip()
                if 'text' in current_tweet:
                    current_tweet.setdefault('hashtags', '')
                    current_tweet.setdefault('media', '')
                    tweets.append(current_tweet)
            for tweet in tweets:
                tweet['media'] = [url.strip() for url in tweet['media'].split(',') if url.strip()]
                tweet['hashtags'] = [tag.strip() for tag in tweet['hashtags'].split() if tag.strip()]
            if not tweets: raise ValueError("Tidak ada tweet yang valid ditemukan")
            return tweets
        except Exception as e:
            print(f"❌ Gagal parsing tweet: {e}")
            sys.exit(1)

    def compose_tweet(self, base_text, media_links, default_hashtags):
        """
        --- FUNGSI YANG DIPERBAIKI ---
        Menyusun tweet, memasukkan frase apa adanya tanpa tanda '#'.
        """
        top_part = base_text
        
        scraped_items = self.get_twitter_trends()
        all_items = scraped_items + default_hashtags
        
        addon_part = ""
        available_space = MAX_TWEET_LENGTH - len(top_part) - 2
        
        unique_items = []
        for item in all_items:
            item = item.strip()
            if not item: continue

            # --- LOGIKA BARU SESUAI PERMINTAAN ANDA ---
            # Jika item adalah bagian dari hashtag default Anda, pastikan diawali '#'
            if item in default_hashtags:
                if not item.startswith('#'):
                    item = '#' + item
            # Jika item dari hasil scraping, biarkan apa adanya (tidak ditambah '#')
            
            if item not in unique_items:
                if len(addon_part) + len(item) + 1 <= available_space:
                    addon_part += f" {item}"
                    unique_items.append(item)
        
        tweet_text = f'{top_part}\n\n{addon_part.strip()}'

        media_id = None
        if media_links:
            random_media = random.choice(media_links)
            if media_path := self.download_media(random_media):
                media_id = self.upload_media(media_path)
        
        return tweet_text, media_id

    def post_tweet(self):
        """Mengambil data, menyusun, dan memposting tweet."""
        tweets = self.parse_tweets_file()
        if not tweets:
            print("❌ Tidak ada data tweet untuk diproses.")
            return False
        selected_tweet = random.choice(tweets)
        base_text = selected_tweet.get('text', '')
        media_links = selected_tweet.get('media', [])
        hashtags = selected_tweet.get('hashtags', [])
        tweet_text, media_id = self.compose_tweet(base_text, media_links, hashtags)
        try:
            if media_id:
                response = self.client.create_tweet(text=tweet_text, media_ids=[media_id])
            else:
                response = self.client.create_tweet(text=tweet_text)
            print(f"✅ Tweet berhasil diposting! ID: {response.data['id']}")
            return True
        except tweepy.errors.TweepyException as e:
            print(f"❌ Error Twitter: {str(e)}")
            return False
        except Exception as e:
            print(f"❌ Error tidak terduga: {str(e)}")
            return False
    
    def download_media(self, url):
        try:
            headers = {'User-Agent': USER_AGENT}
            response = requests.get(url, headers=headers, stream=True, timeout=15)
            response.raise_for_status()
            content_type = response.headers.get('content-type', '')
            ext = '.jpg'
            if 'png' in content_type: ext = '.png'
            elif 'gif' in content_type: ext = '.gif'
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    tmp_file.write(chunk)
                return tmp_file.name
        except Exception as e:
            print(f"⚠️ Gagal download media: {str(e)}")
            return None

    def upload_media(self, media_path):
        if not self.api_v1: return None
        try:
            media = self.api_v1.media_upload(filename=media_path)
            return media.media_id_string
        except Exception as e:
            print(f"⚠️ Gagal upload media: {str(e)}")
            return None
        finally:
            try: os.unlink(media_path)
            except: pass

if __name__ == "__main__":
    print("\n=== 🚀 Twitter Bot (Sesuai Permintaan Final) ===")
    bot = TwitterBot()
    if bot.post_tweet():
        print("✅ Berhasil")
        sys.exit(0)
    else:
        print("❌ Gagal")
        sys.exit(1)
