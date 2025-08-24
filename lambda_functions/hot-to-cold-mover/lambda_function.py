import json

def lambda_handler(event, context):
    print("Hello from Hot To Cold Mover!")
    print("Event: " + json.dumps(event))

    # TODO implement
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from hot to cold mover Lambda!')
    }
