import json
import os
import boto3


LAYER_INFO = json.loads(os.environ.get("LAYER_INFO", None))

lambda_client = boto3.client("lambda")


def lambda_handler(event, context):
    payload = event.copy()
    payload.pop("topic", None)

    if LAYER_INFO["layer_2_provider"].lower() == "aws":
        processor_function_name = event["topic"].split('/', 1)[1] + "-processor"
        lambda_client.invoke(FunctionName=processor_function_name, InvocationType="Event", Payload=json.dumps(payload).encode("utf-8"))

    elif LAYER_INFO["layer_2_provider"].lower() == "azure":
        print("TODO AZURE")

    else:
        print("UNKNOWN LAYER_INFO")
