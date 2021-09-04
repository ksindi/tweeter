import itertools
import os
from typing import Dict, Iterable

from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

import checkpoint
import db_writer
import twitter_client

tracer = Tracer()
logger = Logger()
metrics = Metrics()

SCREEN_NAME = os.environ["SCREEN_NAME"]
BATCH_SIZE = int(os.environ["BATCH_SIZE"])
METHODS = os.getenv("METHODS", "user_timeline,favorites").split(",")
STREAM_MODE_ENABLED = os.environ["STREAM_MODE_ENABLED"] == "true"


@metrics.log_metrics(capture_cold_start_metric=True)
@logger.inject_lambda_context(log_event=True)
@tracer.capture_lambda_handler
def lambda_handler(event: Dict, context: LambdaContext):
    num_tweets = 0
    for method in METHODS:
        for i, tweets in enumerate(_batch_tweets(method)):
            db_writer.write(tweets)
            num_tweets += len(tweets)
            logger.info("%d tweets written so far", num_tweets)


def _chunker(iterable: Iterable, n: int):
    it = iter(iterable)
    while True:
        chunk = tuple(itertools.islice(it, n))
        if not chunk:
            return
        yield chunk


@tracer.capture_method
def _batch_tweets(method):
    since_id = None
    if STREAM_MODE_ENABLED:
        since_id = checkpoint.last_id(f"checkpoint_{method}")
        logger.info("Stream mode is enabled. Starting from checkpoint '%s'.", since_id)

    # chunk tweets so that we can checkpoint regularly
    for tweets in _chunker(twitter_client.iter_tweets(method, SCREEN_NAME, since_id), BATCH_SIZE):
        yield tweets

        since_id = tweets[0]["id"]

        if STREAM_MODE_ENABLED:
            checkpoint.update(f"checkpoint_{method}", since_id)
