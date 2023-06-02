from decouple import config
import logging
import os 
import tweepy

logger = logging.getLogger()

bearer_token = config('BEARER_TOKEN')
consumer_key = config('CONSUMER_KEY')
consumer_secret = config('CONSUMER_SECRET')
access_token = config('ACCESS_TOKEN')
access_token_secret = config('ACCESS_TOKEN_SECRET')


try:
    client = tweepy.Client(consumer_key = consumer_key, consumer_secret = consumer_secret, access_token = access_token, access_token_secret = access_token_secret)
except:
    print('Failed: {e}')
    logger.info('Failed to authenticate API credentials')


response = client.create_tweet(
    text="This Tweet was Tweeted using Tweepy and Twitter API v2!"
)
print(f"https://twitter.com/user/status/{response.data['id']}")