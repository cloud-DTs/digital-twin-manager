import os
import json
import boto3


LAYER_INFO = json.loads(os.environ.get("LAYER_INFO", None))
DYNAMODB_TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME", None)
TWINMAKER_WORKSPACE_NAME = os.environ.get("TWINMAKER_WORKSPACE_NAME", None)


def lambda_handler(event, context):
    # push data into dynamoDb
    # push data into twinmaker (batch_put_property_values)
    # push data into azure digital twins

    print("Hello from Persister!")
    print("Event: " + json.dumps(event))
