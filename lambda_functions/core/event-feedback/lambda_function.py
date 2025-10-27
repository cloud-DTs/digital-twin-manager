import os
import json
import boto3


DIGITAL_TWIN_INFO = json.loads(os.environ.get("DIGITAL_TWIN_INFO", None))
AWS_REGION = os.environ["AWS_REGION"]

iot_data_client = boto3.client("iot-data", region_name=AWS_REGION)


def lambda_handler(event, context):
    print("Hello from Event-Feedback!")
    print("Event: " + json.dumps(event))

    e = event["event"]["e"]
    result_from_lambda_a = event["fromA"]
    feedback = e["action"]["feedback"]

    if feedback["type"] == "mqtt":
        topic = feedback.get("topic", None) or f"{DIGITAL_TWIN_INFO["config"]["digital_twin_name"]}-{feedback.get("iotDeviceId", None)}"

        if feedback["payload"] == "action-result":
            message = result_from_lambda_a
        else:
            message = feedback["payload"]

        iot_data_client.publish(
            topic=topic,
            qos=1,
            payload=json.dumps(message)
        )

