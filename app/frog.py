from datetime import datetime
import logging

from decouple import config
import matplotlib.pyplot as plt
from meteostat import Daily
from meteostat import Point
from meteostat import units
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import SplineTransformer
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
    logger.info("Tweepy V2 API credentials successfully verified.")
except Exception:
    logger.info("Failed to authenticate Tweepy V2 API credentials.")

try:
    auth = tweepy.OAuth1UserHandler(
        consumer_key, consumer_secret, access_token, access_token_secret
    )
    api = tweepy.API(auth)
    logger.info("Tweepy V1 API credentials successfully verified.")
except Exception:
    logger.info("Failed to authenticate Tweepy V1 API credentials.")


# fetch weather data from metostat API
N = 75
end = datetime.now()
start = datetime(end.year - N, end.month, end.day)

# Define nyc, weather location
nyc = Point(40.7789, -73.9692, 3.0)

# Fetch the weather series from NYC
data = Daily(nyc, start, end)
data = data.convert(units.imperial)
data = data.fetch()

# Modify the pandas DF to assist in day of year pivot table
data["year"], data["month"], data["day"] = (
    data.index.year,
    data.index.month,
    data.index.day,
)

daily_max_avg = pd.DataFrame(data.tmax.groupby(by=[data.month, data.day]).mean())
daily_max_max = pd.DataFrame(data.tmax.groupby(by=[data.month, data.day]).max())

# Create month, day tuple
daily_max_avg["time"] = daily_max_avg.index.values

today = end.strftime("%Y-%m-%d")
todays_high = data.tmax.loc[today]

Month, Day, Year = end.month, end.day, end.year
todays_avg_high = daily_max_avg.tmax.loc[(Month, Day)]
todays_max_high = daily_max_max.tmax.loc[(Month, Day)]

# Compare weather conditions
if todays_high > todays_avg_high:
    forecast_tweet = f"NYC: The high today is {todays_high:.1f}°F, which is {todays_high - todays_avg_high:.1f}°F hotter than today's {N}-year average."
else:
    forecast_tweet = f"NYC: The high today is {todays_high:.1f}°F, which is {todays_high - todays_avg_high:.1f}°F cooler than today's {N}-year average."

forecast_tweet += (
    f"\n\nThe {N}-year historical high for today is {todays_max_high:.1f}°F."
)

# generate dataframe for scatter plot
pd.options.mode.chained_assignment = None
daily_hist_series = data[(data["month"] == Month) & (data["day"] == Day)]
daily_hist_series["most_recent"] = np.where(
    daily_hist_series["year"] == daily_hist_series["year"].max(), 1, 0
)

# fit the spline to the trends over the last N years
x, y = daily_hist_series["year"].values.reshape(-1, 1), daily_hist_series[
    ["tmax"]
].values.reshape(-1, 1)
model = make_pipeline(SplineTransformer(n_knots=4, degree=2), Ridge(alpha=1e-3))
model.fit(x, y)

x_plot = np.linspace(Year - N, Year, 500).reshape(-1, 1)
y_plot = model.predict(x_plot)

pct_bound = 0.1

upper_ci = y_plot + (1.96 * np.std(y) / np.sqrt(N + 1))
lower_ci = y_plot - (1.96 * np.std(y) / np.sqrt(N + 1))

# plot the weather data
plt.style.use("fivethirtyeight")
plt.rcParams["figure.figsize"] = (16, 9)

plt.scatter(
    daily_hist_series["year"][daily_hist_series["most_recent"] == 0],
    daily_hist_series["tmax"][daily_hist_series["most_recent"] == 0],
    color="gray",
    zorder=2,
)
plt.scatter(
    daily_hist_series["year"][daily_hist_series["most_recent"] == 1],
    daily_hist_series["tmax"][daily_hist_series["most_recent"] == 1],
    color="red",
    label="Today",
    zorder=3,
)

plt.plot(x_plot, y_plot, color="Black", zorder=1, label="Trend")

plt.fill_between(
    x_plot.reshape(-1),
    upper_ci.reshape(-1),
    lower_ci.reshape(-1),
    color="tomato",
    zorder=1,
    alpha=0.3,
    label="95% Confidence Interval",
)


plt.xlabel("Year")
plt.ylabel("Daily High")
plt.title("Daily High by Year")
plt.legend(loc="upper left")
plt.savefig("daily_plot.jpeg")

media = api.media_upload(filename="daily_plot.jpeg")

# tweet the takeaway
response = client.create_tweet(text=forecast_tweet, media_ids=[media.media_id_string])
logger.info(
    f"Today's forecast tweeted: https://twitter.com/user/status/{response.data['id']}"
)
print(
    f"Today's forecast tweeted: https://twitter.com/user/status/{response.data['id']}"
)
