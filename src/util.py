import os
import zipfile
import globals
from botocore.exceptions import ClientError

def compile_lambda_function(relative_folder_path):
  zip_path = zip_directory(relative_folder_path)

  with open(zip_path, "rb") as f:
    zip_code = f.read()

  return zip_code

def zip_directory(relative_folder_path, zip_name='zipped.zip'):
  folder_path = os.path.join(globals.project_path(), relative_folder_path)
  output_path = os.path.join(folder_path, zip_name)

  with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(folder_path):
      for file in files:
        full_path = os.path.join(root, file)
        if full_path == output_path:
          continue
        arcname = os.path.relpath(full_path, start=folder_path)
        zf.write(full_path, arcname)

  return output_path

def iot_rule_exists(rule_name):
  paginator = globals.aws_iot_client.get_paginator('list_topic_rules')
  for page in paginator.paginate():
      for rule in page.get('rules', []):
          if rule['ruleName'] == rule_name:
              return True
  return False

def destroy_s3_bucket(bucket_name):
  try:
    paginator = globals.aws_s3_client.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket_name):
      if 'Contents' in page:
        objects = [{'Key': obj['Key']} for obj in page['Contents']]
        globals.aws_s3_client.delete_objects(Bucket=bucket_name, Delete={'Objects': objects})
    print(f"Deleted all objects from S3 Bucket: {bucket_name}")
  except ClientError as e:
    if e.response['Error']['Code'] != 'NoSuchBucket':
      raise

  try:
    paginator = globals.aws_s3_client.get_paginator('list_object_versions')
    for page in paginator.paginate(Bucket=bucket_name):
      versions = page.get('Versions', []) + page.get('DeleteMarkers', [])
      if versions:
        objects = [{'Key': v['Key'], 'VersionId': v['VersionId']} for v in versions]
        globals.aws_s3_client.delete_objects(Bucket=bucket_name, Delete={'Objects': objects})
    print(f"Deleted all object versions from S3 Bucket: {bucket_name}")
  except ClientError as e:
    if e.response['Error']['Code'] != 'NoSuchBucket':
      raise

  try:
    globals.aws_s3_client.delete_bucket(Bucket=bucket_name)
    print(f"Deleted S3 Bucket: {bucket_name}")
  except ClientError as e:
    if e.response['Error']['Code'] != 'NoSuchBucket':
      raise

def get_grafana_workspace_id_by_name(workspace_name):
    paginator = globals.aws_grafana_client.get_paginator("list_workspaces")

    for page in paginator.paginate():
        for workspace in page["workspaces"]:
            if workspace["name"] == workspace_name:
                return workspace["id"] if "id" in workspace else workspace["workspaceId"]

    error_response = {
      "Error": {
        "Code": "ResourceNotFoundException",
        "Message": "The requested resource was not found."
      }
    }

    operation_name = "get_grafana_workspace_id_by_name"

    raise ClientError(error_response, operation_name)

def link_to_iam_role(role_name):
  return f"https://console.aws.amazon.com/iam/home?region={globals.aws_iam_client.meta.region_name}#/roles/{role_name}"

def link_to_lambda_function(function_name):
  return f"https://console.aws.amazon.com/lambda/home?region={globals.aws_lambda_client.meta.region_name}#/functions/{function_name}"

def link_to_iot_rule(rule_name):
  return f"https://console.aws.amazon.com/iot/home?region={globals.aws_iot_client.meta.region_name}#/rule/{rule_name}"

def link_to_iot_thing(thing_name):
  return f"https://console.aws.amazon.com/iot/home?region={globals.aws_iot_client.meta.region_name}#/thing/{thing_name}"

def link_to_dynamodb_table(table_name):
  return f"https://console.aws.amazon.com/dynamodbv2/home?region={globals.aws_dynamodb_client.meta.region_name}#table?name={table_name}"

def link_to_event_rule(rule_name):
  return f"https://console.aws.amazon.com/events/home?region={globals.aws_events_client.meta.region_name}#/eventbus/default/rules/{rule_name}"

def link_to_s3_bucket(bucket_name):
  return f"https://console.aws.amazon.com/s3/buckets/{bucket_name}"

def link_to_twinmaker_workspace(workspace_name):
  return f"https://console.aws.amazon.com/iottwinmaker/home?region={globals.aws_twinmaker_client.meta.region_name}#/workspaces/{workspace_name}"

def link_to_twinmaker_component_type(workspace_name, component_type_id):
  return f"https://console.aws.amazon.com/iottwinmaker/home?region={globals.aws_twinmaker_client.meta.region_name}#/workspaces/{workspace_name}/component-types/{component_type_id}"

def link_to_twinmaker_entity(workspace_name, entity_id):
  return f"https://console.aws.amazon.com/iottwinmaker/home?region={globals.aws_twinmaker_client.meta.region_name}#/workspaces/{workspace_name}/entities/{entity_id}"

def link_to_twinmaker_component(workspace_name, entity_id, component_name):
  return f"https://console.aws.amazon.com/iottwinmaker/home?region={globals.aws_twinmaker_client.meta.region_name}#/workspaces/{workspace_name}/entities/{entity_id}/components/{component_name}"

def link_to_grafana_workspace(workspace_id):
  return f"https://console.aws.amazon.com/grafana/home?region={globals.aws_grafana_client.meta.region_name}#/workspaces/{workspace_id}"