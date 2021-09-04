from typing import Dict

from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.data_classes.dynamo_db_stream_event import DynamoDBStreamEvent

import es_client

tracer = Tracer()
logger = Logger()
metrics = Metrics()


def _deserialize(ddb_record):
    return {k: v.get_value for k, v in ddb_record.items()}


@metrics.log_metrics(capture_cold_start_metric=True)
@logger.inject_lambda_context(log_event=True)
@tracer.capture_lambda_handler
def lambda_handler(event: Dict, context: LambdaContext):
    event: DynamoDBStreamEvent = DynamoDBStreamEvent(event)

    docs = [_deserialize(record.dynamodb.new_image) for record in event.records]
    es_client.write(docs)
