from deployers.aws.iot.l1 import L1Deployer
from deployers.aws.iot.l2 import L2Deployer
from deployers.aws.iot.l4 import L4Deployer
from deployers.base import Deployer

class AllDeployer(Deployer):
  def log(self, message):
    print(f"IoT: {message}")

  def deploy(self):
    L1Deployer().deploy()
    L2Deployer().deploy()
    L4Deployer().deploy()

  def destroy(self):
    L4Deployer().destroy()
    L2Deployer().destroy()
    L1Deployer().destroy()

  def info(self):
    L1Deployer().info()
    L2Deployer().info()
    L4Deployer().info()
