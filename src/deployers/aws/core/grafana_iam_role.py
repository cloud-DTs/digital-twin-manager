from deployers.base import Deployer
import json
import time
import globals
import util
from botocore.exceptions import ClientError

class GrafanaIamRoleDeployer(Deployer):
  def log(self, message):
    print(f"Core: {message}")

  def deploy(self):
    role_name = globals.grafana_iam_role_name()

    response = globals.aws_iam_client.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=json.dumps(
          {
            "Version": "2012-10-17",
            "Statement": [
              {
                "Effect": "Allow",
                "Principal": {
                  "Service": "grafana.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
              }
            ]
          }
        )
    )
    role_arn = response["Role"]["Arn"]

    self.log(f"Created IAM role: {role_name}")

    self.log(f"Waiting for propagation...")
    time.sleep(20)

    trust_policy = globals.aws_iam_client.get_role(RoleName=role_name)['Role']['AssumeRolePolicyDocument']

    if isinstance(trust_policy['Statement'], dict):
      trust_policy['Statement'] = [trust_policy['Statement']]

    new_statement = {
        "Effect": "Allow",
        "Principal": {
            "AWS": role_arn
        },
        "Action": "sts:AssumeRole"
    }

    trust_policy['Statement'].append(new_statement)

    globals.aws_iam_client.update_assume_role_policy(
        RoleName=role_name,
        PolicyDocument=json.dumps(trust_policy)
    )

    self.log(f"Updated IAM role trust policy: {role_name}")

    policy_name = "GrafanaExecutionPolicy"

    globals.aws_iam_client.put_role_policy(
      RoleName=role_name,
      PolicyName=policy_name,
      PolicyDocument=json.dumps(
        {
          "Version": "2012-10-17",
          "Statement": [
            {
              "Effect": "Allow",
              "Action": "iottwinmaker:ListWorkspaces",
              "Resource": "*"
            },
            {
              "Effect": "Allow",
              "Action": [
                "iottwinmaker:*",
              ],
              "Resource": "*"
            },
            {
              "Effect": "Allow",
              "Action": [
                "dynamodb:*",
              ],
              "Resource": "*"
            },
            {
              "Effect": "Allow",
              "Action": [
                "s3:*"
              ],
              "Resource": "*"
            }
          ]
        }
      )
    )
    self.log(f"Attached inline IAM policy: {policy_name}")

    self.log(f"Waiting for propagation...")
    time.sleep(20)

  def destroy(self):
    role_name = globals.grafana_iam_role_name()

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

  def info(self):
    role_name = globals.grafana_iam_role_name()

    try:
      globals.aws_iam_client.get_role(RoleName=role_name)
      self.log(f"✅ Grafana IAM Role exists: {util.link_to_iam_role(role_name)}")
    except ClientError as e:
      if e.response["Error"]["Code"] == "NoSuchEntity":
        self.log(f"❌ Grafana IAM Role missing: {role_name}")
      else:
        raise
