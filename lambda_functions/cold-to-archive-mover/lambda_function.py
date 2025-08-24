import json

def lambda_handler(event, context):
    print("Hello from Hot To Archive Mover!")
    print("Event: " + json.dumps(event))

    # TODO implement
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from cold to archive mover Lambda!')
    }
