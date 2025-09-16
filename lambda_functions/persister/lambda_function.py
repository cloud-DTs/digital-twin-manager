import os
import json
import boto3


DIGITAL_TWIN_INFO = json.loads(os.environ.get("DIGITAL_TWIN_INFO", None))
DYNAMODB_TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME", None)
EVENT_CHECKER_LAMBDA_NAME = os.environ.get("EVENT_CHECKER_LAMBDA_NAME", None)

dynamodb_client = boto3.resource("dynamodb")
dynamodb_table = dynamodb_client.Table(DYNAMODB_TABLE_NAME)
twinmaker_client = boto3.client("iottwinmaker")
lambda_client = boto3.client("lambda")


def lambda_handler(event, context):
    print("Hello from Persister!")
    print("Event: " + json.dumps(event))

    item = event.copy()
    item["id"] = str(item.pop("time"))

    dynamodb_table.put_item(Item=item)

    lambda_client.invoke(FunctionName=EVENT_CHECKER_LAMBDA_NAME, InvocationType="Event", Payload=json.dumps(event).encode("utf-8"))
    