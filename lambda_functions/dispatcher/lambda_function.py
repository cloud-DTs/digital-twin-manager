import json

def lambda_handler(event, context):
    print("Dispatcher Lambda Function (ME) was called!")
    print(f"Event: {event}")
    print(f"Context: {context}")

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda! Uploaded from client!! version 67')
    }
