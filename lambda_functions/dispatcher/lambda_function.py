import json
import os
import boto3


DIGITAL_TWIN_INFO = json.loads(os.environ.get("DIGITAL_TWIN_INFO", None))

lambda_client = boto3.client("lambda")


def lambda_handler(event, context):
    print("Hello from Dispatcher!")
    print("Event: " + json.dumps(event))

    processor_function_name = DIGITAL_TWIN_INFO["config"]["digital_twin_name"] + "-" + event["iotDeviceId"] + "-processor"
    lambda_client.invoke(FunctionName=processor_function_name, InvocationType="Event", Payload=json.dumps(event).encode("utf-8"))
