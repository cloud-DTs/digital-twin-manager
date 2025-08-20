import os
import json
import boto3


LAYER_INFO = json.loads(os.environ.get("LAYER_INFO", None))
PERSISTER_LAMBDA_NAME = os.environ.get("PERSISTER_LAMBDA_NAME", None)

lambda_client = boto3.client("lambda")


def process(event):
    payload = event.copy()
    payload["pressure"] = 20
    return payload


def lambda_handler(event, context):
    payload = process(event)

    if LAYER_INFO["layer_3_provider"].lower() == "aws":
        lambda_client.invoke(FunctionName=PERSISTER_LAMBDA_NAME, InvocationType="Event", Payload=json.dumps(payload).encode("utf-8"))

    elif LAYER_INFO["layer_3_provider"].lower() == "azure":
        print("TODO AZURE")

    else:
        print("UNKNOWN LAYER_INFO")

