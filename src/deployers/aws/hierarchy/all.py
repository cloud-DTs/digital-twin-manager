from deployers.aws.hierarchy.twinmaker_hierarchy import TwinmakerHierarchyDeployer
from deployers.base import Deployer

class AllDeployer(Deployer):
  def log(self, message):
    print(f"Hierarchy: {message}")

  def deploy(self):
    TwinmakerHierarchyDeployer().deploy()

  def destroy(self):
    TwinmakerHierarchyDeployer().destroy()

  def info(self):
    TwinmakerHierarchyDeployer().info()
