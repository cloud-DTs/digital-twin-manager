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
    print("Hello from Twinmaker Connector!")
    print("Event: " + json.dumps(event))

    entity = twinmaker_client.get_entity(workspaceId=event["workspaceId"], entityId=event["entityId"])
    components = entity.get("components", {})
    component_info = components.get(event["componentName"])
    component_type_id = component_info.get("componentTypeId")

    iot_device_id = component_type_id.removeprefix(DIGITAL_TWIN_INFO["config"]["digital_twin_name"] + "-")

    response = dynamodb_table.query(
        KeyConditionExpression=Key("iotDeviceId").eq(iot_device_id) &
                               Key("id").between(event["startTime"], event["endTime"])
        )
    items = response["Items"]

    property_values = []

    for property_name in event["selectedProperties"]:
        property_type = f"{event["properties"][property_name]["definition"]["dataType"]["type"].capitalize()}Value"

        entry = {
            "entityPropertyReference": {
                "propertyName": property_name
            },
            "values": []
        }

        for item in items:
            entry["values"].append({
                "time": item["id"],
                "value": { property_type: item[property_name] }
            })

        property_values.append(entry)

    return { "propertyValues": property_values }
