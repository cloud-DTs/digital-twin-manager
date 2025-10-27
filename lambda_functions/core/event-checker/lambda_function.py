import os
import json
import boto3


DIGITAL_TWIN_INFO = json.loads(os.environ.get("DIGITAL_TWIN_INFO", None))
TWINMAKER_WORKSPACE_NAME = os.environ.get("TWINMAKER_WORKSPACE_NAME", None)
LAMBDA_CHAIN_STEP_FUNCTION_ARN = os.environ.get("LAMBDA_CHAIN_STEP_FUNCTION_ARN", None)
EVENT_FEEDBACK_LAMBDA_FUNCTION_ARN = os.environ.get("EVENT_FEEDBACK_LAMBDA_FUNCTION_ARN", None)

twinmaker_client = boto3.client("iottwinmaker")
lambda_client = boto3.client("lambda")
sf_client = boto3.client("stepfunctions")


def fetch_value(entity_id, component_name, property_name):
    response = twinmaker_client.get_property_value(
        workspaceId=TWINMAKER_WORKSPACE_NAME,
        entityId=entity_id,
        componentName=component_name,
        selectedProperties=[property_name]
    )

    property = list(response["propertyValues"].values())[0]
    value = list(property["propertyValue"].values())[0]

    return value


def extract_const_value(string):
    if string.startswith("DOUBLE"):
        return float(string[7:-1])
    elif string.startswith("INTEGER"):
        return int(string[8:-1])
    elif string.startswith("STRING"):
        string[7:-1]
    return string


def lambda_handler(event, context):
    print("Hello from Event-Checker!")
    print("Event: " + json.dumps(event))
    print("Events: " + json.dumps(DIGITAL_TWIN_INFO["config_events"]))

    for e in DIGITAL_TWIN_INFO["config_events"]:
        try:
            condition = e["condition"]
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

            match operation:
                case "<": result = param1_value < param2_value
                case ">": result = param1_value < param2_value
                case "==": result = param1_value == param2_value

            if e["action"]["type"] == "lambda" and result:
                if "feedback" not in e["action"]:
                    payload = { "e": e }
                    lambda_client.invoke(FunctionName=e["action"]["functionName"], InvocationType="Event", Payload=json.dumps(payload).encode("utf-8"))
                else:
                    response = lambda_client.get_function(FunctionName=e["action"]["functionName"])
                    action_function_arn = response["Configuration"]["FunctionArn"]

                    sf_client.start_execution(
                        stateMachineArn=LAMBDA_CHAIN_STEP_FUNCTION_ARN,
                        input=json.dumps({
                            "LambdaAArn": action_function_arn,
                            "LambdaBArn": EVENT_FEEDBACK_LAMBDA_FUNCTION_ARN,
                            "InputData": { "e": e }
                        })
                    )
            else:
                raise ValueError(f"Invalid action type: {e["action"]["type"]}")

        except Exception as ex:
            print("Something went wrong: ", ex)
