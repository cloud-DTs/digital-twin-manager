import json
import os
import time
from datetime import datetime
import boto3


DIGITAL_TWIN_NAME = os.environ["DIGITAL_TWIN_NAME"]

lambda_client = boto3.client("lambda")


def now_ms():
    return int(time.time() * 1000)


def iso_to_ms(value):
    return int(datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp() * 1000)


def start_trace(event):
    trace = {"dispatcher": now_ms()}
    if "iotRuleTs" in event:
        trace["iot_rule"] = int(event.pop("iotRuleTs"))
    try:
        trace["t0"] = iso_to_ms(event["time"])
    except (KeyError, ValueError):
        pass
    event["_trace"] = trace


def lambda_handler(event, context):
    start_trace(event)
    print("Hello from Dispatcher!")
    print("Event: " + json.dumps(event))

    processor_function_name = DIGITAL_TWIN_NAME + "-" + event["iotDeviceId"] + "-processor"
    lambda_client.invoke(FunctionName=processor_function_name, InvocationType="Event", Payload=json.dumps(event).encode("utf-8"))
