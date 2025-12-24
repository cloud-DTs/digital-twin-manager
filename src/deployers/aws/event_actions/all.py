from deployers.aws.event_actions.lambda_actions import LambdaActionsDeployer
from deployers.base import Deployer

class AllDeployer(Deployer):
  def log(self, message):
    print(f"Event Actions: {message}")

  def deploy(self):
    LambdaActionsDeployer().deploy()

  def destroy(self):
    LambdaActionsDeployer().destroy()

  def info(self):
    LambdaActionsDeployer().info()
