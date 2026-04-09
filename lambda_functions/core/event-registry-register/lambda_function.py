import os
import json
import boto3

SSM_REGISTRY_PREFIX = os.environ.get("SSM_REGISTRY_PREFIX", None)

ssm_client = boto3.client("ssm")

VALID_ADDRESS_TYPES = {"lambda", "webhook"}


def respond(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body)
    }


def handle_register(body):
    event_name = body.get("eventName")
    address = body.get("address")
    address_type = body.get("addressType", "lambda")

    if not event_name or not address:
        return respond(400, {"error": "eventName and address are required"})
    if address_type not in VALID_ADDRESS_TYPES:
        return respond(400, {"error": f"addressType must be one of {list(VALID_ADDRESS_TYPES)}"})

    param_name = f"{SSM_REGISTRY_PREFIX}/{event_name}"
    value = json.dumps({"address": address, "addressType": address_type})

    ssm_client.put_parameter(
        Name=param_name,
        Value=value,
        Type="String",
        Overwrite=True,
        Description=f"FunctionRegistry entry for event '{event_name}'"
    )

    print(f"Registered: {param_name} = {value}")
    return respond(200, {"message": f"Registered '{event_name}' -> '{address}' ({address_type})", "parameter": param_name})


def handle_deregister(body):
    event_name = body.get("eventName")
    if not event_name:
        return respond(400, {"error": "eventName is required"})

    param_name = f"{SSM_REGISTRY_PREFIX}/{event_name}"
    try:
        ssm_client.delete_parameter(Name=param_name)
        print(f"Deregistered: {param_name}")
        return respond(200, {"message": f"Deregistered '{event_name}'"})
    except ssm_client.exceptions.ParameterNotFound:
        return respond(404, {"error": f"No entry found for '{event_name}'"})


def handle_list():
    response = ssm_client.get_parameters_by_path(Path=SSM_REGISTRY_PREFIX, Recursive=False)
    entries = []
    for param in response.get("Parameters", []):
        event_name = param["Name"].removeprefix(SSM_REGISTRY_PREFIX + "/")
        try:
            value = json.loads(param["Value"])
        except Exception:
            value = param["Value"]
        entries.append({"eventName": event_name, **value})
    return respond(200, {"entries": entries})


def lambda_handler(event, context):
    print("Hello from Event-Registry-Register (FunctionRegistry)!")
    print("Event: " + json.dumps(event))

    http_method = event.get("requestContext", {}).get("http", {}).get("method", "").upper()
    raw_body = event.get("body") or "{}"

    try:
        body = json.loads(raw_body)
    except Exception:
        return respond(400, {"error": "Invalid JSON body"})

    if http_method == "GET":
        return handle_list()
    if http_method == "DELETE":
        return handle_deregister(body)


    action = body.get("action", "register")
    if action == "register":
        return handle_register(body)
    elif action == "deregister":
        return handle_deregister(body)
    elif action == "list":
        return handle_list()
    else:
        return respond(400, {"error": f"Unknown action '{action}'. Use: register | deregister | list"})
