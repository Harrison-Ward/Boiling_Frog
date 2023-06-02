from datetime import datetime
import logging

from decouple import config
from meteostat import Daily
from meteostat import Point
from meteostat import units
import pandas as pd
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
    logger.info('API credentials successfully verified.')
except Exception:
    logger.info("Failed to authenticate API credentials.")

# fetch weather data from metostat API
N = 30
end = datetime.now()
start = datetime(end.year - N, end.month, end.day)

# Define nyc, weather location
nyc = Point(40.7789, -73.9692, 3.0)

# Fetch the weather series from NYC
data = Daily(nyc, start, end)
data = data.convert(units.imperial)
data = data.fetch()

# Modify the pandas DF to assist in day of year pivot table
data["month"], data["day"] = data.index.month, data.index.day

daily_max_avg = pd.DataFrame(data.tmax.groupby(by=[data.month, data.day]).mean())
daily_max_max = pd.DataFrame(data.tmax.groupby(by=[data.month, data.day]).max())

# Create month, day tuple
daily_max_avg["time"] = daily_max_avg.index.values

today = end.strftime("%Y-%m-%d")
todays_high = data.tmax.loc[today]

month, day = end.month, end.day
todays_avg_high = daily_max_avg.tmax.loc[(month, day)]
todays_max_high = daily_max_max.tmax.loc[(month, day)]

# Compare weather conditions
if todays_high > todays_avg_high:
    forecast_tweet = f"NYC: The high today is {todays_high:.1f}°F, which is {todays_high - todays_avg_high:.1f}°F hotter than today's {N}-year average."
else:
    forecast_tweet = f"NYC: The high today is {todays_high:.1f}°F, which is {todays_high - todays_avg_high:.1f}°F cooler than today's {N}-year average."

forecast_tweet += f"\n\nThe {N}-year historical high for today is {todays_max_high:.1f}°F."

# tweet the takeaway
response = client.create_tweet(text=forecast_tweet)
logger.info(
    f"Today's forecast tweeted: https://twitter.com/user/status/{response.data['id']}"
)
print(f"Today's forecast tweeted: https://twitter.com/user/status/{response.data['id']}")
