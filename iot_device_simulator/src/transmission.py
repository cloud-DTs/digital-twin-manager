import time
import globals
import os
import json
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient


payload_index = 0


def send_mqtt(payload):
  device_name = payload["iot_device_id"]
  auth_path = os.path.join(globals.project_path(), globals.config.get("general", "auth_files_path"), device_name)

  client = AWSIoTMQTTClient(device_name)
  client.configureEndpoint(globals.config.get("general", "endpoint"), 8883)
  client.configureCredentials(os.path.join(globals.project_path(), globals.config.get("general", "root_ca_cert_path")), os.path.join(auth_path, "private.pem.key"), os.path.join(auth_path, "certificate.pem.crt"))

  topic = globals.config.get("general", "topic")

  client.connect()
  client.publish(topic, json.dumps(payload), 1)
  client.disconnect()

  print(f"Message sent! Topic: {topic}, Payload: {payload}")


def send():
  global payload_index

  payloads_path = os.path.join(globals.project_path(), globals.config.get("general", "payload_file_path"))

  with open(payloads_path, "r", encoding="utf-8") as f:
    payloads = json.load(f)

  if payload_index >= len(payloads):
    payload_index = 0

  payload = payloads[payload_index]
  payload_index += 1

  if "timestamp" not in payload or payload["timestamp"] == "":
    payload["timestamp"] = int(time.time())

  send_mqtt(payload)
