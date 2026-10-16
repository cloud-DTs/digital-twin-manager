import os
import json
import time
import boto3
from decimal import Decimal

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

def now_ms():
    return int(time.time() * 1000)


def emit_latency_metrics(event):
    """Print per-hop latencies (ms) as a CloudWatch EMF record; no-op without a trace."""
    trace = event.get("_trace")
    if not trace:
        return
    hops = [
        ("DeviceToIotRuleMs", "t0", "iot_rule"),
        ("IotRuleToDispatcherMs", "iot_rule", "dispatcher"),
        ("DispatcherToProcessorMs", "dispatcher", "processor"),
        ("ProcessorToPersisterMs", "processor", "persister_in"),
        ("DynamoDbWriteMs", "persister_in", "persisted"),
        ("TotalToPersistedMs", "t0", "persisted"),
    ]
    values = {name: trace[b] - trace[a] for name, a, b in hops if a in trace and b in trace}
    if not values:
        return
    print(json.dumps({
        "_aws": {
            "Timestamp": trace["persisted"],
            "CloudWatchMetrics": [{
                "Namespace": "DigitalTwin/Latency",
                "Dimensions": [["iotDeviceId"]],
                "Metrics": [{"Name": name, "Unit": "Milliseconds"} for name in values],
            }],
        },
        "iotDeviceId": event.get("iotDeviceId"),
        **values,
    }))


def lambda_handler(event, context):
    persister_in = now_ms()
    print("Hello from Persister!")
    print("Event: " + json.dumps(event))

    trace = event.get("_trace")
    if trace is not None:
        trace["persister_in"] = persister_in

    item = event.copy()
    item["id"] = str(item.pop("time"))
    item = floats_to_decimals(item)

    dynamodb_table.put_item(Item=item)

    if trace is not None:
        trace["persisted"] = now_ms()
        emit_latency_metrics(event)

    lambda_client.invoke(FunctionName=EVENT_CHECKER_LAMBDA_NAME, InvocationType="Event", Payload=json.dumps(event).encode("utf-8"))
