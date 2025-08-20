import json

def lambda_handler(event, context):
    # TODO implement

    # push data into dynamoDb
    # push data into twinmaker (batch_put_property_values)
    # push data into azure digital twins

    print("Hello from Persister!")
    print("Event: " + json.dumps(event))
