import json
import os
import boto3
from boto3.dynamodb.conditions import Key


DIGITAL_TWIN_INFO = json.loads(os.environ.get("DIGITAL_TWIN_INFO", None))
DYNAMODB_TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME", None)

twinmaker_client = boto3.client("iottwinmaker")
dynamodb_resource = boto3.resource("dynamodb")
dynamodb_table = dynamodb_resource.Table(DYNAMODB_TABLE_NAME)


def lambda_handler(event, context):
    print("Hello from Twinmaker Connector Last Entry!")
    print("Event: " + json.dumps(event))

    entity = twinmaker_client.get_entity(workspaceId=event["workspaceId"], entityId=event["entityId"])
    components = entity.get("components", {})
    component_info = components.get(event["componentName"])
    component_type_id = component_info.get("componentTypeId")

    response = dynamodb_table.query(
        KeyConditionExpression=Key("iotDeviceId").eq(component_type_id),
                               ScanIndexForward=False,
                               Limit=1
        )
    item = response["Items"][0]

    propertyValues = {}

    for property_name in event["selectedProperties"]:
        property_type = f"{event["properties"][property_name]["definition"]["dataType"]["type"].lower()}Value"

        propertyValues[property_name] = {
            "propertyReference": {
                "entityId": event["entityId"],
                "componentName": event["componentName"],
                "propertyName": property_name
            },
            "propertyValue": {
                property_type: item[property_name]
            }
        }

    return { "propertyValues": propertyValues }
