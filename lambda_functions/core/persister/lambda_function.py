import os
import json
import boto3
from decimal import Decimal


DIGITAL_TWIN_INFO = json.loads(os.environ.get("DIGITAL_TWIN_INFO", None))
DYNAMODB_TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME", None)
EVENT_CHECKER_LAMBDA_NAME = os.environ.get("EVENT_CHECKER_LAMBDA_NAME", None)

dynamodb_client = boto3.resource("dynamodb")
dynamodb_table = dynamodb_client.Table(DYNAMODB_TABLE_NAME)
twinmaker_client = boto3.client("iottwinmaker")
lambda_client = boto3.client("lambda")


def floats_to_decimals(obj):
    if isinstance(obj, list):
        return [floats_to_decimals(x) for x in obj]
    elif isinstance(obj, dict):
        return {k: floats_to_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, float):
        return Decimal(str(obj))
    else:
        return obj

def lambda_handler(event, context):
    print("Hello from Persister!")
    print("Event: " + json.dumps(event))

    item = event.copy()
    item["id"] = str(item.pop("time"))
    item = floats_to_decimals(item)

    dynamodb_table.put_item(Item=item)

    lambda_client.invoke(FunctionName=EVENT_CHECKER_LAMBDA_NAME, InvocationType="Event", Payload=json.dumps(event).encode("utf-8"))
