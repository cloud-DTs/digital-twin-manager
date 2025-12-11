from deployers.base import Deployer
import json
import globals
import os
from botocore.exceptions import ClientError
import shutil
import util

class IotThingDeployer(Deployer):
  def log(self, message):
    print(f"IoT: {message}")

  def deploy(self, iot_device):
    thing_name = globals.iot_thing_name(iot_device)
    policy_name = globals.iot_thing_policy_name(iot_device)

    globals.aws_iot_client.create_thing(thingName=thing_name)
    self.log(f"Created IoT Thing: {thing_name}")

    cert_response = globals.aws_iot_client.create_keys_and_certificate(setAsActive=True)
    certificate_arn = cert_response['certificateArn']
    self.log(f"Created IoT Certificate: {cert_response['certificateId']}")

    dir = f"{globals.iot_data_path}/{iot_device["id"]}/"
    os.makedirs(os.path.dirname(dir), exist_ok=True)

    with open(f"{dir}certificate.pem.crt", "w") as f:
      f.write(cert_response["certificatePem"])
    with open(f"{dir}private.pem.key", "w") as f:
      f.write(cert_response["keyPair"]["PrivateKey"])
    with open(f"{dir}public.pem.key", "w") as f:
      f.write(cert_response["keyPair"]["PublicKey"])

    self.log(f"Stored certificate and keys to {dir}")

    policy_document = {
      "Version": "2012-10-17",
      "Statement": [{
        "Effect": "Allow",
        "Action": ["iot:*"],
        "Resource": "*"
      }]
    }

    globals.aws_iot_client.create_policy(policyName=policy_name, policyDocument=json.dumps(policy_document))
    self.log(f"Created IoT Policy: {policy_name}")

    globals.aws_iot_client.attach_thing_principal(thingName=thing_name, principal=certificate_arn)
    self.log(f"Attached IoT Certificate to Thing")

    globals.aws_iot_client.attach_policy(policyName=policy_name, target=certificate_arn)
    self.log(f"Attached IoT Policy to Certificate")

  def destroy(self, iot_device):
    thing_name = globals.iot_thing_name(iot_device)
    policy_name = globals.iot_thing_policy_name(iot_device)

    try:
      principals_resp = globals.aws_iot_client.list_thing_principals(thingName=thing_name)
      principals = principals_resp.get('principals', [])

      if len(principals) > 1:
        raise "Error at deleting IoT Thing: Too many principals or certificates attached. Not sure which one to delete."

      for principal in principals:
        globals.aws_iot_client.detach_thing_principal(thingName=thing_name, principal=principal)
        self.log(f"Detached IoT Certificate")

        policies = globals.aws_iot_client.list_attached_policies(target=principal)
        for p in policies.get('policies', []):
          globals.aws_iot_client.detach_policy(policyName=p['policyName'], target=principal)
          self.log(f"Detached IoT Policy")

        cert_id = principal.split('/')[-1]
        globals.aws_iot_client.update_certificate(certificateId=cert_id, newStatus='INACTIVE')
        globals.aws_iot_client.delete_certificate(certificateId=cert_id, forceDelete=True)
        self.log(f"Deleted IoT Certificate: {cert_id}")
    except ClientError as e:
      if e.response["Error"]["Code"] != "ResourceNotFoundException":
        raise

    try:
      versions = globals.aws_iot_client.list_policy_versions(policyName=policy_name).get('policyVersions', [])
      for version in versions:
        if not version['isDefaultVersion']:
          try:
            globals.aws_iot_client.delete_policy_version(policyName=policy_name, policyVersionId=version['versionId'])
            self.log(f"Deleted IoT Policy version: {version['versionId']}")
          except ClientError as e:
            if e.response["Error"]["Code"] != "ResourceNotFoundException":
              raise
    except ClientError as e:
      if e.response["Error"]["Code"] != "ResourceNotFoundException":
        raise

    try:
      globals.aws_iot_client.delete_policy(policyName=policy_name)
      self.log(f"Deleted IoT Policy: {policy_name}")
    except ClientError as e:
      if e.response["Error"]["Code"] != "ResourceNotFoundException":
        raise

    try:
      globals.aws_iot_client.describe_thing(thingName=thing_name)
      globals.aws_iot_client.delete_thing(thingName=thing_name)
      self.log(f"Deleted IoT Thing: {thing_name}")
    except ClientError as e:
      if e.response["Error"]["Code"] != "ResourceNotFoundException":
        raise

    try:
      shutil.rmtree(f"{globals.iot_data_path}/{iot_device["id"]}")
    except FileNotFoundError:
      pass

  def info(self, iot_device):
    thing_name = globals.iot_thing_name(iot_device)

    try:
      globals.aws_iot_client.describe_thing(thingName=thing_name)
      self.log(f"✅ Iot Thing {thing_name} exists: {util.link_to_iot_thing(thing_name)}")
    except ClientError as e:
      if e.response["Error"]["Code"] == "ResourceNotFoundException":
        self.log(f"❌ IoT Thing {thing_name} missing: {thing_name}")
      else:
        raise
