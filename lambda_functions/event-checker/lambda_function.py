import os
import json
import boto3
import datetime


DIGITAL_TWIN_INFO = json.loads(os.environ.get("DIGITAL_TWIN_INFO", None))
TWINMAKER_WORKSPACE_NAME = os.environ.get("TWINMAKER_WORKSPACE_NAME", None)

twinmaker_client = boto3.client("iottwinmaker")
lambda_client = boto3.client("lambda")


def fetch_value_old(entity_id, component_name, property_name):
    end_time = datetime.datetime.utcnow()
    start_time = end_time - datetime.timedelta(minutes=5)

    response = twinmaker_client.get_property_value_history(
        workspaceId=TWINMAKER_WORKSPACE_NAME,
        entityId=entity_id,
        componentName=component_name,
        selectedProperties=[property_name],
        startTime=start_time.isoformat() + "Z",
        endTime=end_time.isoformat() + "Z"
    )

    if len(response["propertyValues"][0]["values"]) <= 0:
        print("Error: response['propertyValues'][0]['values'] was 0")
        return None

    value_wrapper = response["propertyValues"][0]["values"][-1]
    value = list(value_wrapper["value"].values())[0]

    return value


def fetch_value(entity_id, component_name, property_name):
    response = twinmaker_client.get_property_value(
        workspaceId=TWINMAKER_WORKSPACE_NAME,
        entityId=entity_id,
        componentName=component_name,
        selectedProperties=[property_name]
    )

    if len(response["propertyValues"][0]["values"]) <= 0:
        print("Error: response['propertyValues'][0]['values'] was 0")
        return None

    value_wrapper = response["propertyValues"][0]["values"][-1]
    value = list(value_wrapper["value"].values())[0]

    return value


def extract_const_value(string):
    if string.startswith("DOUBLE"):
        print(f"FLOAT = {float(string[7:-1])}")
        return float(string[7:-1])
    elif string.startswith("INTEGER"):
        return int(string[8:-1])
    elif string.startswith("STRING"):
        string[7:-1]
    return string


def lambda_handler(event, context):
    print("Hello from Event-Checker!")
    print("Event: " + json.dumps(event))
    print("Events: " + json.dumps(DIGITAL_TWIN_INFO["events"]))

    for e in DIGITAL_TWIN_INFO["events"]:
        condition = e["condition"]
        print(f"CHECKING CONDITION = {condition}")
        param1 = condition.split()[0]
        operation = condition.split()[1]
        param2 = condition.split()[2]

        if len(param1.split(".")) > 1:
            param1_entity_id = param1.split(".")[0]
            param1_component_name = param1.split(".")[1]
            param1_property_name = param1.split(".")[2]
            param1_value = fetch_value(param1_entity_id, param1_component_name, param1_property_name)
        else:
            param1_value = extract_const_value(param1)

        if len(param2.split(".")) > 1:
            param2_entity_id = param2.split(".")[0]
            param2_component_name = param2.split(".")[1]
            param2_property_name = param2.split(".")[2]
            param2_value = fetch_value(param2_entity_id, param2_component_name, param2_property_name)
        else:
            param2_value = extract_const_value(param2)

        print(f"param1_value = {param1_value}")
        print(f"param2_value = {param2_value}")

        match operation:
            case "<": result = param1_value < param2_value
            case ">": result = param1_value < param2_value
            case "==": result = param1_value == param2_value

        if result:
            print(f"TRUE = {condition}")
            # lambda_client.invoke(FunctionName=PERSISTER_LAMBDA_NAME, InvocationType="Event", Payload=json.dumps(payload).encode("utf-8"))
        else:
            print(f"FALSE = {condition}")
