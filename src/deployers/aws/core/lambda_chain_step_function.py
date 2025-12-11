from deployers.base import Deployer
import json
import time
import globals
import util
from botocore.exceptions import ClientError

class LambdaChainStepFunctionDeployer(Deployer):
  def log(self, message):
    print(f"Core: {message}")

  def deploy(self):
    sf_name = globals.lambda_chain_step_function_name()
    role_name = globals.lambda_chain_iam_role_name()

    response = globals.aws_iam_client.get_role(RoleName=role_name)
    role_arn = response["Role"]["Arn"]

    globals.aws_sf_client.create_state_machine(
      name=sf_name,
      roleArn=role_arn,
      definition=json.dumps({
        "Comment": "Executing two lambda functions consecutive",
        "StartAt": "LambdaA",
        "States": {
          "LambdaA": {
            "Type": "Task",
            "Resource": "arn:aws:states:::lambda:invoke",
            "Parameters": {
              "FunctionName.$": "$.LambdaAArn",
              "Payload.$": "$.InputData"
            },
            "ResultPath": "$.LambdaAResult",
            "Next": "LambdaB"
          },
          "LambdaB": {
            "Type": "Task",
            "Resource": "arn:aws:states:::lambda:invoke",
            "Parameters": {
              "FunctionName.$": "$.LambdaBArn",
              "Payload": {
                "fromA.$": "$.LambdaAResult.Payload",
                "event.$": "$.InputData"
              }
            },
            "OutputPath": "$.Payload",
            "End": True
          }
        }
      })
    )

    self.log(f"Created Step Function: {sf_name}")

  def destroy(self):
    sf_name = globals.lambda_chain_step_function_name()
    region = globals.aws_lambda_client.meta.region_name
    account_id = globals.aws_sts_client.get_caller_identity()['Account']
    sf_arn = f"arn:aws:states:{region}:{account_id}:stateMachine:{sf_name}"

    try:
      globals.aws_sf_client.describe_state_machine(stateMachineArn=sf_arn)
    except ClientError as e:
      if e.response["Error"]["Code"] == "StateMachineDoesNotExist":
        return

    globals.aws_sf_client.delete_state_machine(stateMachineArn=sf_arn)
    self.log(f"Deletion of Step Function initiated: {sf_name}")

    while True:
      try:
        globals.aws_sf_client.describe_state_machine(stateMachineArn=sf_arn)
        time.sleep(2)
      except ClientError as e:
        if e.response["Error"]["Code"] == "StateMachineDoesNotExist":
          break
        else:
          raise

    self.log(f"Deleted Step Function: {sf_name}")

  def info(self):
    sf_name = globals.lambda_chain_step_function_name()
    region = globals.aws_lambda_client.meta.region_name
    account_id = globals.aws_sts_client.get_caller_identity()['Account']
    sf_arn = f"arn:aws:states:{region}:{account_id}:stateMachine:{sf_name}"

    try:
      globals.aws_sf_client.describe_state_machine(stateMachineArn=sf_arn)
      self.log(f"✅ Lambda-Chain Step Function exists: {util.link_to_step_function(sf_arn)}")
    except ClientError as e:
      if e.response["Error"]["Code"] == "StateMachineDoesNotExist":
        self.log(f"❌ Lambda-Chain Step Function missing: {sf_name}")
      else:
        raise
