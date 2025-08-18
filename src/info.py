import globals
from botocore.exceptions import ClientError


def check_dispatcher_iam_role():
  role_name = globals.dispatcher_iam_role_name()

  try:
    globals.aws_iam_client.get_role(RoleName=role_name)
    print(f"✅ Dispatcher IAM Role exists: {role_name}")
  except ClientError as e:
    if e.response["Error"]["Code"] == "NoSuchEntityException":
      print(f"❌ Dispatcher IAM Role missing: {role_name}")
    else:
      raise


def check_dispatcher_lambda_function():
  function_name = globals.dispatcher_lambda_function_name()

  try:
    globals.aws_lambda_client.get_function(FunctionName=function_name)
    print(f"✅ Dispatcher Lambda Function exists: {function_name}")
  except ClientError as e:
    if e.response['Error']['Code'] == "ResourceNotFoundException":
      print(f"❌ Dispatcher Lambda Function missing: {function_name}")
    else:
      raise


def check_dispatcher_iot_rule():
  rule_name = globals.dispatcher_iot_rule_name()

  try:
    globals.aws_iot_client.get_topic_rule(ruleName=rule_name)
    print(f"✅ Dispatcher Iot Rule exists: {rule_name}")
  except ClientError as e:
    if e.response['Error']['Code'] == "ResourceNotFoundException":
      print(f"❌ Dispatcher IoT Rule missing: {rule_name}")
    else:
      raise


def check_iot_thing(iot_device):
  thing_name = globals.iot_thing_name(iot_device)

  try:
    globals.aws_iot_client.describe_thing(thingName=thing_name)
    print(f"✅ Iot Thing exists: {thing_name}")
  except ClientError as e:
    if e.response['Error']['Code'] == "ResourceNotFoundException":
      print(f"❌ IoT Thing missing: {thing_name}")
    else:
      raise


def check_persister_iam_role():
  role_name = globals.persister_iam_role_name()

  try:
    globals.aws_iam_client.get_role(RoleName=role_name)
    print(f"✅ Persister IAM Role exists: {role_name}")
  except ClientError as e:
    if e.response["Error"]["Code"] == "NoSuchEntityException":
      print(f"❌ Persister IAM Role missing: {role_name}")
    else:
      raise


def check_persister_lambda_function():
  function_name = globals.persister_lambda_function_name()

  try:
    globals.aws_lambda_client.get_function(FunctionName=function_name)
    print(f"✅ Persister Lambda Function exists: {function_name}")
  except ClientError as e:
    if e.response['Error']['Code'] == "ResourceNotFoundException":
      print(f"❌ Persister Lambda Function missing: {function_name}")
    else:
      raise


def check_preprocessor_iam_role(iot_device):
  role_name = globals.preprocessor_iam_role_name(iot_device)

  try:
    globals.aws_iam_client.get_role(RoleName=role_name)
    print(f"✅ Preprocessor IAM Role exists: {role_name}")
  except ClientError as e:
    if e.response["Error"]["Code"] == "NoSuchEntityException":
      print(f"❌ Preprocessor IAM Role missing: {role_name}")
    else:
      raise


def check_preprocessor_lambda_function(iot_device):
  function_name = globals.preprocessor_lambda_function_name(iot_device)

  try:
    globals.aws_lambda_client.get_function(FunctionName=function_name)
    print(f"✅ Preprocessor Lambda Function exists: {function_name}")
  except ClientError as e:
    if e.response['Error']['Code'] == "ResourceNotFoundException":
      print(f"❌ Preprocessor Lambda Function missing: {function_name}")
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

  for iot_device in globals.config_iot_devices:
    check_preprocessor_iam_role(iot_device)
    check_preprocessor_lambda_function(iot_device)


def check_l3():
  pass


def check():
  check_l1()
  check_l2()
  check_l3()