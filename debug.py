import os
import tweepy

print("Checking environment variables...")
print("API_KEY:", bool(os.getenv('TWITTER_API_KEY')))
print("API_SECRET:", bool(os.getenv('TWITTER_API_SECRET')))

client = tweepy.Client(
    consumer_key=os.getenv('TWITTER_API_KEY'),
    consumer_secret=os.getenv('TWITTER_API_SECRET'),
    access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
    access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
)

try:
    response = client.get_me()
    print("Auth success! User:", response.data.username)
    test_tweet = client.create_tweet(text="Test tweet from GitHub Actions")
    print("Tweet posted:", test_tweet.data)
except Exception as e:
    print("ERROR:", str(e))
