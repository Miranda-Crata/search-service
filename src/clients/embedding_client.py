import json
import os
import boto3

from src.settings import EMBEDDING_MODEL_ID, EMBEDDING_DIMENSIONS, BEDROCK_REGION

_embedding_client = None


def _get_client():
    global _embedding_client
    if _embedding_client is None:
        _embedding_client = boto3.client(
            "bedrock-runtime",
            region_name=os.environ.get("AWS_REGION", BEDROCK_REGION),
        )
    return _embedding_client


def generate_embedding(text):
    client = _get_client()

    body = json.dumps({
        "inputText": text,
        "dimensions": EMBEDDING_DIMENSIONS,
    })

    response = client.invoke_model(
        modelId=EMBEDDING_MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=body,
    )

    result = json.loads(response["body"].read())
    return result["embedding"]
