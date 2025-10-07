import json
import os
import time
import globals
import util
from botocore.exceptions import ClientError


def create_iam_role(role_name):
  globals.aws_iam_client.create_role(
      RoleName=role_name,
      AssumeRolePolicyDocument=json.dumps(
        {
          "Version": "2012-10-17",
          "Statement": [
            {
              "Effect": "Allow",
              "Principal": {
                "Service": "lambda.amazonaws.com"
              },
              "Action": "sts:AssumeRole"
            }
          ]
        }
      )
  )

  log(f"Created IAM role: {role_name}")

  policy_arns = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  ]

  for policy_arn in policy_arns:
    globals.aws_iam_client.attach_role_policy(
      RoleName=role_name,
      PolicyArn=policy_arn
    )

    log(f"Attached IAM policy ARN: {policy_arn}")

def destroy_iam_role(role_name):
  try:
    response = globals.aws_iam_client.list_attached_role_policies(RoleName=role_name)
    for policy in response["AttachedPolicies"]:
        globals.aws_iam_client.detach_role_policy(RoleName=role_name, PolicyArn=policy["PolicyArn"])

    response = globals.aws_iam_client.list_role_policies(RoleName=role_name)
    for policy_name in response["PolicyNames"]:
        globals.aws_iam_client.delete_role_policy(RoleName=role_name, PolicyName=policy_name)

    response = globals.aws_iam_client.list_instance_profiles_for_role(RoleName=role_name)
    for profile in response["InstanceProfiles"]:
      globals.aws_iam_client.remove_role_from_instance_profile(
        InstanceProfileName=profile["InstanceProfileName"],
        RoleName=role_name
      )

    globals.aws_iam_client.delete_role(RoleName=role_name)
    log(f"Deleted IAM role: {role_name}")
  except ClientError as e:
    if e.response["Error"]["Code"] != "NoSuchEntity":
      raise

def info_iam_role(role_name):
  try:
    globals.aws_iam_client.get_role(RoleName=role_name)
    log(f"✅ IAM Role exists: {role_name} {util.link_to_iam_role(role_name)}")
  except ClientError as e:
    if e.response["Error"]["Code"] == "NoSuchEntity":
      log(f"❌ IAM Role missing: {role_name}")
    else:
      raise


def create_lambda_function(function_name):
  role_name = function_name

  response = globals.aws_iam_client.get_role(RoleName=role_name)
  role_arn = response['Role']['Arn']

  globals.aws_lambda_client.create_function(
    FunctionName=function_name,
    Runtime="python3.13",
    Role=role_arn,
    Handler="lambda_function.lambda_handler", #  file.function
    Code={"ZipFile": util.compile_lambda_function(os.path.join(globals.event_actions_path, function_name))},
    Description="",
    Timeout=3, # seconds
    MemorySize=128, # MB
    Publish=True,
    Environment={
      "Variables": {
        "DIGITAL_TWIN_INFO": json.dumps(globals.digital_twin_info())
      }
    }
  )

  log(f"Created Lambda function: {function_name}")

def destroy_lambda_function(function_name):
  try:
    globals.aws_lambda_client.delete_function(FunctionName=function_name)
    log(f"Deleted Lambda function: {function_name}")
  except ClientError as e:
    if e.response["Error"]["Code"] != "ResourceNotFoundException":
      raise

def info_lambda_function(function_name):
  try:
    globals.aws_lambda_client.get_function(FunctionName=function_name)
    log(f"✅ Lambda Function exists: {function_name} {util.link_to_lambda_function(function_name)}")
  except ClientError as e:
    if e.response["Error"]["Code"] == "ResourceNotFoundException":
      log(f"❌ Lambda Function missing: {function_name}")
    else:
      raise


def deploy_lambda_actions():
  for event in globals.config_events:
    a = event["action"]
    if a["type"] == "lambda" and ("autoDeploy" not in a or a["autoDeploy"] == True):
      create_iam_role(a["functionName"])

    log(f"Waiting for propagation...")
    time.sleep(20)

    if a["type"] == "lambda" and ("autoDeploy" not in a or a["autoDeploy"] == True):
      create_lambda_function(a["functionName"])

def destroy_lambda_actions():
  for event in globals.config_events:
    a = event["action"]
    if a["type"] == "lambda" and ("autoDeploy" not in a or a["autoDeploy"] == True):
      destroy_lambda_function(a["functionName"])
      destroy_iam_role(a["functionName"])

def info_lambda_actions():
  for event in globals.config_events:
    a = event["action"]
    if a["type"] == "lambda" and ("autoDeploy" not in a or a["autoDeploy"] == True):
      info_iam_role(a["functionName"])
      info_lambda_function(a["functionName"])



def log(string):
  print(f"Event Action Deployer: " + string)

def deploy():
  deploy_lambda_actions()

def destroy():
  destroy_lambda_actions()

def redeploy():
  destroy_lambda_actions()
  deploy_lambda_actions()

def info():
  info_lambda_actions()