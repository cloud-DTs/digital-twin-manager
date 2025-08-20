import configparser
import json
import os
import boto3


config_path = "config.ini"
config_iot_devices_path = "config_iot_devices.json"
iot_data_path = "iot_devices_auth"
lambda_functions_path = "lambda_functions"

config = {}
config_iot_devices = []
config_layers = {}

aws_iam_client = {}
aws_lambda_client = {}
aws_iot_client = {}
aws_sts_client = {}
aws_events_client = {}
aws_dynamodb_client = {}
aws_s3_client = {}
aws_twinmaker_client = {}
aws_grafana_client = {}
aws_logs_client = {}


def project_path():
  return os.path.dirname(os.path.dirname(__file__))

def initialize_config():
  global config
  config = configparser.ConfigParser()
  config.read(os.path.join(os.path.dirname(os.path.dirname(__file__)), config_path))

def initialize_config_iot_devices():
  global config_iot_devices
  with open("config_iot_devices.json", "r") as file:
    config_iot_devices = json.load(file)

def initialize_config_layers():
  global config_layers
  with open("config_layers.json", "r") as file:
    config_layers = json.load(file)


def initialize_aws_iam_client():
  global config
  global aws_iam_client
  aws_iam_client = boto3.client("iam",
    aws_access_key_id=config.get("credentials", "aws_access_key_id"),
    aws_secret_access_key=config.get("credentials", "aws_secret_access_key"),
    region_name=config.get("credentials", "aws_region"))

def initialize_aws_lambda_client():
  global config
  global aws_lambda_client
  aws_lambda_client = boto3.client("lambda",
    aws_access_key_id=config.get("credentials", "aws_access_key_id"),
    aws_secret_access_key=config.get("credentials", "aws_secret_access_key"),
    region_name=config.get("credentials", "aws_region"))

def initialize_aws_iot_client():
  global config
  global aws_iot_client
  aws_iot_client = boto3.client("iot",
    aws_access_key_id=config.get("credentials", "aws_access_key_id"),
    aws_secret_access_key=config.get("credentials", "aws_secret_access_key"),
    region_name=config.get("credentials", "aws_region"))

def initialize_aws_sts_client():
  global config
  global aws_sts_client
  aws_sts_client = boto3.client("sts",
    aws_access_key_id=config.get("credentials", "aws_access_key_id"),
    aws_secret_access_key=config.get("credentials", "aws_secret_access_key"),
    region_name=config.get("credentials", "aws_region"))

def initialize_aws_events_client():
  global config
  global aws_events_client
  aws_events_client = boto3.client("events",
    aws_access_key_id=config.get("credentials", "aws_access_key_id"),
    aws_secret_access_key=config.get("credentials", "aws_secret_access_key"),
    region_name=config.get("credentials", "aws_region"))

def initialize_aws_dynamodb_client():
  global config
  global aws_dynamodb_client
  aws_dynamodb_client = boto3.client("dynamodb",
    aws_access_key_id=config.get("credentials", "aws_access_key_id"),
    aws_secret_access_key=config.get("credentials", "aws_secret_access_key"),
    region_name=config.get("credentials", "aws_region"))

def initialize_aws_s3_client():
  global config
  global aws_s3_client
  aws_s3_client = boto3.client("s3",
    aws_access_key_id=config.get("credentials", "aws_access_key_id"),
    aws_secret_access_key=config.get("credentials", "aws_secret_access_key"),
    region_name=config.get("credentials", "aws_region"))

def initialize_aws_twinmaker_client():
  global config
  global aws_twinmaker_client
  aws_twinmaker_client = boto3.client("iottwinmaker",
    aws_access_key_id=config.get("credentials", "aws_access_key_id"),
    aws_secret_access_key=config.get("credentials", "aws_secret_access_key"),
    region_name=config.get("credentials", "aws_region"))

def initialize_aws_grafana_client():
  global config
  global aws_grafana_client
  aws_grafana_client = boto3.client("grafana",
    aws_access_key_id=config.get("credentials", "aws_access_key_id"),
    aws_secret_access_key=config.get("credentials", "aws_secret_access_key"),
    region_name=config.get("credentials", "aws_region"))

def initialize_aws_logs_client():
  global config
  global aws_logs_client
  aws_logs_client = boto3.client("logs",
    aws_access_key_id=config.get("credentials", "aws_access_key_id"),
    aws_secret_access_key=config.get("credentials", "aws_secret_access_key"),
    region_name=config.get("credentials", "aws_region"))


def dispatcher_iam_role_name():
  return config.get("general", "digital_twin_name") + "-dispatcher"

def dispatcher_lambda_function_name():
  return config.get("general", "digital_twin_name") + "-dispatcher"

def dispatcher_iot_rule_name():
  rule_name = config.get("general", "digital_twin_name") + "-trigger-dispatcher"
  return rule_name.replace("-", "_")

def persister_iam_role_name():
  return config.get("general", "digital_twin_name") + "-persister"

def persister_lambda_function_name():
  return config.get("general", "digital_twin_name") + "-persister"

def dynamodb_table_name():
  return config.get("general", "digital_twin_name") + "-iot-data"

def hot_cold_mover_iam_role_name():
  return config.get("general", "digital_twin_name") + "-hot-to-cold-mover"

def hot_cold_mover_lambda_function_name():
  return config.get("general", "digital_twin_name") + "-hot-to-cold-mover"

def hot_cold_mover_event_rule_name():
  return config.get("general", "digital_twin_name") + "-hot-to-cold-mover"

def cold_archive_mover_iam_role_name():
  return config.get("general", "digital_twin_name") + "-cold-to-archive-mover"

def cold_archive_mover_lambda_function_name():
  return config.get("general", "digital_twin_name") + "-cold-to-archive-mover"

def cold_archive_mover_event_rule_name():
  return config.get("general", "digital_twin_name") + "-cold-to-archive-mover"

def cold_s3_bucket_name():
  return config.get("general", "digital_twin_name") + "-cold-iot-data"

def archive_s3_bucket_name():
  return config.get("general", "digital_twin_name") + "-archive-iot-data"

def twinmaker_s3_bucket_name():
  return config.get("general", "digital_twin_name") + "-twinmaker"

def twinmaker_iam_role_name():
  return config.get("general", "digital_twin_name") + "-twinmaker"

def twinmaker_workspace_name():
  return config.get("general", "digital_twin_name") + "-twinmaker"

def grafana_workspace_name():
  return config.get("general", "digital_twin_name") + "-grafana"

def grafana_iam_role_name():
  return config.get("general", "digital_twin_name") + "-grafana"

def iot_thing_name(iot_device):
  return config.get("general", "digital_twin_name") + "-" + iot_device["name"]

def iot_thing_policy_name(iot_device):
  return config.get("general", "digital_twin_name") + "-" + iot_device["name"]

def preprocessor_iam_role_name(iot_device):
  return config.get("general", "digital_twin_name") + "-" + iot_device["name"] + "-preprocessor"

def preprocessor_lambda_function_name(iot_device):
  return config.get("general", "digital_twin_name") + "-" + iot_device["name"] + "-preprocessor"

def twinmaker_component_type_id(iot_device):
  return config.get("general", "digital_twin_name") + "-" + iot_device["name"]
