from deployers.base import Deployer
import json
import globals
import os
from botocore.exceptions import ClientError
import util

class ProcessorLambdaFunctionDeployer(Deployer):
  def log(self, message):
    print(f"IoT: {message}")

  def deploy(self, iot_device):
    function_name = globals.processor_lambda_function_name(iot_device)
    function_name_local = globals.processor_lambda_function_name_local(iot_device)
    role_name = globals.processor_iam_role_name(iot_device)

    response = globals.aws_iam_client.get_role(RoleName=role_name)
    role_arn = response["Role"]["Arn"]

    path_to_code_folder = os.path.join(globals.project_path(), globals.processor_lfs_path, function_name_local)

    if not os.path.exists(path_to_code_folder):
      path_to_code_folder = os.path.join(globals.project_path(), globals.core_lfs_path, "default-processor")

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
          "DIGITAL_TWIN_INFO": json.dumps(globals.digital_twin_info()),
          "PERSISTER_LAMBDA_NAME": globals.persister_lambda_function_name()
        }
      }
    )

    self.log(f"Created Lambda function: {function_name}")

  def destroy(self, iot_device):
    function_name = globals.processor_lambda_function_name(iot_device)

    try:
      globals.aws_lambda_client.delete_function(FunctionName=function_name)
      self.log(f"Deleted Lambda function: {function_name}")
    except ClientError as e:
      if e.response["Error"]["Code"] != "ResourceNotFoundException":
        raise

  def info(self, iot_device):
    function_name = globals.processor_lambda_function_name(iot_device)

    try:
      globals.aws_lambda_client.get_function(FunctionName=function_name)
      self.log(f"✅ Processor {function_name} Lambda Function exists: {util.link_to_lambda_function(function_name)}")
    except ClientError as e:
      if e.response["Error"]["Code"] == "ResourceNotFoundException":
        self.log(f"❌ Processor {function_name} Lambda Function missing: {function_name}")
      else:
        raise
