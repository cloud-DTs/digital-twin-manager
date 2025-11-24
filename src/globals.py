import json
import os
import boto3


iot_data_path = "iot_devices_auth"
core_lfs_path = "lambda_functions/core"
processor_lfs_path = "lambda_functions/processors"
event_action_lfs_path = "lambda_functions/event_actions"

config = {}
config_iot_devices = []
config_credentials = {}

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
aws_sf_client = {}
aws_iot_data_client = {}


def project_path():
  return os.path.dirname(os.path.dirname(__file__))

def initialize_config():
  global config
  with open(f"{project_path()}/config.json", "r") as file:
    config = json.load(file)

def initialize_config_iot_devices():
  global config_iot_devices
  with open(f"{project_path()}/config_iot_devices.json", "r") as file:
    config_iot_devices = json.load(file)

def initialize_config_events():
  global config_events
  with open(f"{project_path()}/config_events.json", "r") as file:
    config_events = json.load(file)

def initialize_config_hierarchy():
  global config_hierarchy
  with open(f"{project_path()}/config_hierarchy.json", "r") as file:
    config_hierarchy = json.load(file)

def initialize_config_credentials():
  global config_credentials
  with open(f"{project_path()}/config_credentials.json", "r") as file:
    config_credentials = json.load(file)

def digital_twin_info():
  return {
    "config": config,
    "config_iot_devices": config_iot_devices,
    "config_events": config_events
  }


def initialize_aws_iam_client():
  global aws_iam_client
  aws_iam_client = boto3.client("iam",
    aws_access_key_id=config_credentials["aws_access_key_id"],
    aws_secret_access_key=config_credentials["aws_secret_access_key"],
    region_name=config_credentials["aws_region"])

def initialize_aws_lambda_client():
  global aws_lambda_client
  aws_lambda_client = boto3.client("lambda",
    aws_access_key_id=config_credentials["aws_access_key_id"],
    aws_secret_access_key=config_credentials["aws_secret_access_key"],
    region_name=config_credentials["aws_region"])

def initialize_aws_iot_client():
  global aws_iot_client
  aws_iot_client = boto3.client("iot",
    aws_access_key_id=config_credentials["aws_access_key_id"],
    aws_secret_access_key=config_credentials["aws_secret_access_key"],
    region_name=config_credentials["aws_region"])

def initialize_aws_sts_client():
  global aws_sts_client
  aws_sts_client = boto3.client("sts",
    aws_access_key_id=config_credentials["aws_access_key_id"],
    aws_secret_access_key=config_credentials["aws_secret_access_key"],
    region_name=config_credentials["aws_region"])

def initialize_aws_events_client():
  global aws_events_client
  aws_events_client = boto3.client("events",
    aws_access_key_id=config_credentials["aws_access_key_id"],
    aws_secret_access_key=config_credentials["aws_secret_access_key"],
    region_name=config_credentials["aws_region"])

def initialize_aws_dynamodb_client():
  global aws_dynamodb_client
  aws_dynamodb_client = boto3.client("dynamodb",
    aws_access_key_id=config_credentials["aws_access_key_id"],
    aws_secret_access_key=config_credentials["aws_secret_access_key"],
    region_name=config_credentials["aws_region"])

def initialize_aws_s3_client():
  global aws_s3_client
  aws_s3_client = boto3.client("s3",
    aws_access_key_id=config_credentials["aws_access_key_id"],
    aws_secret_access_key=config_credentials["aws_secret_access_key"],
    region_name=config_credentials["aws_region"])

def initialize_aws_twinmaker_client():
  global aws_twinmaker_client
  aws_twinmaker_client = boto3.client("iottwinmaker",
    aws_access_key_id=config_credentials["aws_access_key_id"],
    aws_secret_access_key=config_credentials["aws_secret_access_key"],
    region_name=config_credentials["aws_region"])

def initialize_aws_grafana_client():
  global aws_grafana_client
  aws_grafana_client = boto3.client("grafana",
    aws_access_key_id=config_credentials["aws_access_key_id"],
    aws_secret_access_key=config_credentials["aws_secret_access_key"],
    region_name=config_credentials["aws_region"])

def initialize_aws_logs_client():
  global aws_logs_client
  aws_logs_client = boto3.client("logs",
    aws_access_key_id=config_credentials["aws_access_key_id"],
    aws_secret_access_key=config_credentials["aws_secret_access_key"],
    region_name=config_credentials["aws_region"])

def initialize_aws_sf_client():
  global aws_sf_client
  aws_sf_client = boto3.client("stepfunctions",
    aws_access_key_id=config_credentials["aws_access_key_id"],
    aws_secret_access_key=config_credentials["aws_secret_access_key"],
    region_name=config_credentials["aws_region"])

def initialize_aws_iot_data_client():
  global aws_iot_data_client
  aws_iot_data_client = boto3.client("iot-data",
    aws_access_key_id=config_credentials["aws_access_key_id"],
    aws_secret_access_key=config_credentials["aws_secret_access_key"],
    region_name=config_credentials["aws_region"])


def dispatcher_iam_role_name():
  return config["digital_twin_name"] + "-dispatcher"

def dispatcher_lambda_function_name():
  return config["digital_twin_name"] + "-dispatcher"

def dispatcher_iot_rule_name():
  rule_name = config["digital_twin_name"] + "-trigger-dispatcher"
  return rule_name.replace("-", "_")

def dispatcher_iot_rule_topic():
  return config["digital_twin_name"] + "/iot-data"

def persister_iam_role_name():
  return config["digital_twin_name"] + "-persister"

def persister_lambda_function_name():
  return config["digital_twin_name"] + "-persister"

def event_feedback_iam_role_name():
  return config["digital_twin_name"] + "-event-feedback"

def event_feedback_lambda_function_name():
  return config["digital_twin_name"] + "-event-feedback"

def event_checker_iam_role_name():
  return config["digital_twin_name"] + "-event-checker"

def event_checker_lambda_function_name():
  return config["digital_twin_name"] + "-event-checker"

def lambda_chain_iam_role_name():
  return config["digital_twin_name"] + "-lambda-chain"

def lambda_chain_step_function_name():
  return config["digital_twin_name"] + "-lambda-chain"

def hot_dynamodb_table_name():
  return config["digital_twin_name"] + "-hot-iot-data"

def hot_cold_mover_iam_role_name():
  return config["digital_twin_name"] + "-hot-to-cold-mover"

def hot_cold_mover_lambda_function_name():
  return config["digital_twin_name"] + "-hot-to-cold-mover"

def hot_cold_mover_event_rule_name():
  return config["digital_twin_name"] + "-hot-to-cold-mover"

def cold_archive_mover_iam_role_name():
  return config["digital_twin_name"] + "-cold-to-archive-mover"

def cold_archive_mover_lambda_function_name():
  return config["digital_twin_name"] + "-cold-to-archive-mover"

def cold_archive_mover_event_rule_name():
  return config["digital_twin_name"] + "-cold-to-archive-mover"

def cold_s3_bucket_name():
  return (config["digital_twin_name"] + "-cold-iot-data").lower()

def archive_s3_bucket_name():
  return (config["digital_twin_name"] + "-archive-iot-data").lower()

def hot_reader_iam_role_name():
  return config["digital_twin_name"] + "-hot-reader"

def hot_reader_lambda_function_name():
  return config["digital_twin_name"] + "-hot-reader"

def twinmaker_s3_bucket_name():
  return (config["digital_twin_name"] + "-twinmaker").lower()

def twinmaker_iam_role_name():
  return config["digital_twin_name"] + "-twinmaker"

def twinmaker_workspace_name():
  return config["digital_twin_name"] + "-twinmaker"

def grafana_workspace_name():
  return config["digital_twin_name"] + "-grafana"

def grafana_iam_role_name():
  return config["digital_twin_name"] + "-grafana"

def iot_thing_name(iot_device):
  return config["digital_twin_name"] + "-" + iot_device["id"]

def iot_thing_policy_name(iot_device):
  return config["digital_twin_name"] + "-" + iot_device["id"]

def processor_iam_role_name(iot_device):
  return config["digital_twin_name"] + "-" + iot_device["id"] + "-processor"

def processor_lambda_function_name_local(iot_device):
  return iot_device["id"]

def processor_lambda_function_name(iot_device):
  return config["digital_twin_name"] + "-" + processor_lambda_function_name_local(iot_device) + "-processor"

def twinmaker_component_type_id(iot_device):
  return config["digital_twin_name"] + "-" + iot_device["id"]
