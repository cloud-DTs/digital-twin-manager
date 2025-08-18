import os
import json
import boto3

lambda_client = boto3.client("lambda")

PERSISTER_LAMBDA_NAME = os.environ.get("PERSISTER_LAMBDA_NAME", "persister")

def lambda_handler(event, context):
    lambda_client.invoke(
        FunctionName=PERSISTER_LAMBDA_NAME,
        InvocationType="Event",
        Payload=json.dumps(event).encode("utf-8")
    )