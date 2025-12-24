from deployers.base import Deployer
import json
import os
import globals
import util
from botocore.exceptions import ClientError

class EventCheckerLambdaFunctionDeployer(Deployer):
  def log(self, message):
    print(f"Core: {message}")

  def deploy(self):
    function_name = globals.event_checker_lambda_function_name()
    role_name = globals.event_checker_iam_role_name()

    response = globals.aws_iam_client.get_role(RoleName=role_name)
    role_arn = response["Role"]["Arn"]

    region = globals.aws_lambda_client.meta.region_name
    account_id = globals.aws_sts_client.get_caller_identity()['Account']
    lambda_chain_name = globals.lambda_chain_step_function_name()
    lambda_chain_arn = f"arn:aws:states:{region}:{account_id}:stateMachine:{lambda_chain_name}"

    event_feedback_lambda_function = globals.event_feedback_lambda_function_name()
    response = globals.aws_lambda_client.get_function(FunctionName=event_feedback_lambda_function)
    event_feedback_lambda_function_arn = response["Configuration"]["FunctionArn"]

    globals.aws_lambda_client.create_function(
      FunctionName=function_name,
      Runtime="python3.13",
      Role=role_arn,
      Handler="lambda_function.lambda_handler", #  file.function
      Code={"ZipFile": util.compile_lambda_function(os.path.join(globals.core_lfs_path, "event-checker"))},
      Description="",
      Timeout=3, # seconds
      MemorySize=128, # MB
      Publish=True,
      Environment={
        "Variables": {
          "DIGITAL_TWIN_INFO": json.dumps(globals.digital_twin_info()),
          "TWINMAKER_WORKSPACE_NAME": globals.twinmaker_workspace_name(),
          "LAMBDA_CHAIN_STEP_FUNCTION_ARN": lambda_chain_arn,
          "EVENT_FEEDBACK_LAMBDA_FUNCTION_ARN": event_feedback_lambda_function_arn
        }
      }
    )

    self.log(f"Created Lambda function: {function_name}")

  def destroy(self):
    function_name = globals.event_checker_lambda_function_name()

    try:
      globals.aws_lambda_client.delete_function(FunctionName=function_name)
      self.log(f"Deleted Lambda function: {function_name}")
    except ClientError as e:
      if e.response["Error"]["Code"] != "ResourceNotFoundException":
        raise

  def info(self):
    function_name = globals.event_checker_lambda_function_name()

    try:
      globals.aws_lambda_client.get_function(FunctionName=function_name)
      self.log(f"✅ Event-Checker Lambda Function exists: {util.link_to_lambda_function(function_name)}")
    except ClientError as e:
      if e.response["Error"]["Code"] == "ResourceNotFoundException":
        self.log(f"❌ Event-Checker Lambda Function missing: {function_name}")
      else:
        raise
