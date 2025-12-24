from deployers.base import Deployer
import json
import time
import globals
import util
from botocore.exceptions import ClientError

class GrafanaWorkspaceDeployer(Deployer):
  def log(self, message):
    print(f"Core: {message}")

  def deploy(self):
    workspace_name = globals.grafana_workspace_name()
    role_name = globals.grafana_iam_role_name()

    response = globals.aws_iam_client.get_role(RoleName=role_name)
    role_arn = response["Role"]["Arn"]

    response = globals.aws_grafana_client.create_workspace(
      workspaceName=workspace_name,
      workspaceDescription="",
      grafanaVersion="10.4",
      accountAccessType="CURRENT_ACCOUNT",
      authenticationProviders=["AWS_SSO"],
      permissionType="CUSTOMER_MANAGED",
      workspaceRoleArn=role_arn,
      configuration=json.dumps(
        {
          "plugins": {
            "pluginAdminEnabled": True
          },
          # "unifiedAlerting": {
          #   "enabled": True
          # }
        }
      ),
      tags={
          "Environment": "Dev"
      }
    )
    workspace_id = response["workspace"]["id"]

    self.log(f"Creation of Grafana workspace initiated: {workspace_name}")

    while True:
      response = globals.aws_grafana_client.describe_workspace(workspaceId=workspace_id)
      if response["workspace"]["status"] == "ACTIVE":
        break
      time.sleep(2)

    self.log(f"Created Grafana workspace: {workspace_name}")
    self.log(f"Grafana login: https://{response["workspace"]["endpoint"]}")

  def destroy(self):
    workspace_name = globals.grafana_workspace_name()

    try:
      workspace_id = util.get_grafana_workspace_id_by_name(workspace_name)
      globals.aws_grafana_client.delete_workspace(workspaceId=workspace_id)
    except ClientError as e:
      if e.response["Error"]["Code"] == "ResourceNotFoundException":
        return
      else:
        raise

    self.log(f"Deletion of Grafana workspace initiated: {workspace_name}")

    while True:
      try:
        globals.aws_grafana_client.describe_workspace(workspaceId=workspace_id)
        time.sleep(2)
      except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
          break
        else:
          raise

    self.log(f"Deleted Grafana workspace: {workspace_name}")

  def info(self):
    workspace_name = globals.grafana_workspace_name()

    try:
      workspace_id = util.get_grafana_workspace_id_by_name(workspace_name)
      response = globals.aws_grafana_client.describe_workspace(workspaceId=workspace_id)
      self.log(f"✅ Grafana Workspace exists: {util.link_to_grafana_workspace(workspace_id)}")
      self.log(f"Grafana login: https://{response["workspace"]["endpoint"]}")
    except ClientError as e:
      if e.response["Error"]["Code"] == "ResourceNotFoundException":
        self.log(f"❌ Grafana Workspace missing: {workspace_name}")
      else:
        raise
