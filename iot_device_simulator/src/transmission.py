import globals
import os
import json
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient

last_payload_index = {}


def send_mqtt(device_name, payload):
  auth_path = os.path.join(globals.project_path(), globals.config.get("general", "auth_files_path"), device_name)

  client = AWSIoTMQTTClient(device_name)
  client.configureEndpoint(globals.config.get("general", "endpoint"), 8883)
  client.configureCredentials(os.path.join(globals.project_path(), globals.config.get("general", "root_ca_cert_path")), os.path.join(auth_path, "private.pem.key"), os.path.join(auth_path, "certificate.pem.crt"))

  topic = globals.config.get("general", "topic_prefix") + device_name

  client.connect()
  client.publish(topic, json.dumps(payload), 1)
  client.disconnect()

  print(f"Message sent! Topic: {topic}, Payload: {payload}")


def send(device_name):
  payload_path = os.path.join(globals.project_path(), globals.config.get("general", "payload_files_path"), device_name) + ".json"

  with open(payload_path, "r", encoding="utf-8") as f:
    payload = json.load(f)

  if device_name in last_payload_index:
    index = last_payload_index[device_name] + 1
  else:
    index = 0

  if index >= len(payload):
    index = 0

  send_mqtt(device_name, payload[index])

  last_payload_index[device_name] = index
