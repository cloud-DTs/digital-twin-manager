from deployers.aws.core.l1 import L1Deployer
from deployers.aws.core.l2 import L2Deployer
from deployers.aws.core.l3_archive import L3ArchiveDeployer
from deployers.aws.core.l3_cold import L3ColdDeployer
from deployers.aws.core.l3_hot import L3HotDeployer
from deployers.aws.core.l4 import L4Deployer
from deployers.aws.core.l5 import L5Deployer
from deployers.base import Deployer

class AllDeployer(Deployer):
  def log(self, message):
    print(message)

  def deploy(self):
    L1Deployer().deploy()
    L2Deployer().deploy()
    L3HotDeployer().deploy()
    L3ColdDeployer().deploy()
    L3ArchiveDeployer().deploy()
    L4Deployer().deploy()
    # L5Deployer().deploy()

  def destroy(self):
    # L5Deployer().destroy()
    L4Deployer().destroy()
    L3ArchiveDeployer().destroy()
    L3ColdDeployer().destroy()
    L3HotDeployer().destroy()
    L2Deployer().destroy()
    L1Deployer().destroy()

  def info(self):
    L1Deployer().info()
    L2Deployer().info()
    L3HotDeployer().info()
    L3ColdDeployer().info()
    L3ArchiveDeployer().info()
    L4Deployer().info()
    L5Deployer().info()
