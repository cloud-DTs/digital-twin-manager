import json
import os
import boto3
from boto3.dynamodb.conditions import Key


DIGITAL_TWIN_INFO = json.loads(os.environ.get("DIGITAL_TWIN_INFO", None))
DYNAMODB_TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME", None)

twinmaker_client = boto3.client("iottwinmaker")
dynamodb_resource = boto3.resource("dynamodb")
dynamodb_table = dynamodb_resource.Table(DYNAMODB_TABLE_NAME)


def aws_handler(event, context):
    entity = twinmaker_client.get_entity(workspaceId=event["workspaceId"], entityId=event["entityId"])
    components = entity.get("components", {})
    component_info = components.get(event["componentName"])
    component_type_id = component_info.get("componentTypeId")

    response = dynamodb_table.query(
        KeyConditionExpression=Key("iotDeviceId").eq(component_type_id) &
                               Key("id").between(event["startTime"], event["endTime"])
        )
    items = response["Items"]

    propertyValues = []

    for prop in event["selectedProperties"]:
        prop_type = f"{event["properties"][prop]["definition"]["dataType"]["type"].capitalize()}Value"

        entry = {
            "entityPropertyReference": {
                "propertyName": prop
            },
            "values": []
        }

        for item in items:
            entry["values"].append({
                "time": item["id"],
                "value": { prop_type: item[prop] }
            })

        propertyValues.append(entry)

    return { "propertyValues": propertyValues }


def azure_handler(event, context):
    print("TODO Azure")


def lambda_handler(event, context):
    print("Hello from Twinmaker Connector!")
    print("Event: " + json.dumps(event))

    if DIGITAL_TWIN_INFO["layer_3_hot_provider"].lower() == "aws":
        return aws_handler(event, context)

    elif DIGITAL_TWIN_INFO["layer_3_hot_provider"].lower() == "azure":
        return azure_handler(event, context)

    else:
        print("Error: Unknown DIGITAL_TWIN_INFO['layer_3_hot_provider']")
