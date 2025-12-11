from deployers.aws.core.twinmaker_iam_role import TwinmakerIamRoleDeployer
from deployers.aws.core.twinmaker_s3_bucket import TwinmakerS3BucketDeployer
from deployers.aws.core.twinmaker_workspace import TwinmakerWorkspaceDeployer
from deployers.base import Deployer

class L4Deployer(Deployer):
  def log(self, message):
    print(message)

  def deploy(self):
    TwinmakerS3BucketDeployer().deploy()
    TwinmakerIamRoleDeployer().deploy()
    TwinmakerWorkspaceDeployer().deploy()

  def destroy(self):
    TwinmakerWorkspaceDeployer().destroy()
    TwinmakerIamRoleDeployer().destroy()
    TwinmakerS3BucketDeployer().destroy()

  def info(self):
    TwinmakerS3BucketDeployer().info()
    TwinmakerIamRoleDeployer().info()
    TwinmakerWorkspaceDeployer().info()
