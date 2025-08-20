import json
import os

LAYER_INFO = os.environ.get("LAYER_INFO", None)

def lambda_handler(event, context):
    print("Dispatcher Lambda Function (ME) was called!")
    print(f"Event: {event}")
    print(f"Context: {context}")

    print(f"Layer info: ", json.loads(LAYER_INFO))
    print(f"Layer 2: ", json.loads(LAYER_INFO)["layer_2_provider"])

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda! Uploaded from client!! version 67')
    }
