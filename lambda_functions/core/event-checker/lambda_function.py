import os
import json
import boto3
import urllib.request
from datetime import datetime, timezone, timedelta


DIGITAL_TWIN_INFO = json.loads(os.environ.get("DIGITAL_TWIN_INFO", None))
TWINMAKER_WORKSPACE_NAME = os.environ.get("TWINMAKER_WORKSPACE_NAME", None)
LAMBDA_CHAIN_STEP_FUNCTION_ARN = os.environ.get("LAMBDA_CHAIN_STEP_FUNCTION_ARN", None)
EVENT_FEEDBACK_LAMBDA_FUNCTION_ARN = os.environ.get("EVENT_FEEDBACK_LAMBDA_FUNCTION_ARN", None)
SSM_REGISTRY_PREFIX = os.environ.get("SSM_REGISTRY_PREFIX", None)

twinmaker_client = boto3.client("iottwinmaker")
lambda_client = boto3.client("lambda")
sf_client = boto3.client("stepfunctions")
ssm_client = boto3.client("ssm")


def unwrap_data_value(value):
    if not isinstance(value, dict) or len(value) != 1:
        return value
    key, val = next(iter(value.items()))
    if key == "listValue":
        return [unwrap_data_value(v) for v in val]
    if key == "mapValue":
        return {k: unwrap_data_value(v) for k, v in val.items()}
    return val


def fetch_value(entity_id, component_name, property_name):
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=24)

    try:
        response = twinmaker_client.get_property_value_history(
            workspaceId=TWINMAKER_WORKSPACE_NAME,
            entityId=entity_id,
            componentName=component_name,
            selectedProperties=[property_name],
            startTime=start_time.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            endTime=end_time.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            maxResults=1,
            orderByTime="DESCENDING"
        )
        if not response.get("propertyValues"):
            return None
        entry = response["propertyValues"][0]
        if not entry.get("values"):
            return None
        return unwrap_data_value(entry["values"][0]["value"])

    except Exception:
        response = twinmaker_client.get_property_value(
            workspaceId=TWINMAKER_WORKSPACE_NAME,
            entityId=entity_id,
            componentName=component_name,
            selectedProperties=[property_name]
        )
        if not response.get("propertyValues"):
            return None
        property = list(response["propertyValues"].values())[0]
        if not property.get("propertyValue"):
            return None
        return unwrap_data_value(property["propertyValue"]["value"])


def extract_const_value(string):
    if string.startswith("DOUBLE"):
        return float(string[7:-1])
    elif string.startswith("INTEGER"):
        return int(string[8:-1])
    elif string.startswith("STRING"):
        return string[7:-1]
    return string


def resolve_input_parameters(e):
    input_params = {}
    for param in e["action"].get("inputParameters", []):
        if "value" in param:
            input_params[param["name"]] = param["value"]
        else:
            parts = param["id"].split(".")
            input_params[param["name"]] = fetch_value(parts[0], parts[1], parts[2])
    return input_params


def lookup_registry(event_name):
    if not SSM_REGISTRY_PREFIX:
        return None
    param_name = f"{SSM_REGISTRY_PREFIX}/{event_name}"
    try:
        response = ssm_client.get_parameter(Name=param_name)
        entry = json.loads(response["Parameter"]["Value"])
        print(f"FunctionRegistry hit for '{event_name}': {entry}")
        return entry.get("targets", [])
    except ssm_client.exceptions.ParameterNotFound:
        return None
    except Exception as ex:
        print(f"FunctionRegistry lookup failed (falling back to default): {ex}")
        return None


def resolve_lambda_arn(function_name):
    response = lambda_client.get_function(FunctionName=function_name)
    return response["Configuration"]["FunctionArn"]


def fire_action(e, input_params, registry_entry):
    action = e["action"]
    has_feedback = "feedback" in action
    payload = {"e": e, **input_params}
    print(f"Fire action {action}")
    if registry_entry:
        for entry in registry_entry:
            address = entry["address"]
            print(f"FunctionRegistry: redirecting to Step Function {address}")
            sf_client.start_execution(
                    stateMachineArn=address,
                    input=json.dumps(payload)
                )
        return
    
    #Default execution
    function_name = DIGITAL_TWIN_INFO["config"]["digital_twin_name"] + "-" + action["functionName"]
    if not has_feedback:
        lambda_client.invoke(FunctionName=function_name, InvocationType="Event", Payload=json.dumps(payload).encode("utf-8"))
    else:
        print(f"Invoking Lambda function {function_name} with feedback")
        action_function_arn = resolve_lambda_arn(function_name)
        response = sf_client.start_execution(
            stateMachineArn=LAMBDA_CHAIN_STEP_FUNCTION_ARN,
            input=json.dumps({
                "LambdaAArn": action_function_arn,
                "LambdaBArn": EVENT_FEEDBACK_LAMBDA_FUNCTION_ARN,
                "InputData": payload
            })
        )
        print(f"Step Function started! Response: {json.dumps(response, default=str)}")

def lambda_handler(event, context):
    print("Hello from Event-Checker!")
    print("Event: " + json.dumps(event))

    for e in DIGITAL_TWIN_INFO["config_events"]:
        try:
            condition = e["condition"]
            param1, operation, param2 = condition.split()

            param1_value = fetch_value(*param1.split(".")) if "." in param1 else extract_const_value(param1)
            if param1_value is None:
                print(f"No value yet for {param1}, skipping event")
                continue

            param2_value = fetch_value(*param2.split(".")) if "." in param2 else extract_const_value(param2)
            if param2_value is None:
                print(f"No value yet for {param2}, skipping event")
                continue

            match operation:
                case "<":  result = param1_value < param2_value
                case ">":  result = param1_value > param2_value
                case "==": result = param1_value == param2_value
                case _:    raise ValueError(f"Unknown operator: {operation}")

            if e["action"]["type"] == "lambda" and result:
                input_params = resolve_input_parameters(e)
                registry_entry = lookup_registry(e["action"]["functionName"])
                fire_action(e, input_params, registry_entry)

        except Exception as ex:
            print("Something went wrong: ", ex)