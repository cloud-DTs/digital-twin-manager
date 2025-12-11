from deployers.base import Deployer
import json
import globals
from botocore.exceptions import ClientError
import time
import util

class ProcessorIamRoleDeployer(Deployer):
  def log(self, message):
    print(f"IoT: {message}")

  def deploy(self, iot_device):
    role_name = globals.processor_iam_role_name(iot_device)

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
      "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
      "arn:aws:iam::aws:policy/service-role/AWSLambdaRole"
    ]

    for policy_arn in policy_arns:
      globals.aws_iam_client.attach_role_policy(
        RoleName=role_name,
        PolicyArn=policy_arn
      )

      self.log(f"Attached IAM policy ARN: {policy_arn}")

    self.log(f"Waiting for propagation...")

    time.sleep(10)

  def destroy(self, iot_device):
    role_name = globals.processor_iam_role_name(iot_device)

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

  def info(self, iot_device):
    role_name = globals.processor_iam_role_name(iot_device)

    try:
      globals.aws_iam_client.get_role(RoleName=role_name)
      self.log(f"✅ Processor {role_name} IAM Role exists: {util.link_to_iam_role(role_name)}")
    except ClientError as e:
      if e.response["Error"]["Code"] == "NoSuchEntity":
        self.log(f"❌ Processor {role_name} IAM Role missing: {role_name}")
      else:
        raise
