import os
import json
import boto3


PERSISTER_LAMBDA_NAME = os.environ.get("PERSISTER_LAMBDA_NAME", None)

lambda_client = boto3.client("lambda")


def process(event):
    payload = event.copy()
    payload["pressure"] = 20
    return payload


def lambda_handler(event, context):
    payload = process(event)
    lambda_client.invoke(FunctionName=PERSISTER_LAMBDA_NAME, InvocationType="Event", Payload=json.dumps(payload).encode("utf-8"))