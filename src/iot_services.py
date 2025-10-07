import json
import globals
import os
from botocore.exceptions import ClientError
import shutil
import time
import util


def create_iot_thing(iot_device):
  thing_name = globals.iot_thing_name(iot_device)
  policy_name = globals.iot_thing_policy_name(iot_device)

  globals.aws_iot_client.create_thing(thingName=thing_name)
  print(f"Created IoT Thing: {thing_name}")

  cert_response = globals.aws_iot_client.create_keys_and_certificate(setAsActive=True)
  certificate_arn = cert_response['certificateArn']
  print(f"Created IoT Certificate: {cert_response['certificateId']}")

  dir = f"{globals.iot_data_path}/{iot_device["id"]}/"
  os.makedirs(os.path.dirname(dir), exist_ok=True)

  with open(f"{dir}certificate.pem.crt", "w") as f:
    f.write(cert_response["certificatePem"])
  with open(f"{dir}private.pem.key", "w") as f:
    f.write(cert_response["keyPair"]["PrivateKey"])
  with open(f"{dir}public.pem.key", "w") as f:
    f.write(cert_response["keyPair"]["PublicKey"])

  print(f"Stored certificate and keys to {dir}")

  policy_document = {
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": ["iot:*"],
      "Resource": "*"
    }]
  }

  globals.aws_iot_client.create_policy(policyName=policy_name, policyDocument=json.dumps(policy_document))
  print(f"Created IoT Policy: {policy_name}")

  globals.aws_iot_client.attach_thing_principal(thingName=thing_name, principal=certificate_arn)
  print(f"Attached IoT Certificate to Thing")

  globals.aws_iot_client.attach_policy(policyName=policy_name, target=certificate_arn)
  print(f"Attached IoT Policy to Certificate")

def destroy_iot_thing(iot_device):
  thing_name = globals.iot_thing_name(iot_device)
  policy_name = globals.iot_thing_policy_name(iot_device)

  try:
    principals_resp = globals.aws_iot_client.list_thing_principals(thingName=thing_name)
    principals = principals_resp.get('principals', [])

    if len(principals) > 1:
      raise "Error at deleting IoT Thing: Too many principals or certificates attached. Not sure which one to delete."

    for principal in principals:
      globals.aws_iot_client.detach_thing_principal(thingName=thing_name, principal=principal)
      print(f"Detached IoT Certificate")

      policies = globals.aws_iot_client.list_attached_policies(target=principal)
      for p in policies.get('policies', []):
        globals.aws_iot_client.detach_policy(policyName=p['policyName'], target=principal)
        print(f"Detached IoT Policy")

      cert_id = principal.split('/')[-1]
      globals.aws_iot_client.update_certificate(certificateId=cert_id, newStatus='INACTIVE')
      globals.aws_iot_client.delete_certificate(certificateId=cert_id, forceDelete=True)
      print(f"Deleted IoT Certificate: {cert_id}")
  except ClientError as e:
    if e.response["Error"]["Code"] != "ResourceNotFoundException":
      raise

  try:
    versions = globals.aws_iot_client.list_policy_versions(policyName=policy_name).get('policyVersions', [])
    for version in versions:
      if not version['isDefaultVersion']:
        try:
          globals.aws_iot_client.delete_policy_version(policyName=policy_name, policyVersionId=version['versionId'])
          print(f"Deleted IoT Policy version: {version['versionId']}")
        except ClientError as e:
          if e.response["Error"]["Code"] != "ResourceNotFoundException":
            raise
  except ClientError as e:
    if e.response["Error"]["Code"] != "ResourceNotFoundException":
      raise

  try:
    globals.aws_iot_client.delete_policy(policyName=policy_name)
    print(f"Deleted IoT Policy: {policy_name}")
  except ClientError as e:
    if e.response["Error"]["Code"] != "ResourceNotFoundException":
      raise

  try:
    globals.aws_iot_client.describe_thing(thingName=thing_name)
    globals.aws_iot_client.delete_thing(thingName=thing_name)
    print(f"Deleted IoT Thing: {thing_name}")
  except ClientError as e:
    if e.response["Error"]["Code"] != "ResourceNotFoundException":
      raise

  try:
    shutil.rmtree(f"{globals.iot_data_path}/{iot_device["id"]}")
  except FileNotFoundError:
    pass


def create_processor_iam_role(iot_device):
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

  print(f"Created IAM role: {role_name}")

  policy_arns = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    "arn:aws:iam::aws:policy/service-role/AWSLambdaRole"
  ]

  for policy_arn in policy_arns:
    globals.aws_iam_client.attach_role_policy(
      RoleName=role_name,
      PolicyArn=policy_arn
    )

    print(f"Attached IAM policy ARN: {policy_arn}")

  print(f"Waiting for propagation...")

  time.sleep(10)

def destroy_processor_iam_role(iot_device):
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
    print(f"Deleted IAM role: {role_name}")
  except ClientError as e:
    if e.response["Error"]["Code"] != "NoSuchEntity":
      raise


def create_processor_lambda_function(iot_device):
  function_name = globals.processor_lambda_function_name(iot_device)
  role_name = globals.processor_iam_role_name(iot_device)

  response = globals.aws_iam_client.get_role(RoleName=role_name)
  role_arn = response['Role']['Arn']

  if os.path.exists(os.path.join(globals.project_path(), globals.lambda_functions_path, function_name)):
    function_name_local = function_name
  else:
    function_name_local = "default-processor"

  globals.aws_lambda_client.create_function(
    FunctionName=function_name,
    Runtime="python3.13",
    Role=role_arn,
    Handler="lambda_function.lambda_handler", #  file.function
    Code={"ZipFile": util.compile_lambda_function(os.path.join(globals.lambda_functions_path, function_name_local))},
    Description="",
    Timeout=3, # seconds
    MemorySize=128, # MB
    Publish=True,
    Environment={
      "Variables": {
        "DIGITAL_TWIN_INFO": json.dumps(globals.digital_twin_info()),
        "PERSISTER_LAMBDA_NAME": globals.persister_lambda_function_name()
      }
    }
  )

  print(f"Created Lambda function: {function_name}")

def destroy_processor_lambda_function(iot_device):
  function_name = globals.processor_lambda_function_name(iot_device)

  try:
    globals.aws_lambda_client.delete_function(FunctionName=function_name)
    print(f"Deleted Lambda function: {function_name}")
  except ClientError as e:
    if e.response["Error"]["Code"] != "ResourceNotFoundException":
      raise


def create_twinmaker_component_type(iot_device):
  connector_function_name = globals.twinmaker_connector_lambda_function_name()
  connector_last_entry_function_name = globals.twinmaker_connector_last_entry_lambda_function_name()
  workspace_name = globals.twinmaker_workspace_name()
  component_type_id = globals.twinmaker_component_type_id(iot_device)

  response = globals.aws_lambda_client.get_function(FunctionName=connector_function_name)
  connector_function_arn = response["Configuration"]["FunctionArn"]

  response = globals.aws_lambda_client.get_function(FunctionName=connector_last_entry_function_name)
  connector_last_entry_function_arn = response["Configuration"]["FunctionArn"]

  property_definitions = {}

  if "properties" in iot_device:
    for property in iot_device["properties"]:
      property_definitions[property["name"]] = {
        "dataType": {
          "type": property["dataType"]
        },
        "isTimeSeries": True,
        "isStoredExternally": True
      }

  if "constProperties" in iot_device:
    for const_property in iot_device["constProperties"]:
      property_definitions[const_property["name"]] = {
        "dataType": {
          "type": const_property["dataType"]
        },
        "defaultValue": {
          f"{const_property["dataType"].lower()}Value": const_property["value"]
        },
        "isTimeSeries": False,
        "isStoredExternally": False
      }

  functions = {}

  functions = {
    "dataReader": {
      "implementedBy": {
        "lambda": {
          "arn": connector_function_arn
        }
      }
    },
    "attributePropertyValueReaderByEntity": {
      "implementedBy": {
        "lambda": {
          "arn": connector_last_entry_function_arn
        }
      }
    }
  }

  globals.aws_twinmaker_client.create_component_type(
    workspaceId=workspace_name,
    componentTypeId=component_type_id,
    propertyDefinitions=property_definitions,
    functions=functions
  )

  print(f"Creation of IoT Twinmaker Component Type initiated: {component_type_id}")

  while True:
    response = globals.aws_twinmaker_client.get_component_type(workspaceId=workspace_name, componentTypeId=component_type_id)
    if response["status"]["state"] == "ACTIVE":
      break
    time.sleep(2)

  print(f"Created IoT Twinmaker Component Type: {component_type_id}")

def destroy_twinmaker_component_type(iot_device):
  workspace_name = globals.twinmaker_workspace_name()
  component_type_id = globals.twinmaker_component_type_id(iot_device)

  try:
    globals.aws_twinmaker_client.get_component_type(workspaceId=workspace_name, componentTypeId=component_type_id)
  except ClientError as e:
    if e.response['Error']['Code'] == 'ResourceNotFoundException':
      return

  try:
    response = globals.aws_twinmaker_client.list_entities(workspaceId=workspace_name)

    for entity in response.get("entitySummaries", []):
      entity_details = globals.aws_twinmaker_client.get_entity(workspaceId=workspace_name, entityId=entity["entityId"])
      components = entity_details.get("components", {})
      component_updates = {}

      for comp_name, comp in components.items():
        if comp.get("componentTypeId") == component_type_id:
          component_updates[comp_name] = {"updateType": "DELETE"}

      if component_updates:
        globals.aws_twinmaker_client.update_entity(workspaceId=workspace_name, entityId=entity["entityId"], componentUpdates=component_updates)
        print("Deletion of components initiated.")

        while True:
          entity_details_2 = globals.aws_twinmaker_client.get_entity(workspaceId=workspace_name, entityId=entity["entityId"])
          components_2 = entity_details_2.get("components", {})

          if not set(component_updates.keys()) & set(components_2.keys()):
            print(f"Deleted components.")
            break
          else:
            time.sleep(2)

  except ClientError as e:
    if e.response["Error"]["Code"] != "ValidationException":
      raise

  print(f"Deleted all IoT Twinmaker Components with component type id: {component_type_id}")

  globals.aws_twinmaker_client.delete_component_type(workspaceId=workspace_name, componentTypeId=component_type_id)

  print(f"Deletion of IoT Twinmaker Component Type initiated: {component_type_id}")

  while True:
    try:
      globals.aws_twinmaker_client.get_component_type(workspaceId=workspace_name, componentTypeId=component_type_id)
      time.sleep(2)
    except ClientError as e:
      if e.response['Error']['Code'] == 'ResourceNotFoundException':
        break
      else:
        raise

  print(f"Deleted IoT Twinmaker Component Type: {component_type_id}")


def deploy_l1():
  for iot_device in globals.config_iot_devices:
    create_iot_thing(iot_device)

def destroy_l1():
  for iot_device in globals.config_iot_devices:
    destroy_iot_thing(iot_device)


def deploy_l2():
  for iot_device in globals.config_iot_devices:
    create_processor_iam_role(iot_device)
    create_processor_lambda_function(iot_device)

def destroy_l2():
  for iot_device in globals.config_iot_devices:
    destroy_processor_lambda_function(iot_device)
    destroy_processor_iam_role(iot_device)


def deploy_l4():
  for iot_device in globals.config_iot_devices:
    create_twinmaker_component_type(iot_device)

def destroy_l4():
  for iot_device in globals.config_iot_devices:
    destroy_twinmaker_component_type(iot_device)


def deploy():
  deploy_l1()
  deploy_l2()
  deploy_l4()

def destroy():
  destroy_l4()
  destroy_l2()
  destroy_l1()
