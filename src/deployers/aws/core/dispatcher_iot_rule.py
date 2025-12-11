from deployers.base import Deployer
import globals
import util
from botocore.exceptions import ClientError

class DispatcherIotRuleDeployer(Deployer):
  def log(self, message):
    print(f"Core: {message}")

  def deploy(self):
    rule_name = globals.dispatcher_iot_rule_name()
    topic = globals.dispatcher_iot_rule_topic()
    sql = f"SELECT * FROM '{topic}'"

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

    self.log(f"Created IoT rule: {rule_name}")

    region = globals.aws_iot_client.meta.region_name
    account_id = globals.aws_sts_client.get_caller_identity()['Account']

    globals.aws_lambda_client.add_permission(
      FunctionName=function_name,
      StatementId="iot-invoke",
      Action="lambda:InvokeFunction",
      Principal="iot.amazonaws.com",
      SourceArn=f"arn:aws:iot:{region}:{account_id}:rule/{rule_name}"
    )

    self.log(f"Added permission to Lambda function so the rule can invoke the function.")

  def destroy(self):
    function_name = globals.dispatcher_lambda_function_name()
    rule_name = globals.dispatcher_iot_rule_name()

    try:
      globals.aws_lambda_client.remove_permission(
          FunctionName=function_name,
          StatementId="iot-invoke"
      )
      self.log(f"Removed permission from Lambda function: {rule_name}, {function_name}")
    except globals.aws_lambda_client.exceptions.ResourceNotFoundException:
      pass

    if util.iot_rule_exists(rule_name):
      try:
        globals.aws_iot_client.delete_topic_rule(ruleName=rule_name)
        self.log(f"Deleted IoT Rule: {rule_name}")
      except globals.aws_iot_client.exceptions.ResourceNotFoundException:
        pass

  def info(self):
    rule_name = globals.dispatcher_iot_rule_name()

    try:
      globals.aws_iot_client.get_topic_rule(ruleName=rule_name)
      self.log(f"✅ Dispatcher Iot Rule exists: {util.link_to_iot_rule(rule_name)}")
    except ClientError as e:
      if e.response["Error"]["Code"] == "UnauthorizedException":
        self.log(f"❌ Dispatcher IoT Rule missing: {rule_name}")
      else:
        raise
