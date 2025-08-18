import os
import zipfile
import globals
from botocore.exceptions import ClientError

def compile_lambda_function(lambda_function_name):
  zip_path = zip_directory(os.path.join(globals.lambda_functions_path, lambda_function_name))

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
