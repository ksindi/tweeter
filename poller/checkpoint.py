"""Manages user timeline checkpoint (used when stream mode enabled)."""

import os

import boto3
from boto3.dynamodb.conditions import Attr, Or
from botocore.exceptions import ClientError

DDB = boto3.resource("dynamodb")
TABLE = DDB.Table(os.environ["TIMELINE_CHECKPOINT_TABLE_NAME"])


def last_id(record_key: str):
    """Return last checkpoint tweet id."""
    result = TABLE.get_item(Key={"id": record_key})
    if "Item" in result:
        return result["Item"]["since_id"]
    return None


def update(record_key: str, since_id: int):
    """Update checkpoint to given tweet id."""
    try:
        TABLE.put_item(
            Item={"id": record_key, "since_id": since_id},
            ConditionExpression=Or(
                Attr("id").not_exists(), Attr("since_id").lt(since_id)
            ),
        )
    except ClientError as e:
        if e.response["Error"]["Code"] != "ConditionalCheckFailedException":
            raise
