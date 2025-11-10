import globals
from datetime import datetime, timezone
import json


def post_init_values_to_iot_core():
  topic = "digital-twin/iot-data"

  for iot_device in globals.config_iot_devices:
    has_init = any("initValue" in prop for prop in iot_device["properties"])

    if not has_init:
      continue

    payload = {
      "iotDeviceId": iot_device["id"],
      "time": datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
    }

    for property in iot_device["properties"]:
      payload[property["name"]] = property.get("initValue", None)

    globals.aws_iot_data_client.publish(
        topic=topic,
        qos=1,
        payload=json.dumps(payload).encode("utf-8")
    )

    log(f"Posted init values for IoT device id: {iot_device["id"]}")



def deploy():
  post_init_values_to_iot_core()

def destroy():
  pass

def info():
  pass


def log(string):
  print(f"Init Value Deployer: " + string)
