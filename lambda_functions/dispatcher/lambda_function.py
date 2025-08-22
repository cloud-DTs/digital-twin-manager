import json
import os
import boto3


DIGITAL_TWIN_INFO = json.loads(os.environ.get("DIGITAL_TWIN_INFO", None))

lambda_client = boto3.client("lambda")


def lambda_handler(event, context):
    if DIGITAL_TWIN_INFO["layer_2_provider"].lower() == "aws":
        processor_function_name = event["iot_device_id"] + "-processor"
        lambda_client.invoke(FunctionName=processor_function_name, InvocationType="Event", Payload=json.dumps(event).encode("utf-8"))

    elif DIGITAL_TWIN_INFO["layer_2_provider"].lower() == "azure":
        print("TODO AZURE")

    else:
        print("UNKNOWN DIGITAL_TWIN_INFO")
