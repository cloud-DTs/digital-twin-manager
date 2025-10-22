import globals
from botocore.exceptions import ClientError
import util


def check_dispatcher_iam_role():
  role_name = globals.dispatcher_iam_role_name()

  try:
    globals.aws_iam_client.get_role(RoleName=role_name)
    print(f"✅ Dispatcher IAM Role exists: {util.link_to_iam_role(role_name)}")
  except ClientError as e:
    if e.response["Error"]["Code"] == "NoSuchEntity":
      print(f"❌ Dispatcher IAM Role missing: {role_name}")
    else:
      raise

def check_dispatcher_lambda_function():
  function_name = globals.dispatcher_lambda_function_name()

  try:
    globals.aws_lambda_client.get_function(FunctionName=function_name)
    print(f"✅ Dispatcher Lambda Function exists: {util.link_to_lambda_function(function_name)}")
  except ClientError as e:
    if e.response["Error"]["Code"] == "ResourceNotFoundException":
      print(f"❌ Dispatcher Lambda Function missing: {function_name}")
    else:
      raise

def check_dispatcher_iot_rule():
  rule_name = globals.dispatcher_iot_rule_name()

  try:
    globals.aws_iot_client.get_topic_rule(ruleName=rule_name)
    print(f"✅ Dispatcher Iot Rule exists: {util.link_to_iot_rule(rule_name)}")
  except ClientError as e:
    if e.response["Error"]["Code"] == "UnauthorizedException":
      print(f"❌ Dispatcher IoT Rule missing: {rule_name}")
    else:
      raise

def check_iot_thing(iot_device):
  thing_name = globals.iot_thing_name(iot_device)

  try:
    globals.aws_iot_client.describe_thing(thingName=thing_name)
    print(f"✅ Iot Thing {thing_name} exists: {util.link_to_iot_thing(thing_name)}")
  except ClientError as e:
    if e.response["Error"]["Code"] == "ResourceNotFoundException":
      print(f"❌ IoT Thing {thing_name} missing: {thing_name}")
    else:
      raise

def check_persister_iam_role():
  role_name = globals.persister_iam_role_name()

  try:
    globals.aws_iam_client.get_role(RoleName=role_name)
    print(f"✅ Persister IAM Role exists: {util.link_to_iam_role(role_name)}")
  except ClientError as e:
    if e.response["Error"]["Code"] == "NoSuchEntity":
      print(f"❌ Persister IAM Role missing: {role_name}")
    else:
      raise

def check_persister_lambda_function():
  function_name = globals.persister_lambda_function_name()

  try:
    globals.aws_lambda_client.get_function(FunctionName=function_name)
    print(f"✅ Persister Lambda Function exists: {util.link_to_lambda_function(function_name)}")
  except ClientError as e:
    if e.response["Error"]["Code"] == "ResourceNotFoundException":
      print(f"❌ Persister Lambda Function missing: {function_name}")
    else:
      raise

def check_event_checker_iam_role():
  role_name = globals.event_checker_iam_role_name()

  try:
    globals.aws_iam_client.get_role(RoleName=role_name)
    print(f"✅ Event Checker IAM Role exists: {util.link_to_iam_role(role_name)}")
  except ClientError as e:
    if e.response["Error"]["Code"] == "NoSuchEntity":
      print(f"❌ Event Checker IAM Role missing: {role_name}")
    else:
      raise

def check_event_checker_lambda_function():
  function_name = globals.event_checker_lambda_function_name()

  try:
    globals.aws_lambda_client.get_function(FunctionName=function_name)
    print(f"✅ Event Checker Lambda Function exists: {util.link_to_lambda_function(function_name)}")
  except ClientError as e:
    if e.response["Error"]["Code"] == "ResourceNotFoundException":
      print(f"❌ Event Checker Lambda Function missing: {function_name}")
    else:
      raise

def check_event_checker_iam_role():
  role_name = globals.event_checker_iam_role_name()

  try:
    globals.aws_iam_client.get_role(RoleName=role_name)
    print(f"✅ Event-Checker IAM Role exists: {util.link_to_iam_role(role_name)}")
  except ClientError as e:
    if e.response["Error"]["Code"] == "NoSuchEntity":
      print(f"❌ Event-Checker IAM Role missing: {role_name}")
    else:
      raise

def check_event_checker_lambda_function():
  function_name = globals.event_checker_lambda_function_name()

  try:
    globals.aws_lambda_client.get_function(FunctionName=function_name)
    print(f"✅ Event-Checker Lambda Function exists: {util.link_to_lambda_function(function_name)}")
  except ClientError as e:
    if e.response["Error"]["Code"] == "ResourceNotFoundException":
      print(f"❌ Event-Checker Lambda Function missing: {function_name}")
    else:
      raise

def check_processor_iam_role(iot_device):
  role_name = globals.processor_iam_role_name(iot_device)

  try:
    globals.aws_iam_client.get_role(RoleName=role_name)
    print(f"✅ Processor {role_name} IAM Role exists: {util.link_to_iam_role(role_name)}")
  except ClientError as e:
    if e.response["Error"]["Code"] == "NoSuchEntity":
      print(f"❌ Processor {role_name} IAM Role missing: {role_name}")
    else:
      raise

def check_processor_lambda_function(iot_device):
  function_name = globals.processor_lambda_function_name(iot_device)

  try:
    globals.aws_lambda_client.get_function(FunctionName=function_name)
    print(f"✅ Processor {function_name} Lambda Function exists: {util.link_to_lambda_function(function_name)}")
  except ClientError as e:
    if e.response["Error"]["Code"] == "ResourceNotFoundException":
      print(f"❌ Processor {function_name} Lambda Function missing: {function_name}")
    else:
      raise

def check_hot_dynamodb_table():
  table_name = globals.hot_dynamodb_table_name()

  try:
    globals.aws_dynamodb_client.describe_table(TableName=table_name)
    print(f"✅ DynamoDb Table exists: {util.link_to_dynamodb_table(table_name)}")
  except ClientError as e:
    if e.response["Error"]["Code"] == "ResourceNotFoundException":
      print(f"❌ DynamoDb Table missing: {table_name}")
    else:
      raise

def check_hot_cold_mover_iam_role():
  role_name = globals.hot_cold_mover_iam_role_name()

  try:
    globals.aws_iam_client.get_role(RoleName=role_name)
    print(f"✅ Hot to Cold Mover IAM Role exists: {util.link_to_iam_role(role_name)}")
  except ClientError as e:
    if e.response["Error"]["Code"] == "NoSuchEntity":
      print(f"❌ Hot to Cold Mover IAM Role missing: {role_name}")
    else:
      raise

def check_hot_cold_mover_lambda_function():
  function_name = globals.hot_cold_mover_lambda_function_name()

  try:
    globals.aws_lambda_client.get_function(FunctionName=function_name)
    print(f"✅ Hot to Cold Mover Lambda Function exists: {util.link_to_lambda_function(function_name)}")
  except ClientError as e:
    if e.response["Error"]["Code"] == "ResourceNotFoundException":
      print(f"❌ Hot to Cold Mover Lambda Function missing: {function_name}")
    else:
      raise

def check_hot_cold_mover_event_rule():
  rule_name = globals.hot_cold_mover_event_rule_name()

  try:
    globals.aws_events_client.describe_rule(Name=rule_name)
    print(f"✅ Hot to Cold Mover EventBridge Rule exists: {util.link_to_event_rule(rule_name)}")
  except ClientError as e:
    if e.response["Error"]["Code"] == "ResourceNotFoundException":
      print(f"❌ Hot to Cold Mover EventBridge Rule missing: {rule_name}")
    else:
      raise

def check_hot_reader_iam_role():
  role_name = globals.hot_reader_iam_role_name()

  try:
    globals.aws_iam_client.get_role(RoleName=role_name)
    print(f"✅ Hot Reader IAM Role exists: {util.link_to_iam_role(role_name)}")
  except ClientError as e:
    if e.response["Error"]["Code"] == "NoSuchEntity":
      print(f"❌ Hot Reader IAM Role missing: {role_name}")
    else:
      raise

def check_hot_reader_lambda_function():
  function_name = globals.hot_reader_lambda_function_name()

  try:
    globals.aws_lambda_client.get_function(FunctionName=function_name)
    print(f"✅ Hot Reader Lambda Function exists: {util.link_to_lambda_function(function_name)}")
  except ClientError as e:
    if e.response["Error"]["Code"] == "ResourceNotFoundException":
      print(f"❌ Hot Reader Lambda Function missing: {function_name}")
    else:
      raise

def check_hot_reader_last_entry_iam_role():
  role_name = globals.hot_reader_last_entry_iam_role_name()

  try:
    globals.aws_iam_client.get_role(RoleName=role_name)
    print(f"✅ Hot Reader Last Entry IAM Role exists: {util.link_to_iam_role(role_name)}")
  except ClientError as e:
    if e.response["Error"]["Code"] == "NoSuchEntity":
      print(f"❌ Hot Reader Last Entry IAM Role missing: {role_name}")
    else:
      raise

def check_hot_reader_last_entry_lambda_function():
  function_name = globals.hot_reader_last_entry_lambda_function_name()

  try:
    globals.aws_lambda_client.get_function(FunctionName=function_name)
    print(f"✅ Hot Reader Last Entry Lambda Function exists: {util.link_to_lambda_function(function_name)}")
  except ClientError as e:
    if e.response["Error"]["Code"] == "ResourceNotFoundException":
      print(f"❌ Hot Reader Last Entry Lambda Function missing: {function_name}")
    else:
      raise

def check_cold_s3_bucket():
  bucket_name = globals.cold_s3_bucket_name()

  try:
    globals.aws_s3_client.head_bucket(Bucket=bucket_name)
    print(f"✅ Cold S3 Bucket exists: {util.link_to_s3_bucket(bucket_name)}")
  except ClientError as e:
    if int(e.response["Error"]["Code"]) == 404:
      print(f"❌ Cold S3 Bucket missing: {bucket_name}")
    else:
      raise

def check_cold_archive_mover_iam_role():
  role_name = globals.cold_archive_mover_iam_role_name()

  try:
    globals.aws_iam_client.get_role(RoleName=role_name)
    print(f"✅ Cold to Archive Mover IAM Role exists: {util.link_to_iam_role(role_name)}")
  except ClientError as e:
    if e.response["Error"]["Code"] == "NoSuchEntity":
      print(f"❌ Cold to Archive Mover IAM Role missing: {role_name}")
    else:
      raise

def check_cold_archive_mover_lambda_function():
  function_name = globals.cold_archive_mover_lambda_function_name()

  try:
    globals.aws_lambda_client.get_function(FunctionName=function_name)
    print(f"✅ Cold to Archive Mover Lambda Function exists: {util.link_to_lambda_function(function_name)}")
  except ClientError as e:
    if e.response["Error"]["Code"] == "ResourceNotFoundException":
      print(f"❌ Cold to Archive Mover Lambda Function missing: {function_name}")
    else:
      raise

def check_cold_archive_mover_event_rule():
  rule_name = globals.cold_archive_mover_event_rule_name()

  try:
    globals.aws_events_client.describe_rule(Name=rule_name)
    print(f"✅ Cold to Archive Mover EventBridge Rule exists: {util.link_to_event_rule(rule_name)}")
  except ClientError as e:
    if e.response["Error"]["Code"] == "ResourceNotFoundException":
      print(f"❌ Cold to Archive Mover EventBridge Rule missing: {rule_name}")
    else:
      raise

def check_archive_s3_bucket():
  bucket_name = globals.archive_s3_bucket_name()

  try:
    globals.aws_s3_client.head_bucket(Bucket=bucket_name)
    print(f"✅ Archive S3 Bucket exists: {util.link_to_s3_bucket(bucket_name)}")
  except ClientError as e:
    if int(e.response["Error"]["Code"]) == 404:
      print(f"❌ Archive S3 Bucket missing: {bucket_name}")
    else:
      raise

def check_twinmaker_s3_bucket():
  bucket_name = globals.twinmaker_s3_bucket_name()

  try:
    globals.aws_s3_client.head_bucket(Bucket=bucket_name)
    print(f"✅ Twinmaker S3 Bucket exists: {util.link_to_s3_bucket(bucket_name)}")
  except ClientError as e:
    if int(e.response["Error"]["Code"]) == 404:
      print(f"❌ Twinmaker S3 Bucket missing: {bucket_name}")
    else:
      raise

def check_twinmaker_iam_role():
  role_name = globals.twinmaker_iam_role_name()

  try:
    globals.aws_iam_client.get_role(RoleName=role_name)
    print(f"✅ Twinmaker IAM Role exists: {util.link_to_iam_role(role_name)}")
  except ClientError as e:
    if e.response["Error"]["Code"] == "NoSuchEntity":
      print(f"❌ Twinmaker IAM Role missing: {role_name}")
    else:
      raise

def check_twinmaker_workspace():
  workspace_name = globals.twinmaker_workspace_name()

  try:
    globals.aws_twinmaker_client.get_workspace(workspaceId=workspace_name)
    print(f"✅ Twinmaker Workspace exists: {util.link_to_twinmaker_workspace(workspace_name)}")
  except ClientError as e:
    if e.response["Error"]["Code"] == "ResourceNotFoundException":
      print(f"❌ Twinmaker Workspace missing: {workspace_name}")
    else:
      raise

def check_twinmaker_component_type(iot_device):
  workspace_name = globals.twinmaker_workspace_name()
  component_type_id = globals.twinmaker_component_type_id(iot_device)

  try:
    globals.aws_twinmaker_client.get_component_type(workspaceId=workspace_name, componentTypeId=component_type_id)
    print(f"✅ Twinmaker Component Type {component_type_id} exists: {util.link_to_twinmaker_component_type(workspace_name, component_type_id)}")
  except ClientError as e:
    if e.response["Error"]["Code"] == "ResourceNotFoundException":
      print(f"❌ Twinmaker Component Type {component_type_id} missing: {component_type_id}")
    else:
      raise

def check_grafana_iam_role():
  role_name = globals.grafana_iam_role_name()

  try:
    globals.aws_iam_client.get_role(RoleName=role_name)
    print(f"✅ Grafana IAM Role exists: {util.link_to_iam_role(role_name)}")
  except ClientError as e:
    if e.response["Error"]["Code"] == "NoSuchEntity":
      print(f"❌ Grafana IAM Role missing: {role_name}")
    else:
      raise

def check_grafana_workspace():
  workspace_name = globals.grafana_workspace_name()

  try:
    workspace_id = util.get_grafana_workspace_id_by_name(workspace_name)
    response = globals.aws_grafana_client.describe_workspace(workspaceId=workspace_id)
    print(f"✅ Grafana Workspace exists: {util.link_to_grafana_workspace(workspace_id)}")
    print(f"Grafana Login: https://{response["workspace"]["endpoint"]}")
  except ClientError as e:
    if e.response["Error"]["Code"] == "ResourceNotFoundException":
      print(f"❌ Grafana Workspace missing: {workspace_name}")
    else:
      raise


def check_l1():
  check_dispatcher_iam_role()
  check_dispatcher_lambda_function()
  check_dispatcher_iot_rule()

  for iot_device in globals.config_iot_devices:
    check_iot_thing(iot_device)

def check_l2():
  check_persister_iam_role()
  check_persister_lambda_function()
  check_event_checker_iam_role()
  check_event_checker_lambda_function()

  for iot_device in globals.config_iot_devices:
    check_processor_iam_role(iot_device)
    check_processor_lambda_function(iot_device)

def check_l3_hot():
  check_hot_dynamodb_table()
  check_hot_cold_mover_iam_role()
  check_hot_cold_mover_lambda_function()
  check_hot_cold_mover_event_rule()
  check_hot_reader_iam_role()
  check_hot_reader_lambda_function()
  check_hot_reader_last_entry_iam_role()
  check_hot_reader_last_entry_lambda_function()

def check_l3_cold():
  check_cold_s3_bucket()
  check_cold_archive_mover_iam_role()
  check_cold_archive_mover_lambda_function()
  check_cold_archive_mover_event_rule()

def check_l3_archive():
  check_archive_s3_bucket()

def check_l3():
  check_l3_hot()
  check_l3_cold()
  check_l3_archive()

def check_l4():
  check_twinmaker_s3_bucket()
  check_twinmaker_iam_role()
  check_twinmaker_workspace()

  for iot_device in globals.config_iot_devices:
    check_twinmaker_component_type(iot_device)

def check_l5():
  check_grafana_iam_role()
  check_grafana_workspace()


def check():
  check_l1()
  check_l2()
  check_l3()
  check_l4()
  check_l5()