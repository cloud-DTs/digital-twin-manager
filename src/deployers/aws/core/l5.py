from deployers.aws.core.grafana_iam_role import GrafanaIamRoleDeployer
from deployers.aws.core.grafana_workspace import GrafanaWorkspaceDeployer
from deployers.base import Deployer

class L5Deployer(Deployer):
  def log(self, message):
    print(message)

  def deploy(self):
    GrafanaIamRoleDeployer().deploy()
    GrafanaWorkspaceDeployer().deploy()

  def destroy(self):
    GrafanaWorkspaceDeployer().destroy()
    GrafanaIamRoleDeployer().destroy()

  def info(self):
    GrafanaIamRoleDeployer().info()
    GrafanaWorkspaceDeployer().info()
