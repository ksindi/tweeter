"""Elasticsearch helper."""

import os
from typing import List

from elastic_enterprise_search import AppSearch

from ssm_store import SSMParameterStore

ES_HOST = os.environ["ES_HOST"]
ENGINE_NAME = os.getenv("ES_ENGINE_NAME", "tweeter")
SSM_PARAMETER_NAME = os.environ["SSM_PARAMETER_NAME"]

PARAMS = SSMParameterStore(prefix=f"/{SSM_PARAMETER_NAME}/es")

ES = AppSearch(ES_HOST, http_auth=PARAMS["private_key"])


def write(tweets: List):
    ES.index_documents(engine_name=ENGINE_NAME, documents=tweets)
