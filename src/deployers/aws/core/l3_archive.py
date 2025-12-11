from deployers.aws.core.archive_s3_bucket import ArchiveS3BucketDeployer
from deployers.base import Deployer

class L3ArchiveDeployer(Deployer):
  def log(self, message):
    print(message)

  def deploy(self):
    ArchiveS3BucketDeployer().deploy()

  def destroy(self):
    ArchiveS3BucketDeployer().destroy()

  def info(self):
    ArchiveS3BucketDeployer().info()
