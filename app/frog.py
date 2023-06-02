import logging

from decouple import config
import tweepy

logger = logging.getLogger()

bearer_token = config("BEARER_TOKEN")
consumer_key = config("CONSUMER_KEY")
consumer_secret = config("CONSUMER_SECRET")
access_token = config("ACCESS_TOKEN")
access_token_secret = config("ACCESS_TOKEN_SECRET")


try:
    client = tweepy.Client(
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        access_token=access_token,
        access_token_secret=access_token_secret,
    )
except Exception:
    logger.info("Failed to authenticate API credentials")
