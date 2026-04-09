from deployers.base import Deployer
import json
import time
import globals
import util
from botocore.exceptions import ClientError


class EventRegistryRegisterIamRoleDeployer(Deployer):
    def log(self, message):
        print(f"Core: {message}")

    def deploy(self):
        role_name = globals.event_registry_register_iam_role_name()

        globals.aws_iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps({
                "Version": "2012-10-17",
                "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]
            })
        )
        self.log(f"Created IAM role: {role_name}")

        globals.aws_iam_client.attach_role_policy(
            RoleName=role_name,
            PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
        )

        ssm_prefix = globals.ssm_registry_prefix()

        globals.aws_iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName="EventRegistrySsmAccess",
            PolicyDocument=json.dumps({
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Action": ["ssm:PutParameter", "ssm:DeleteParameter", "ssm:GetParametersByPath"],
                    "Resource": [f"arn:aws:ssm:*:*:parameter{ssm_prefix}", f"arn:aws:ssm:*:*:parameter{ssm_prefix}/*"]
                }]
            })
        )
        self.log(f"Attached SSM policy (path: {ssm_prefix}/*) to: {role_name}")

        self.log("Waiting for IAM propagation...")
        time.sleep(20)

    def destroy(self):
        role_name = globals.event_registry_register_iam_role_name()
        try:
            for p in globals.aws_iam_client.list_attached_role_policies(RoleName=role_name)["AttachedPolicies"]:
                globals.aws_iam_client.detach_role_policy(RoleName=role_name, PolicyArn=p["PolicyArn"])
            for pn in globals.aws_iam_client.list_role_policies(RoleName=role_name)["PolicyNames"]:
                globals.aws_iam_client.delete_role_policy(RoleName=role_name, PolicyName=pn)
            globals.aws_iam_client.delete_role(RoleName=role_name)
            self.log(f"Deleted IAM role: {role_name}")
        except ClientError as e:
            if e.response["Error"]["Code"] != "NoSuchEntity":
                raise

    def info(self):
        role_name = globals.event_registry_register_iam_role_name()
        try:
            globals.aws_iam_client.get_role(RoleName=role_name)
            self.log(f"✅ IAM Role exists: {role_name} {util.link_to_iam_role(role_name)}")
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":
                self.log(f"❌ IAM Role missing: {role_name}")
            else:
                raise
