import os
import json


DIGITAL_TWIN_INFO = json.loads(os.environ.get("DIGITAL_TWIN_INFO", None))


def lambda_handler(event, context):
    print("Hello from High Temperature Callback!")
    print("Event: " + json.dumps(event))

    return {
        "this_is_some_return_data": "hello world!"
    }
