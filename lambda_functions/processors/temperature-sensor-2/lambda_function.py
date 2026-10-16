import os
import json
import time
import boto3


PERSISTER_LAMBDA_NAME = os.environ.get("PERSISTER_LAMBDA_NAME", None)

lambda_client = boto3.client("lambda")


def process(event):
    payload = event.copy()
    payload["temperature"] = 30
    return payload


def lambda_handler(event, context):
    print("Hello from temperature-sensor-2 Processor!")
    print("Event: " + json.dumps(event))

    payload = process(event)
    payload.setdefault("_trace", {})["processor"] = int(time.time() * 1000)

    lambda_client.invoke(FunctionName=PERSISTER_LAMBDA_NAME, InvocationType="Event", Payload=json.dumps(payload).encode("utf-8"))
