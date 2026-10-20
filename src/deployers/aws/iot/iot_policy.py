import json

from botocore.exceptions import ClientError

import deployment_state
import globals
from dependency_graph import plan_graph_ids
from deployers.aws.apply_actions import ACTION_DEPLOY, ACTION_DESTROY
from deployers.aws.core.plan_actions import plan_action
from deployers.base import Deployer


class IotPolicyDeployer(Deployer):
  POLICY_DOCUMENT = {
    "Version": "2012-10-17",
    "Statement": [{"Effect": "Allow", "Action": ["iot:*"], "Resource": "*"}],
  }

  def log(self, message):
    print(f"IoT: {message}")

  def _policy(self, policy_name):
    try:
      return globals.aws_iot_client.get_policy(policyName=policy_name)
    except ClientError as error:
      if error.response["Error"]["Code"] != "ResourceNotFoundException":
        raise
      return None

  def exists(self, policy_name):
    return self._policy(policy_name) is not None

  def _targets(self, policy_name):
    request = {"policyName": policy_name, "pageSize": 1}
    while True:
      response = globals.aws_iot_client.list_targets_for_policy(**request)
      yield from response.get("targets", [])
      if not response.get("nextMarker"):
        return
      request["marker"] = response["nextMarker"]

  def needs_cleanup(self, policy_name):
    """Return whether an existing legacy policy has no attached targets."""
    try:
      return next(self._targets(policy_name), None) is None
    except ClientError as error:
      if error.response["Error"]["Code"] != "ResourceNotFoundException":
        raise
      return False

  def _validate_policy(self, policy_name, policy):
    if policy is None or json.loads(policy["policyDocument"]) != self.POLICY_DOCUMENT:
      raise ValueError(f"Existing IoT policy {policy_name} does not match the twin policy.")

  def plan(self):
    previous_name = deployment_state.last_applied_iot_policy_name()
    desired_name = globals.iot_policy_name()
    desired_policy = self._policy(desired_name)
    if desired_policy is not None:
      self._validate_policy(desired_name, desired_policy)
    actions = []
    if previous_name != desired_name:
      actions.append(plan_action(
        previous_name, "iot_policy", action=ACTION_DESTROY, graph_id=plan_graph_ids.IOT_POLICY,
      ))
    actions.append(plan_action(
      desired_name, "iot_policy", action="NO_CHANGE" if desired_policy is not None else ACTION_DEPLOY,
      graph_id=plan_graph_ids.IOT_POLICY,
    ))
    return actions

  def deploy(self, policy_name=None):
    policy_name = policy_name or globals.iot_policy_name()
    policy = self._policy(policy_name)
    if policy is not None:
      self._validate_policy(policy_name, policy)
      return
    try:
      globals.aws_iot_client.create_policy(
        policyName=policy_name, policyDocument=json.dumps(self.POLICY_DOCUMENT),
      )
      self.log(f"Created shared IoT Policy: {policy_name}")
    except ClientError as error:
      if error.response["Error"]["Code"] != "ResourceAlreadyExistsException":
        raise
      self._validate_policy(policy_name, self._policy(policy_name))

  def destroy(self, policy_name=None, *, only_if_unused=False, detached_targets=()):
    policy_name = policy_name or globals.iot_policy_name()
    detached_targets = set(detached_targets)
    pending_detach = False
    try:
      for target in self._targets(policy_name):
        if target not in detached_targets:
          if only_if_unused:
            self.log(f"Retained IoT Policy still in use: {policy_name}")
            return False
          raise ValueError(f"IoT policy {policy_name} still has attached targets.")
        pending_detach = True
      if pending_detach:
        raise RuntimeError(f"IoT policy {policy_name} still lists recently detached targets. Retry after AWS completes detachment.")
      versions = globals.aws_iot_client.list_policy_versions(policyName=policy_name)
      for version in versions.get("policyVersions", []):
        if not version["isDefaultVersion"]:
          try:
            globals.aws_iot_client.delete_policy_version(
              policyName=policy_name, policyVersionId=version["versionId"],
            )
          except ClientError as error:
            if error.response["Error"]["Code"] != "ResourceNotFoundException":
              raise
      globals.aws_iot_client.delete_policy(policyName=policy_name)
      self.log(f"Deleted IoT Policy: {policy_name}")
    except ClientError as error:
      code = error.response["Error"]["Code"]
      if code != "ResourceNotFoundException":
        raise
    return True

  def info(self):
    policy_name = globals.iot_policy_name()
    status = "exists" if self.exists(policy_name) else "missing"
    self.log(f"Shared IoT Policy {policy_name}: {status}")

  def apply(self, action, resource):
    if action["action"] == ACTION_DEPLOY:
      self.deploy(resource)
    elif action["action"] == ACTION_DESTROY:
      self.destroy(resource)
    else:
      raise ValueError(f"Unsupported IoT policy action: {action['action']}")
