"""Write tweets to dynamodb."""

import os

import boto3

ENV = os.environ["ENVIRONMENT"]
ENDPOINT_URL = "http://localstack:4566" if ENV == "localstack" else None

DDB = boto3.resource("dynamodb", endpoint_url=ENDPOINT_URL)
TABLE = DDB.Table(os.environ["TWEETS_TABLE_NAME"])


def write(tweets):
    """Write tweets in batches."""
    with TABLE.batch_writer() as batch:
        for tweet in tweets:
            batch.put_item(Item=tweet)
