from deployers.base import Deployer
import json
import os
import globals
import util
from botocore.exceptions import ClientError

class HotColdMoverLambdaFunctionDeployer(Deployer):
  def log(self, message):
    print(f"Core: {message}")

  def deploy(self):
    function_name = globals.hot_cold_mover_lambda_function_name()
    role_name = globals.hot_cold_mover_iam_role_name()

    response = globals.aws_iam_client.get_role(RoleName=role_name)
    role_arn = response["Role"]["Arn"]

    globals.aws_lambda_client.create_function(
      FunctionName=function_name,
      Runtime="python3.13",
      Role=role_arn,
      Handler="lambda_function.lambda_handler", #  file.function
      Code={"ZipFile": util.compile_lambda_function(os.path.join(globals.core_lfs_path, "hot-to-cold-mover"))},
      Description="",
      Timeout=3, # seconds
      MemorySize=128, # MB
      Publish=True,
      Environment={
        "Variables": {
          "DIGITAL_TWIN_INFO": json.dumps(globals.digital_twin_info()),
          "DYNAMODB_TABLE_NAME": globals.hot_dynamodb_table_name(),
          "S3_BUCKET_NAME": globals.cold_s3_bucket_name()
        }
      }
    )

    self.log(f"Created Lambda function: {function_name}")

  def destroy(self):
    function_name = globals.hot_cold_mover_lambda_function_name()

    try:
      globals.aws_lambda_client.delete_function(FunctionName=function_name)
      self.log(f"Deleted Lambda function: {function_name}")
    except ClientError as e:
      if e.response["Error"]["Code"] != "ResourceNotFoundException":
        raise

  def info(self):
    function_name = globals.hot_cold_mover_lambda_function_name()

    try:
      globals.aws_lambda_client.get_function(FunctionName=function_name)
      self.log(f"✅ Hot to Cold Mover Lambda Function exists: {util.link_to_lambda_function(function_name)}")
    except ClientError as e:
      if e.response["Error"]["Code"] == "ResourceNotFoundException":
        self.log(f"❌ Hot to Cold Mover Lambda Function missing: {function_name}")
      else:
        raise
