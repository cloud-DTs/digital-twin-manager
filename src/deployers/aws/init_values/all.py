from deployers.aws.init_values.init_values import InitValuesDeployer
from deployers.base import Deployer

class AllDeployer(Deployer):
  def log(self, message):
    print(f"Init Values: {message}")

  def deploy(self):
    InitValuesDeployer().deploy()

  def destroy(self):
    InitValuesDeployer().destroy()

  def info(self):
    InitValuesDeployer().info()
