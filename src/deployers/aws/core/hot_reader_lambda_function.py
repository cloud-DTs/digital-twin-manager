import deployment_state
from deployers.aws.apply_actions import ACTION_DESTROY, ACTION_DEPLOY
from deployers.aws.core.plan_actions import plan_action
from deployers.base import Deployer
from dependency_graph import plan_graph_ids
import os
import globals
import util
from botocore.exceptions import ClientError

class HotReaderLambdaFunctionDeployer(Deployer):
  def log(self, message):
    print(f"Core: {message}")

  def plan(self):
    previous_function_name = deployment_state.last_applied_hot_reader_lambda_function_name()
    desired_function_name = globals.hot_reader_lambda_function_name()

    if previous_function_name == desired_function_name:
      self.log(f"Hot Reader Lambda Function {desired_function_name} is up to date.")
      return [
        plan_action(
          desired_function_name,
          "lambda_function",
          graph_id=plan_graph_ids.HOT_READER_LAMBDA,
        )
      ]

    self.log(f"Hot Reader Lambda Function name changed from {previous_function_name} to {desired_function_name}.")
    return [
      plan_action(
        previous_function_name,
        "lambda_function",
        action="DESTROY",
        graph_id=plan_graph_ids.HOT_READER_LAMBDA,
      ),
      plan_action(
        desired_function_name,
        "lambda_function",
        action="DEPLOY",
        graph_id=plan_graph_ids.HOT_READER_LAMBDA,
      ),
    ]

  def deploy(self, function_name=None, role_name=None):
    function_name = function_name or globals.hot_reader_lambda_function_name()
    role_name = role_name or globals.hot_reader_iam_role_name()

    response = globals.aws_iam_client.get_role(RoleName=role_name)
    role_arn = response["Role"]["Arn"]

    globals.aws_lambda_client.create_function(
      FunctionName=function_name,
      Runtime="python3.13",
      Role=role_arn,
      Handler="lambda_function.lambda_handler", #  file.function
      Code={"ZipFile": util.compile_lambda_function(os.path.join(globals.core_lfs_path, "hot-reader"))},
      Description="",
      Timeout=900, # seconds
      MemorySize=128, # MB
      Publish=True,
      Environment=util.lambda_environment({
        "DIGITAL_TWIN_NAME": globals.config["digital_twin_name"],
        "DYNAMODB_TABLE_NAME": globals.hot_dynamodb_table_name()
      })
    )

    self.log(f"Created Lambda function: {function_name}")
    globals.aws_lambda_client.add_permission(
      FunctionName=function_name,
      StatementId="AllowTwinmakerInvoke",
      Action="lambda:InvokeFunction",
      Principal="iottwinmaker.amazonaws.com",
      # Without this, TwinMaker workspaces in any AWS account could invoke the function.
      SourceAccount=globals.aws_sts_client.get_caller_identity()["Account"]
    )

  def destroy(self, function_name=None):
    function_name = function_name or globals.hot_reader_lambda_function_name()

    try:
      globals.aws_lambda_client.delete_function(FunctionName=function_name)
      self.log(f"Deleted Lambda function: {function_name}")
    except ClientError as e:
      if e.response["Error"]["Code"] != "ResourceNotFoundException":
        raise

  def info(self):
    function_name = globals.hot_reader_lambda_function_name()

    try:
      globals.aws_lambda_client.get_function(FunctionName=function_name)
      self.log(f"✅ Hot Reader Lambda Function exists: {util.link_to_lambda_function(function_name)}")
    except ClientError as e:
      if e.response["Error"]["Code"] == "ResourceNotFoundException":
        self.log(f"❌ Hot Reader Lambda Function missing: {function_name}")
      else:
        raise

  def apply(self, action, resource):
    if action["action"] == ACTION_DESTROY:
      self.destroy(resource)
    elif action["action"] == ACTION_DEPLOY:
      self.deploy(resource)
    else:
      raise ValueError(f"Unsupported core_l3_hot action: {action['action']}")
