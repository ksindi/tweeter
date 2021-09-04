"""Twitter API Helper."""

import datetime
import os

from aws_lambda_powertools import Logger
import tweepy

from ssm_store import SSMParameterStore

logger = Logger()

SSM_PARAMETER_NAME = os.environ["SSM_PARAMETER_NAME"]

PARAMS = SSMParameterStore(prefix=f"/{SSM_PARAMETER_NAME}/twitter")


def _get_full_text(tweet):
    # Twitter truncates the tweet in the text field
    if hasattr(tweet, "retweeted_status"):  # Check if Retweet
        try:
            return tweet.retweeted_status.full_text
        except AttributeError:
            return tweet.retweeted_status.text
    else:
        try:
            return tweet.full_text
        except AttributeError:
            return tweet.text


def _get_original_author(tweet):
    if hasattr(tweet, "retweeted_status"):  # Check if Retweet
        return tweet.retweeted_status.author.name
    else:
        return tweet.author.name


def _get_screen_name(tweet):
    if hasattr(tweet, "retweeted_status"):  # Check if Retweet
        return tweet.retweeted_status.author.screen_name
    else:
        return tweet.author.screen_name


def _get_tweet_url(tweet):
    screen_name = _get_screen_name(tweet)
    return f"https://twitter.com/{screen_name}/status/{tweet.id_str}"


def _determine_source_type(method, tweet):
    if method == "favorites":
        return "liked"
    elif hasattr(tweet, "retweeted_status"):
        return "retweet"
    else:
        return "original"


def iter_tweets(method, screen_name, since_id=None):
    # Twitter only allows access to a users most recent 3,240 tweets
    for tweet in tweepy.Cursor(
        getattr(API, method),
        screen_name=screen_name,
        since_id=since_id,
        count=200,  # max count
        tweet_mode="extended",
    ).items():
        yield {
            "id": tweet.id,
            "url": _get_tweet_url(tweet),
            "created_at": tweet.created_at.isoformat(),
            "full_text": _get_full_text(tweet),
            "source_type": _determine_source_type(method, tweet),
            "original_author": _get_original_author(tweet),
            "updated_at": datetime.datetime.utcnow().isoformat(),
        }


def _create_twitter_api():
    auth = tweepy.OAuthHandler(PARAMS["consumer_key"], PARAMS["consumer_secret"])
    auth.set_access_token(PARAMS["access_token"], PARAMS["access_token_secret"])
    api = tweepy.API(auth, wait_on_rate_limit_notify=True, wait_on_rate_limit=True)

    try:
        api.me()
    except tweepy.error.TweepError as e:
        logger.error("Please check the authentication information:\n%s", str(e))
        raise e
    else:
        logger.info("Twitter client initalized")
        return api


API = _create_twitter_api()
