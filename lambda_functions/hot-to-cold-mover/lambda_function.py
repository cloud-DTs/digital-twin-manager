import boto3
import os
import json
import datetime
from boto3.dynamodb.conditions import Key


DIGITAL_TWIN_INFO = json.loads(os.environ.get("DIGITAL_TWIN_INFO", None))
DYNAMODB_TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME", None)
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", None)

dynamodb_client = boto3.resource("dynamodb")
dynamodb_table = dynamodb_client.Table(DYNAMODB_TABLE_NAME)
s3_client = boto3.client("s3")

cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=DIGITAL_TWIN_INFO["config"]["hot_storage_size_in_days"])
cutoff_iso = cutoff.isoformat(timespec='milliseconds').replace('+00:00', 'Z')
chunk_count = 0


def flush_chunk_to_s3(iot_device_id, items, start, end, chunk_index):
    if not items:
        return

    key = f"{iot_device_id}/{start}-{end}/chunk-{chunk_index:05d}.json"
    body = json.dumps(items, default=str)

    s3_client.put_object(
        Bucket=S3_BUCKET_NAME,
        Key=key,
        Body=body,
        ContentType="application/json"
    )

    print(f"Wrote {len(items)} items to s3://{S3_BUCKET_NAME}/{key}")


def lambda_handler(event, context):
    print("Hello from Hot To Cold Mover!")
    print("Event: " + json.dumps(event))

    with dynamodb_table.batch_writer() as batch:
        for iot_device in DIGITAL_TWIN_INFO["config_iot_devices"]:
            iot_device_id = DIGITAL_TWIN_INFO["config"]["digital_twin_name"] + "-" + iot_device["name"]
            chunk_index = 0

            response = dynamodb_table.query(
                KeyConditionExpression=Key("iotDeviceId").eq(iot_device_id) &
                                    Key("id").lt(cutoff_iso),
                ScanIndexForward=False, # descending order by id (time)
                Limit=1
            )
            items = response.get("Items", [])

            if len(items) == 0:
                continue

            end = items[0]["id"]

            response = dynamodb_table.query(
                KeyConditionExpression=Key("iotDeviceId").eq(iot_device_id) &
                                    Key("id").lt(cutoff_iso),
                ScanIndexForward=True # ascending order by id (time)
            )
            items = response.get("Items", [])

            if len(items) == 0:
                continue

            start = items[0]["id"]

            while len(items) > 0:
                flush_chunk_to_s3(iot_device_id, items, start, end, chunk_index)
                chunk_index += 1

                item_count = len(items)

                for item in items:
                    batch.delete_item(
                        Key={
                            "iotDeviceId": item["iotDeviceId"],
                            "id": item["id"],
                        }
                    )

                print(f"Deleted {item_count} items.")

                if "LastEvaluatedKey" not in response:
                    break

                response = dynamodb_table.query(
                    KeyConditionExpression=Key("iotDeviceId").eq(iot_device_id) &
                                        Key("id").lt(cutoff_iso),
                    ExclusiveStartKey=response["LastEvaluatedKey"]
                )
                items = response.get("Items", [])
