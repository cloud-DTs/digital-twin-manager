from deployers.base import Deployer
import json
import os
import time
import globals
import util
from botocore.exceptions import ClientError

class LambdaActionsDeployer(Deployer):
  def log(self, message):
    print(f"Event Actions: {message}")


  def _create_iam_role(self, role_name):
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

    self.log(f"Created IAM role: {role_name}")

    policy_arns = [
      "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
    ]

    for policy_arn in policy_arns:
      globals.aws_iam_client.attach_role_policy(
        RoleName=role_name,
        PolicyArn=policy_arn
      )

      self.log(f"Attached IAM policy ARN: {policy_arn}")

  def _destroy_iam_role(self, role_name):
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
      self.log(f"Deleted IAM role: {role_name}")
    except ClientError as e:
      if e.response["Error"]["Code"] != "NoSuchEntity":
        raise

  def _info_iam_role(self, role_name):
    try:
      globals.aws_iam_client.get_role(RoleName=role_name)
      self.log(f"✅ IAM Role exists: {role_name} {util.link_to_iam_role(role_name)}")
    except ClientError as e:
      if e.response["Error"]["Code"] == "NoSuchEntity":
        self.log(f"❌ IAM Role missing: {role_name}")
      else:
        raise


  def _create_lambda_function(self, function_name, path_to_code_folder=None):
    role_name = function_name

    response = globals.aws_iam_client.get_role(RoleName=role_name)
    role_arn = response["Role"]["Arn"]

    if path_to_code_folder == None:
      path_to_code_folder = os.path.join(globals.event_action_lfs_path, function_name)

    globals.aws_lambda_client.create_function(
      FunctionName=function_name,
      Runtime="python3.13",
      Role=role_arn,
      Handler="lambda_function.lambda_handler", #  file.function
      Code={"ZipFile": util.compile_lambda_function(path_to_code_folder)},
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

    self.log(f"Created Lambda function: {function_name}")

  def _destroy_lambda_function(self, function_name):
    try:
      globals.aws_lambda_client.delete_function(FunctionName=function_name)
      self.log(f"Deleted Lambda function: {function_name}")
    except ClientError as e:
      if e.response["Error"]["Code"] != "ResourceNotFoundException":
        raise

  def _info_lambda_function(self, function_name):
    try:
      globals.aws_lambda_client.get_function(FunctionName=function_name)
      self.log(f"✅ Lambda Function exists: {function_name} {util.link_to_lambda_function(function_name)}")
    except ClientError as e:
      if e.response["Error"]["Code"] == "ResourceNotFoundException":
        self.log(f"❌ Lambda Function missing: {function_name}")
      else:
        raise


  def deploy(self):
    for event in globals.config_events:
      a = event["action"]
      if a["type"] == "lambda" and ("autoDeploy" not in a or a["autoDeploy"] == True):
        self._create_iam_role(a["functionName"])

        self.log(f"Waiting for propagation...")
        time.sleep(20)

        self._create_lambda_function(a["functionName"], a.get("pathToCode"))

  def destroy(self):
    for event in globals.config_events:
      a = event["action"]
      if a["type"] == "lambda" and ("autoDeploy" not in a or a["autoDeploy"] == True):
        self._destroy_lambda_function(a["functionName"])
        self._destroy_iam_role(a["functionName"])

  def info(self):
    for event in globals.config_events:
      a = event["action"]
      if a["type"] == "lambda" and ("autoDeploy" not in a or a["autoDeploy"] == True):
        self._info_iam_role(a["functionName"])
        self._info_lambda_function(a["functionName"])
