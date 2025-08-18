import json
import time
import globals
import util
from botocore.exceptions import ClientError


def create_dispatcher_iam_role():
  role_name = globals.dispatcher_iam_role_name()

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

  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaRole"

  globals.aws_iam_client.attach_role_policy(
    RoleName=role_name,
    PolicyArn=policy_arn
  )

  print(f"Attached IAM policy ARN: {policy_arn}")

  print(f"Waiting for propagation...")

  time.sleep(10)

def destroy_dispatcher_iam_role():
  role_name = globals.dispatcher_iam_role_name()

  try:
    # detach managed policies
    response = globals.aws_iam_client.list_attached_role_policies(RoleName=role_name)
    for policy in response["AttachedPolicies"]:
        globals.aws_iam_client.detach_role_policy(RoleName=role_name, PolicyArn=policy["PolicyArn"])

    # delete inline policies
    response = globals.aws_iam_client.list_role_policies(RoleName=role_name)
    for policy_name in response["PolicyNames"]:
        globals.aws_iam_client.delete_role_policy(RoleName=role_name, PolicyName=policy_name)

    # remove from instance profiles
    response = globals.aws_iam_client.list_instance_profiles_for_role(RoleName=role_name)
    for profile in response["InstanceProfiles"]:
      globals.aws_iam_client.remove_role_from_instance_profile(
        InstanceProfileName=profile["InstanceProfileName"],
        RoleName=role_name
      )

    # delete the role
    globals.aws_iam_client.delete_role(RoleName=role_name)
    print(f"Deleted IAM role: {role_name}")
  except ClientError as e:
    if e.response["Error"]["Code"] != "NoSuchEntity":
      raise


def create_dispatcher_lambda_function():
  function_name = globals.dispatcher_lambda_function_name()
  role_name = globals.dispatcher_iam_role_name()

  response = globals.aws_iam_client.get_role(RoleName=role_name)
  role_arn = response['Role']['Arn']

  globals.aws_lambda_client.create_function(
    FunctionName=function_name,
    Runtime="python3.13",
    Role=role_arn,
    Handler="lambda_function.lambda_handler", #  file.function
    Code={"ZipFile": util.compile_lambda_function("dispatcher")},
    Description="",
    Timeout=3, # seconds
    MemorySize=128, # MB
    Publish=True,
  )

  print(f"Created Lambda function: {function_name}")

def destroy_dispatcher_lambda_function():
  function_name = globals.dispatcher_lambda_function_name()

  try:
    globals.aws_lambda_client.delete_function(FunctionName=function_name)
    print(f"Deleted Lambda function: {function_name}")
  except ClientError as e:
    if e.response["Error"]["Code"] != "ResourceNotFoundException":
      raise


def create_dispatcher_iot_rule():
  rule_name = globals.dispatcher_iot_rule_name()
  sql = f"SELECT * FROM '{globals.config.get("general", "digital_twin_name")}/+'"

  function_name = globals.dispatcher_lambda_function_name()

  response = globals.aws_lambda_client.get_function(FunctionName=function_name)
  function_arn = response['Configuration']['FunctionArn']

  globals.aws_iot_client.create_topic_rule(
    ruleName=rule_name,
    topicRulePayload={
      "sql": sql,
      "description": "",
      "actions": [
        {
          "lambda": {
            "functionArn": function_arn
          }
        }
      ],
      "ruleDisabled": False
    }
  )

  print(f"Created IoT rule: {rule_name}")

  region = globals.aws_iot_client.meta.region_name
  account_id = globals.aws_sts_client.get_caller_identity()['Account']

  globals.aws_lambda_client.add_permission(
    FunctionName=function_name,
    StatementId="iot-invoke",
    Action="lambda:InvokeFunction",
    Principal="iot.amazonaws.com",
    SourceArn=f"arn:aws:iot:{region}:{account_id}:rule/{rule_name}"
  )

  print(f"Added permission to Lambda function so the rule can invoke the function.")

def destroy_dispatcher_iot_rule():
  function_name = globals.dispatcher_lambda_function_name()
  rule_name = globals.dispatcher_iot_rule_name()

  try:
    globals.aws_lambda_client.remove_permission(
        FunctionName=function_name,
        StatementId="iot-invoke"
    )
    print(f"Removed permission from Lambda function: {rule_name}, {function_name}")
  except globals.aws_lambda_client.exceptions.ResourceNotFoundException:
    pass

  if util.iot_rule_exists(rule_name):
    try:
      globals.aws_iot_client.delete_topic_rule(ruleName=rule_name)
      print(f"Deleted IoT Rule: {rule_name}")
    except globals.aws_iot_client.exceptions.ResourceNotFoundException:
      pass


def create_persister_iam_role():
  role_name = globals.persister_iam_role_name()

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

  policy_arn = "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess_v2"

  globals.aws_iam_client.attach_role_policy(
    RoleName=role_name,
    PolicyArn=policy_arn
  )

  print(f"Attached IAM policy ARN: {policy_arn}")

  print(f"Waiting for propagation...")

  time.sleep(10)

def destroy_persister_iam_role():
  role_name = globals.persister_iam_role_name()

  try:
    # detach managed policies
    response = globals.aws_iam_client.list_attached_role_policies(RoleName=role_name)
    for policy in response["AttachedPolicies"]:
        globals.aws_iam_client.detach_role_policy(RoleName=role_name, PolicyArn=policy["PolicyArn"])

    # delete inline policies
    response = globals.aws_iam_client.list_role_policies(RoleName=role_name)
    for policy_name in response["PolicyNames"]:
        globals.aws_iam_client.delete_role_policy(RoleName=role_name, PolicyName=policy_name)

    # remove from instance profiles
    response = globals.aws_iam_client.list_instance_profiles_for_role(RoleName=role_name)
    for profile in response["InstanceProfiles"]:
      globals.aws_iam_client.remove_role_from_instance_profile(
        InstanceProfileName=profile["InstanceProfileName"],
        RoleName=role_name
      )

    # delete the role
    globals.aws_iam_client.delete_role(RoleName=role_name)
    print(f"Deleted IAM role: {role_name}")
  except ClientError as e:
    if e.response["Error"]["Code"] != "NoSuchEntity":
      raise


def create_persister_lambda_function():
  function_name = globals.persister_lambda_function_name()
  role_name = globals.persister_iam_role_name()

  response = globals.aws_iam_client.get_role(RoleName=role_name)
  role_arn = response['Role']['Arn']

  globals.aws_lambda_client.create_function(
    FunctionName=function_name,
    Runtime="python3.13",
    Role=role_arn,
    Handler="lambda_function.lambda_handler", #  file.function
    Code={"ZipFile": util.compile_lambda_function("persister")},
    Description="",
    Timeout=3, # seconds
    MemorySize=128, # MB
    Publish=True,
  )

  print(f"Created Lambda function: {function_name}")

def destroy_persister_lambda_function():
  function_name = globals.persister_lambda_function_name()

  try:
    globals.aws_lambda_client.delete_function(FunctionName=function_name)
    print(f"Deleted Lambda function: {function_name}")
  except ClientError as e:
    if e.response["Error"]["Code"] != "ResourceNotFoundException":
      raise


def create_iot_data_dynamodb_table():
  table_name = globals.dynamodb_table_name()

  globals.aws_dynamodb_client.create_table(
    TableName=table_name,
    KeySchema=[
      {'AttributeName': 'iot_device_id', 'KeyType': 'HASH'},  # partition key
      {'AttributeName': 'id', 'KeyType': 'RANGE'}             # sort key
    ],
    AttributeDefinitions=[
      {'AttributeName': 'iot_device_id', 'AttributeType': 'S'},
      {'AttributeName': 'id', 'AttributeType': 'S'}
    ],
    BillingMode='PAY_PER_REQUEST'
  )

  print(f"Creation of DynamoDb table initiated: {table_name}")

  waiter = globals.aws_dynamodb_client.get_waiter('table_exists')
  waiter.wait(TableName=table_name)

  print(f"Created DynamoDb table: {table_name}")

def destroy_iot_data_dynamodb_table():
  table_name = globals.dynamodb_table_name()

  try:
    globals.aws_dynamodb_client.delete_table(TableName=table_name)
  except ClientError as e:
    if e.response['Error']['Code'] == 'ResourceNotFoundException':
      return
    else:
      raise

  print(f"Deletion of DynamoDb table initiated: {table_name}")

  waiter = globals.aws_dynamodb_client.get_waiter('table_not_exists')
  waiter.wait(TableName=table_name)

  print(f"Deleted DynamoDb table: {table_name}")


def create_hot_cold_mover_iam_role():
  role_name = globals.hot_cold_mover_iam_role_name()

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
    "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess_v2",
    "arn:aws:iam::aws:policy/AmazonS3FullAccess"
  ]

  for policy_arn in policy_arns:
    globals.aws_iam_client.attach_role_policy(
      RoleName=role_name,
      PolicyArn=policy_arn
    )

    print(f"Attached IAM policy ARN: {policy_arn}")

  print(f"Waiting for propagation...")

  time.sleep(10)

def destroy_hot_cold_mover_iam_role():
  role_name = globals.hot_cold_mover_iam_role_name()

  try:
    # detach managed policies
    response = globals.aws_iam_client.list_attached_role_policies(RoleName=role_name)
    for policy in response["AttachedPolicies"]:
        globals.aws_iam_client.detach_role_policy(RoleName=role_name, PolicyArn=policy["PolicyArn"])

    # delete inline policies
    response = globals.aws_iam_client.list_role_policies(RoleName=role_name)
    for policy_name in response["PolicyNames"]:
        globals.aws_iam_client.delete_role_policy(RoleName=role_name, PolicyName=policy_name)

    # remove from instance profiles
    response = globals.aws_iam_client.list_instance_profiles_for_role(RoleName=role_name)
    for profile in response["InstanceProfiles"]:
      globals.aws_iam_client.remove_role_from_instance_profile(
        InstanceProfileName=profile["InstanceProfileName"],
        RoleName=role_name
      )

    # delete the role
    globals.aws_iam_client.delete_role(RoleName=role_name)
    print(f"Deleted IAM role: {role_name}")
  except ClientError as e:
    if e.response["Error"]["Code"] != "NoSuchEntity":
      raise


def create_hot_cold_mover_lambda_function():
  function_name = globals.hot_cold_mover_lambda_function_name()
  role_name = globals.hot_cold_mover_iam_role_name()

  response = globals.aws_iam_client.get_role(RoleName=role_name)
  role_arn = response['Role']['Arn']

  globals.aws_lambda_client.create_function(
    FunctionName=function_name,
    Runtime="python3.13",
    Role=role_arn,
    Handler="lambda_function.lambda_handler", #  file.function
    Code={"ZipFile": util.compile_lambda_function("hot-to-cold-mover")},
    Description="",
    Timeout=3, # seconds
    MemorySize=128, # MB
    Publish=True,
  )

  print(f"Created Lambda function: {function_name}")

def destroy_hot_cold_mover_lambda_function():
  function_name = globals.hot_cold_mover_lambda_function_name()

  try:
    globals.aws_lambda_client.delete_function(FunctionName=function_name)
    print(f"Deleted Lambda function: {function_name}")
  except ClientError as e:
    if e.response["Error"]["Code"] != "ResourceNotFoundException":
      raise


def create_hot_cold_mover_event_rule():
  rule_name = globals.hot_cold_mover_event_rule_name()
  schedule_expression = f"rate({globals.config.get("general", "layer_3_hot_to_cold_interval_days")} days)"

  function_name = globals.hot_cold_mover_lambda_function_name()

  # create the EventBridge rule
  rule_response = globals.aws_events_client.put_rule(
    Name=rule_name,
    ScheduleExpression=schedule_expression,
    State="ENABLED",
    Description="",
  )
  rule_arn = rule_response["RuleArn"]

  print(f"Created EventBridge rule: {rule_name}")

  # add Lambda function as target
  lambda_arn = globals.aws_lambda_client.get_function(FunctionName=function_name)["Configuration"]["FunctionArn"]

  globals.aws_events_client.put_targets(
    Rule=rule_name,
    Targets=[
        {
            "Id": "1",
            "Arn": lambda_arn,
        }
    ]
  )

  print(f"Added Lambda function as target.")

  # grant EventBridge permission to invoke the Lambda function
  globals.aws_lambda_client.add_permission(
    FunctionName=function_name,
    StatementId="events-invoke",
    Action="lambda:InvokeFunction",
    Principal="events.amazonaws.com",
    SourceArn=rule_arn,
  )

  print(f"Added permission to Lambda function so the rule can invoke the function.")

def destroy_hot_cold_mover_event_rule():
  rule_name = globals.hot_cold_mover_event_rule_name()
  function_name = globals.hot_cold_mover_lambda_function_name()

  try:
    globals.aws_lambda_client.remove_permission(FunctionName=function_name, StatementId="events-invoke")
    print(f"Removed permission from Lambda function: {rule_name}, {function_name}")
  except globals.aws_lambda_client.exceptions.ResourceNotFoundException:
    pass

  try:
    globals.aws_events_client.describe_rule(Name=rule_name)
    globals.aws_events_client.delete_rule(Name=rule_name, Force=True)
    print(f"Deleted EventBridge rule: {rule_name}")
  except globals.aws_events_client.exceptions.ResourceNotFoundException:
    pass


def create_cold_data_s3_bucket():
  bucket_name = globals.cold_s3_bucket_name()

  globals.aws_s3_client.create_bucket(
    Bucket=bucket_name,
    CreateBucketConfiguration={
        "LocationConstraint": globals.aws_s3_client.meta.region_name
    }
  )

  print(f"Created S3 Bucket: {bucket_name}")

def destroy_cold_data_s3_bucket():
  bucket_name = globals.cold_s3_bucket_name()

  util.destroy_s3_bucket(bucket_name)


def create_cold_archive_mover_iam_role():
  role_name = globals.cold_archive_mover_iam_role_name()

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

  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"

  globals.aws_iam_client.attach_role_policy(
    RoleName=role_name,
    PolicyArn=policy_arn
  )

  print(f"Attached IAM policy ARN: {policy_arn}")

  print(f"Waiting for propagation...")

  time.sleep(10)

def destroy_cold_archive_mover_iam_role():
  role_name = globals.cold_archive_mover_iam_role_name()

  try:
    # detach managed policies
    response = globals.aws_iam_client.list_attached_role_policies(RoleName=role_name)
    for policy in response["AttachedPolicies"]:
        globals.aws_iam_client.detach_role_policy(RoleName=role_name, PolicyArn=policy["PolicyArn"])

    # delete inline policies
    response = globals.aws_iam_client.list_role_policies(RoleName=role_name)
    for policy_name in response["PolicyNames"]:
        globals.aws_iam_client.delete_role_policy(RoleName=role_name, PolicyName=policy_name)

    # remove from instance profiles
    response = globals.aws_iam_client.list_instance_profiles_for_role(RoleName=role_name)
    for profile in response["InstanceProfiles"]:
      globals.aws_iam_client.remove_role_from_instance_profile(
        InstanceProfileName=profile["InstanceProfileName"],
        RoleName=role_name
      )

    # delete the role
    globals.aws_iam_client.delete_role(RoleName=role_name)
    print(f"Deleted IAM role: {role_name}")
  except ClientError as e:
    if e.response["Error"]["Code"] != "NoSuchEntity":
      raise


def create_cold_archive_mover_lambda_function():
  function_name = globals.cold_archive_mover_lambda_function_name()
  role_name = globals.cold_archive_mover_iam_role_name()

  response = globals.aws_iam_client.get_role(RoleName=role_name)
  role_arn = response['Role']['Arn']

  globals.aws_lambda_client.create_function(
    FunctionName=function_name,
    Runtime="python3.13",
    Role=role_arn,
    Handler="lambda_function.lambda_handler", #  file.function
    Code={"ZipFile": util.compile_lambda_function("cold-to-archive-mover")},
    Description="",
    Timeout=3, # seconds
    MemorySize=128, # MB
    Publish=True,
  )

  print(f"Created Lambda function: {function_name}")

def destroy_cold_archive_mover_lambda_function():
  function_name = globals.cold_archive_mover_lambda_function_name()

  try:
    globals.aws_lambda_client.delete_function(FunctionName=function_name)
    print(f"Deleted Lambda function: {function_name}")
  except ClientError as e:
    if e.response["Error"]["Code"] != "ResourceNotFoundException":
      raise


def create_cold_archive_mover_event_rule():
  rule_name = globals.cold_archive_mover_event_rule_name()
  schedule_expression = f"rate({globals.config.get("general", "layer_3_cold_to_archive_interval_days")} days)"

  function_name = globals.cold_archive_mover_lambda_function_name()

  # create the EventBridge rule
  rule_response = globals.aws_events_client.put_rule(
    Name=rule_name,
    ScheduleExpression=schedule_expression,
    State="ENABLED",
    Description="",
  )
  rule_arn = rule_response["RuleArn"]

  print(f"Created EventBridge rule: {rule_name}")

  # add Lambda function as target
  lambda_arn = globals.aws_lambda_client.get_function(FunctionName=function_name)["Configuration"]["FunctionArn"]

  globals.aws_events_client.put_targets(
    Rule=rule_name,
    Targets=[
        {
            "Id": "1",
            "Arn": lambda_arn,
        }
    ]
  )

  print(f"Added Lambda function as target.")

  # grant EventBridge permission to invoke the Lambda function
  globals.aws_lambda_client.add_permission(
    FunctionName=function_name,
    StatementId="events-invoke",
    Action="lambda:InvokeFunction",
    Principal="events.amazonaws.com",
    SourceArn=rule_arn,
  )

  print(f"Added permission to Lambda function so the rule can invoke the function.")

def destroy_cold_archive_mover_event_rule():
  rule_name = globals.cold_archive_mover_event_rule_name()
  function_name = globals.cold_archive_mover_lambda_function_name()

  try:
    globals.aws_lambda_client.remove_permission(FunctionName=function_name, StatementId="events-invoke")
    print(f"Removed permission from Lambda function: {rule_name}, {function_name}")
  except globals.aws_lambda_client.exceptions.ResourceNotFoundException:
    pass

  try:
    globals.aws_events_client.describe_rule(Name=rule_name)
    globals.aws_events_client.delete_rule(Name=rule_name, Force=True)
    print(f"Deleted EventBridge rule: {rule_name}")
  except globals.aws_events_client.exceptions.ResourceNotFoundException:
    pass


def create_archive_data_s3_bucket():
  bucket_name = globals.archive_s3_bucket_name()

  globals.aws_s3_client.create_bucket(
    Bucket=bucket_name,
    CreateBucketConfiguration={
        "LocationConstraint": globals.aws_s3_client.meta.region_name
    }
  )

  print(f"Created S3 Bucket: {bucket_name}")

def destroy_archive_data_s3_bucket():
  bucket_name = globals.archive_s3_bucket_name()

  util.destroy_s3_bucket(bucket_name)


def create_twinmaker_s3_bucket():
  bucket_name = globals.twinmaker_s3_bucket_name()

  globals.aws_s3_client.create_bucket(
    Bucket=bucket_name,
    CreateBucketConfiguration={
        "LocationConstraint": globals.aws_s3_client.meta.region_name
    }
  )

  print(f"Created S3 Bucket: {bucket_name}")

def destroy_twinmaker_s3_bucket():
  bucket_name = globals.twinmaker_s3_bucket_name()

  util.destroy_s3_bucket(bucket_name)


def create_twinmaker_iam_role():
  role_name = globals.twinmaker_iam_role_name()

  globals.aws_iam_client.create_role(
      RoleName=role_name,
      AssumeRolePolicyDocument=json.dumps(
        {
          "Version": "2012-10-17",
          "Statement": [
            {
              "Effect": "Allow",
              "Principal": {
                "Service": "iottwinmaker.amazonaws.com"
              },
              "Action": "sts:AssumeRole"
            }
          ]
        }
      )
  )
  print(f"Created IAM role: {role_name}")

  policy_name = "TwinMakerExecutionPolicy"

  globals.aws_iam_client.put_role_policy(
    RoleName=role_name,
    PolicyName=policy_name,
    PolicyDocument=json.dumps({
      "Version": "2012-10-17",
      "Statement": [
        {
          "Effect": "Allow",
          "Action": [
            "s3:*",
            "lambda:*",
          ],
          "Resource": "*"
        }
      ]
  })
  )
  print(f"Attached inline IAM policy: {policy_name}")

  print(f"Waiting for propagation...")
  time.sleep(10)

def destroy_twinmaker_iam_role():
  role_name = globals.twinmaker_iam_role_name()

  try:
    # detach managed policies
    response = globals.aws_iam_client.list_attached_role_policies(RoleName=role_name)
    for policy in response["AttachedPolicies"]:
        globals.aws_iam_client.detach_role_policy(RoleName=role_name, PolicyArn=policy["PolicyArn"])

    # delete inline policies
    response = globals.aws_iam_client.list_role_policies(RoleName=role_name)
    for policy_name in response["PolicyNames"]:
        globals.aws_iam_client.delete_role_policy(RoleName=role_name, PolicyName=policy_name)

    # remove from instance profiles
    response = globals.aws_iam_client.list_instance_profiles_for_role(RoleName=role_name)
    for profile in response["InstanceProfiles"]:
      globals.aws_iam_client.remove_role_from_instance_profile(
        InstanceProfileName=profile["InstanceProfileName"],
        RoleName=role_name
      )

    # delete the role
    globals.aws_iam_client.delete_role(RoleName=role_name)
    print(f"Deleted IAM role: {role_name}")
  except ClientError as e:
    if e.response["Error"]["Code"] != "NoSuchEntity":
      raise


def create_twinmaker_workspace():
  workspace_name = globals.twinmaker_workspace_name()
  role_name = globals.twinmaker_iam_role_name()
  bucket_name = globals.twinmaker_s3_bucket_name()

  account_id = globals.aws_sts_client.get_caller_identity()['Account']

  globals.aws_twinmaker_client.create_workspace(
    workspaceId=workspace_name,
    role=f"arn:aws:iam::{account_id}:role/{role_name}",
    s3Location=f"arn:aws:s3:::{bucket_name}",
    description=""
  )

  print(f"Created IoT TwinMaker workspace: {workspace_name}")

def destroy_twinmaker_workspace():
  workspace_name = globals.twinmaker_workspace_name()

  try:
    response = globals.aws_twinmaker_client.list_entities(workspaceId=workspace_name)
    deleted_an_entity = False
    for entity in response.get("entitySummaries", []):
      try:
        globals.aws_twinmaker_client.delete_entity(workspaceId=workspace_name, entityId=entity["entityId"], isRecursive=True)
        deleted_an_entity = True
        print(f"Deleted IoT TwinMaker entity: {entity["entityId"]}")
      except ClientError as e:
        if e.response["Error"]["Code"] != "ResourceNotFoundException":
          raise

    if deleted_an_entity:
      print(f"Waiting for propagation...")
      time.sleep(10)
  except ClientError as e:
    if e.response["Error"]["Code"] != "ValidationException":
      raise

  try:
    response = globals.aws_twinmaker_client.list_scenes(workspaceId=workspace_name)
    for scene in response.get("sceneSummaries", []):
      try:
        globals.aws_twinmaker_client.delete_scene(workspaceId=workspace_name, sceneId=scene["sceneId"])
        print(f"Deleted IoT TwinMaker scene: {scene["sceneId"]}")
      except ClientError as e:
        if e.response["Error"]["Code"] != "ResourceNotFoundException":
          raise
  except ClientError as e:
    if e.response["Error"]["Code"] != "ValidationException":
      raise

  try:
    response = globals.aws_twinmaker_client.list_component_types(workspaceId=workspace_name)
    for componentType in response.get("componentTypeSummaries", []):
      if componentType["componentTypeId"].startswith("com.amazon"):
        continue
      try:
        globals.aws_twinmaker_client.delete_component_type(workspaceId=workspace_name, componentTypeId=componentType["componentTypeId"])
        print(f"Deleted IoT TwinMaker component type: {componentType["componentTypeId"]}")
      except ClientError as e:
        if e.response["Error"]["Code"] != "ResourceNotFoundException":
          raise
  except ClientError as e:
    if e.response["Error"]["Code"] != "ValidationException":
      raise

  try:
    globals.aws_twinmaker_client.delete_workspace(workspaceId=workspace_name)
  except ClientError as e:
    if e.response["Error"]["Code"] == "ResourceNotFoundException":
      return
    else:
      raise

  print(f"Deletion of IoT TwinMaker workspace initiated: {workspace_name}")

  while True:
    try:
      globals.aws_twinmaker_client.get_workspace(workspaceId=workspace_name)
      time.sleep(2)
    except ClientError as e:
      if e.response["Error"]["Code"] == "ResourceNotFoundException":
        break
      else:
        raise

  print(f"Deleted IoT TwinMaker workspace: {workspace_name}")


def create_grafana_iam_role():
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

  print(f"Created IAM role: {role_name}")

  print(f"Waiting for propagation...")
  time.sleep(10)

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

  print(f"Updated IAM role trust policy: {role_name}")

  # https://docs.aws.amazon.com/grafana/latest/userguide/AMG-manage-permissions.html

  # policy_arns = [
  #   "arn:aws:iam::aws:policy/service-role/AmazonGrafanaCloudWatchAccess",
  #   "arn:aws:iam::aws:policy/service-role/AWSIoTSiteWiseReadOnlyAccess",
  # ]

  # for policy_arn in policy_arns:
  #   globals.aws_iam_client.attach_role_policy(
  #     RoleName=role_name,
  #     PolicyArn=policy_arn
  #   )

  #   print(f"Attached IAM policy ARN: {policy_arn}")

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
              "s3:*"
            ],
            "Resource": "*"
          }
        ]
      }
    )
  )
  print(f"Attached inline IAM policy: {policy_name}")

  print(f"Waiting for propagation...")
  time.sleep(10)

def destroy_grafana_iam_role():
  role_name = globals.grafana_iam_role_name()

  try:
    # detach managed policies
    response = globals.aws_iam_client.list_attached_role_policies(RoleName=role_name)
    for policy in response["AttachedPolicies"]:
        globals.aws_iam_client.detach_role_policy(RoleName=role_name, PolicyArn=policy["PolicyArn"])

    # delete inline policies
    response = globals.aws_iam_client.list_role_policies(RoleName=role_name)
    for policy_name in response["PolicyNames"]:
        globals.aws_iam_client.delete_role_policy(RoleName=role_name, PolicyName=policy_name)

    # remove from instance profiles
    response = globals.aws_iam_client.list_instance_profiles_for_role(RoleName=role_name)
    for profile in response["InstanceProfiles"]:
      globals.aws_iam_client.remove_role_from_instance_profile(
        InstanceProfileName=profile["InstanceProfileName"],
        RoleName=role_name
      )

    # delete the role
    globals.aws_iam_client.delete_role(RoleName=role_name)
    print(f"Deleted IAM role: {role_name}")
  except ClientError as e:
    if e.response["Error"]["Code"] != "NoSuchEntity":
      raise


def create_grafana_workspace():
  workspace_name = globals.grafana_workspace_name()
  role_name = globals.grafana_iam_role_name()

  response = globals.aws_iam_client.get_role(RoleName=role_name)
  role_arn = response["Role"]["Arn"]

  response = globals.aws_grafana_client.create_workspace(
    workspaceName=workspace_name,
    workspaceDescription="",
    grafanaVersion="10.4",
    accountAccessType="CURRENT_ACCOUNT",
    authenticationProviders=["AWS_SSO"],
    permissionType="CUSTOMER_MANAGED",
    workspaceRoleArn=role_arn,
    configuration=json.dumps(
      {
        "plugins": {
          "pluginAdminEnabled": True
        },
        # "unifiedAlerting": {
        #   "enabled": True
        # }
      }
    ),
    tags={
        "Environment": "Dev"
    }
  )
  workspace_id = response["workspace"]["id"]

  print(f"Creation of Grafana workspace initiated: {workspace_name}")

  while True:
    response = globals.aws_grafana_client.describe_workspace(workspaceId=workspace_id)
    if response['workspace']['status'] == "ACTIVE":
      break
    time.sleep(2)

  print(f"Created Grafana workspace: {workspace_name}")

def destroy_grafana_workspace():
  workspace_name = globals.grafana_workspace_name()

  try:
    workspace_id = util.get_grafana_workspace_id_by_name(workspace_name)
    globals.aws_grafana_client.delete_workspace(workspaceId=workspace_id)
  except ClientError as e:
    if e.response["Error"]["Code"] == "ResourceNotFoundException":
      return
    else:
      raise

  print(f"Deletion of Grafana workspace initiated: {workspace_name}")

  while True:
    try:
      globals.aws_grafana_client.describe_workspace(workspaceId=workspace_id)
      time.sleep(2)
    except ClientError as e:
      if e.response["Error"]["Code"] == "ResourceNotFoundException":
        break
      else:
        raise

  print(f"Deleted Grafana workspace: {workspace_name}")


def add_cors_to_twinmaker_s3_bucket():
  bucket_name = globals.twinmaker_s3_bucket_name()
  grafana_workspace_id = util.get_grafana_workspace_id_by_name(globals.grafana_workspace_name())

  globals.aws_s3_client.put_bucket_cors(
      Bucket=bucket_name,
      CORSConfiguration={
        "CORSRules": [
          {
            "AllowedOrigins": [f"https://grafana.{globals.aws_grafana_client.meta.region_name}.amazonaws.com/workspaces/{grafana_workspace_id}"],
            "AllowedMethods": ["GET"],
            "AllowedHeaders": ["*"],
            "MaxAgeSeconds": 3000
          }
        ]
      }
  )

  print(f"CORS configuration applied to bucket: {bucket_name}")
  print(f"------- allowed origin: {f"https://grafana.{globals.aws_grafana_client.meta.region_name}.amazonaws.com/workspaces/{grafana_workspace_id}"}")

def remove_cors_from_twinmaker_s3_bucket():
  bucket_name = globals.twinmaker_s3_bucket_name()

  try:
    globals.aws_s3_client.get_bucket_cors(Bucket=bucket_name)
    globals.aws_s3_client.delete_bucket_cors(Bucket=bucket_name)
  except ClientError as e:
    if e.response["Error"]["Code"] == "NoSuchBucket" or e.response["Error"]["Code"] == "NoSuchCORSConfiguration":
      return
    else:
      raise

  print(f"CORS configuration removed from bucket: {bucket_name}")


def deploy_core_services_l1():
  create_dispatcher_iam_role()
  create_dispatcher_lambda_function()
  create_dispatcher_iot_rule()

def destroy_core_services_l1():
  destroy_dispatcher_iot_rule()
  destroy_dispatcher_lambda_function()
  destroy_dispatcher_iam_role()


def deploy_core_services_l2():
  create_persister_iam_role()
  create_persister_lambda_function()

def destroy_core_services_l2():
  destroy_persister_lambda_function()
  destroy_persister_iam_role()


def deploy_core_services_l3_hot():
  create_iot_data_dynamodb_table()
  create_hot_cold_mover_iam_role()
  create_hot_cold_mover_lambda_function()
  create_hot_cold_mover_event_rule()

def destroy_core_services_l3_hot():
  destroy_hot_cold_mover_event_rule()
  destroy_hot_cold_mover_lambda_function()
  destroy_hot_cold_mover_iam_role()
  destroy_iot_data_dynamodb_table()


def deploy_core_services_l3_cold():
  create_cold_data_s3_bucket()
  create_cold_archive_mover_iam_role()
  create_cold_archive_mover_lambda_function()
  create_cold_archive_mover_event_rule()

def destroy_core_services_l3_cold():
  destroy_cold_archive_mover_event_rule()
  destroy_cold_archive_mover_lambda_function()
  destroy_cold_archive_mover_iam_role()
  destroy_cold_data_s3_bucket()


def deploy_core_services_l3_archive():
  create_archive_data_s3_bucket()

def destroy_core_services_l3_archive():
  destroy_archive_data_s3_bucket()


def deploy_core_services_l4():
  create_twinmaker_s3_bucket()
  create_twinmaker_iam_role()
  create_twinmaker_workspace()

def destroy_core_services_l4():
  destroy_twinmaker_workspace()
  destroy_twinmaker_iam_role()
  destroy_twinmaker_s3_bucket()


def deploy_core_services_l5():
  create_grafana_iam_role()
  create_grafana_workspace()
  add_cors_to_twinmaker_s3_bucket()

def destroy_core_services_l5():
  remove_cors_from_twinmaker_s3_bucket()
  destroy_grafana_workspace()
  destroy_grafana_iam_role()


def deploy():
  deploy_core_services_l1()
  deploy_core_services_l2()
  deploy_core_services_l3_hot()
  deploy_core_services_l3_cold()
  deploy_core_services_l3_archive()
  deploy_core_services_l4()
  deploy_core_services_l5()

def destroy():
  destroy_core_services_l5()
  destroy_core_services_l4()
  destroy_core_services_l3_archive()
  destroy_core_services_l3_cold()
  destroy_core_services_l3_hot()
  destroy_core_services_l2()
  destroy_core_services_l1()
