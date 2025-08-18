import json

def lambda_handler(event, context):
    # TODO implement

    # push data into dynamoDb
    # push data into twinmaker (batch_put_property_values)

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from persister Lambda!')
    }
