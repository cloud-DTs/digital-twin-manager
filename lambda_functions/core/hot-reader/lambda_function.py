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
    print("Hello from Hot Reader!")
    print("Event: " + json.dumps(event))

    entity = twinmaker_client.get_entity(workspaceId=event["workspaceId"], entityId=event["entityId"])
    components = entity.get("components", {})
    component_info = components.get(event["componentName"])
    component_type_id = component_info.get("componentTypeId")

    iot_device_id = component_type_id.removeprefix(DIGITAL_TWIN_INFO["config"]["digital_twin_name"] + "-")

    start_time = event.get("startTime")
    end_time = event.get("endTime")

    if start_time and end_time:
        order_by_time = event.get("orderByTime", "ASCENDING")
        query_kwargs = dict(
        KeyConditionExpression=Key("iotDeviceId").eq(iot_device_id) &
                               Key("id").between(start_time, end_time),
        ScanIndexForward=(order_by_time != "DESCENDING"),
        )
        max_results = event.get("maxResults")
        if max_results:
            query_kwargs["Limit"] = max_results

        db_response = dynamodb_table.query(**query_kwargs)
    
        items = db_response.get("Items", [])
        print("DynamoDB items: " + json.dumps(items, default=str))
        property_values = []

        for property_name in event["selectedProperties"]:
            raw_type = event["properties"][property_name]["definition"]["dataType"]["type"]
            property_type_key = raw_type.lower() + "Value"
            entry = {
                "entityPropertyReference": {"propertyName": property_name},
                "values": []
            }
            for item in items:
                if property_name in item:
                    entry["values"].append({
                        "time": item["id"],
                        "value": {property_type_key: item[property_name]}
                    })
            property_values.append(entry)
        return {"propertyValues": property_values}

    else:
        db_response = dynamodb_table.query(
            KeyConditionExpression=Key("iotDeviceId").eq(iot_device_id),
            Limit=1,
            ScanIndexForward=False
        )
        items = db_response.get("Items", [])
        print("DynamoDB items: " + json.dumps(items, default=str))
        property_values = {}

        for property_name in event["selectedProperties"]:
            raw_type = event["properties"][property_name]["definition"]["dataType"]["type"]
            property_type_key = raw_type.lower() + "Value"

            if items:
                latest_item = items[0]
                if property_name in latest_item:
                    property_values[property_name] = {
                        "propertyReference": {
                            "propertyName": property_name,
                            "componentName": event["componentName"],
                            "entityId": event["entityId"]
                        },
                        "propertyValue": {
                            "value": {
                                property_type_key: latest_item[property_name]
                            },
                            "timestamp": latest_item["id"]
                        }
                    }

        return {"propertyValues": property_values}