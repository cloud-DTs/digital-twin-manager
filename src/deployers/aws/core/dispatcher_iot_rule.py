from deployers.aws.apply_actions import ACTION_DESTROY, ACTION_DEPLOY
from deployers.base import Deployer
from deployers.aws.core.aws_arns import iot_rule_arn, lambda_function_arn
from deployers.aws.core.lambda_permission import LambdaPermissionPlanner
from deployers.aws.core.plan_actions import plan_action
from dependency_graph import plan_graph_ids
import globals
import deployment_state
import util
from botocore.exceptions import ClientError

class DispatcherIotRuleDeployer(Deployer):
  LAMBDA_PERMISSION_STATEMENT_ID = "iot-invoke"

  def log(self, message):
    print(f"Core: {message}")

  def _topic_rule(self, rule_name):
    try:
      response = globals.aws_iot_client.get_topic_rule(ruleName=rule_name)
      return response["rule"]
    except ClientError as e:
      if e.response["Error"]["Code"] in ["ResourceNotFoundException", "UnauthorizedException"]:
        return None
      raise

  def _actions(self, function_name):
    return [
      {
        "lambda": {
          "functionArn": lambda_function_arn(function_name)
        }
      }
    ]

  def _drifted_fields(self, topic_rule, expected_topic, expected_function_name):
    expected_sql = f"SELECT *, timestamp() AS iotRuleTs FROM '{expected_topic}'"
    expected_actions = self._actions(expected_function_name)
    drifted_fields = []

    if topic_rule.get("sql") != expected_sql:
      drifted_fields.append("sql")

    if topic_rule.get("ruleDisabled") is not False:
      drifted_fields.append("ruleDisabled")

    if topic_rule.get("actions", []) != expected_actions:
      drifted_fields.append("actions")

    return drifted_fields

  def _lambda_permission_plan(
    self,
    previous_rule_name,
    desired_rule_name,
    previous_function_name,
    desired_function_name
  ):
    previous_source_arn = None
    if previous_rule_name:
      previous_source_arn = iot_rule_arn(previous_rule_name)

    return LambdaPermissionPlanner(
      resource="dispatcher_iot_rule_lambda_permission",
      parent_resource="dispatcher_iot_rule",
      graph_id=plan_graph_ids.DISPATCHER_IOT_RULE_LAMBDA_PERMISSION,
      label="Dispatcher IoT Rule Lambda permission",
      statement_id=self.LAMBDA_PERMISSION_STATEMENT_ID,
      principal_service="iot.amazonaws.com",
      action="lambda:InvokeFunction",
      log=self.log
    ).plan(
      previous_function_name,
      desired_function_name,
      previous_source_arn,
      iot_rule_arn(desired_rule_name)
    )

  def plan(self):
    previous_rule_name = deployment_state.last_applied_dispatcher_iot_rule_name()
    desired_rule_name = globals.dispatcher_iot_rule_name()
    previous_topic = deployment_state.last_applied_dispatcher_iot_rule_topic()
    desired_topic = globals.dispatcher_iot_rule_topic()
    previous_function_name = deployment_state.last_applied_dispatcher_lambda_function_name()
    desired_function_name = globals.dispatcher_lambda_function_name()

    if (
            previous_topic != desired_topic
            or previous_function_name != desired_function_name
            or previous_rule_name != desired_rule_name
    ):
      self.log("Dispatcher IoT Rule configuration drift detected.")

      if previous_topic != desired_topic:
        self.log(
          f"Topic changed: previous_topic={previous_topic}, "
          f"desired_topic={desired_topic}."
        )

      if previous_function_name != desired_function_name:
        self.log(
          f"Lambda target changed: previous_function_name={previous_function_name}, "
          f"desired_function_name={desired_function_name}."
        )

      if previous_rule_name != desired_rule_name:
        self.log(
          f"Rule name changed: previous_rule_name={previous_rule_name}, "
          f"desired_rule_name={desired_rule_name}."
        )

      return [
        plan_action(
          previous_rule_name,
          "iot_rule",
          action="DESTROY",
          graph_id=plan_graph_ids.DISPATCHER_IOT_RULE,
        ),
        plan_action(
          desired_rule_name,
          "iot_rule",
          action="DEPLOY",
          graph_id=plan_graph_ids.DISPATCHER_IOT_RULE,
        ),
      ]

    self.log(f"Dispatcher IoT Rule is up to date.")
    return [
      plan_action(
        desired_rule_name,
        "iot_rule",
        graph_id=plan_graph_ids.DISPATCHER_IOT_RULE,
      )
    ]

  def deploy(self, rule_name=None, topic=None, function_name=None):
    rule_name = rule_name or globals.dispatcher_iot_rule_name()
    topic = topic or globals.dispatcher_iot_rule_topic()
    sql = f"SELECT *, timestamp() AS iotRuleTs FROM '{topic}'"

    function_name = function_name or globals.dispatcher_lambda_function_name()

    globals.aws_iot_client.create_topic_rule(
      ruleName=rule_name,
      topicRulePayload={
        "sql": sql,
        "description": "",
        "actions": self._actions(function_name),
        "ruleDisabled": False
      }
    )

    self.log(f"Created IoT rule: {rule_name}")

    globals.aws_lambda_client.add_permission(
      FunctionName=function_name,
      StatementId=self.LAMBDA_PERMISSION_STATEMENT_ID,
      Action="lambda:InvokeFunction",
      Principal="iot.amazonaws.com",
      SourceArn=iot_rule_arn(rule_name)
    )

    self.log(f"Added permission to Lambda function so the rule can invoke the function.")

  def destroy(self, rule_name=None, function_name=None):
    function_name = function_name or globals.dispatcher_lambda_function_name()
    rule_name = rule_name or globals.dispatcher_iot_rule_name()

    try:
      globals.aws_lambda_client.remove_permission(
          FunctionName=function_name,
          StatementId=self.LAMBDA_PERMISSION_STATEMENT_ID
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

  def apply(self, action, resource):
    if action["action"] == ACTION_DESTROY:
      self.destroy(
        rule_name=resource,
        function_name=deployment_state.last_applied_dispatcher_lambda_function_name(),
      )
    elif action["action"] == ACTION_DEPLOY:
      self.deploy(resource)
    else:
      raise ValueError(f"Unsupported core_l1 action: {action['action']}")
