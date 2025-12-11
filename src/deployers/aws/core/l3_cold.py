from deployers.aws.core.cold_archive_mover_event_rule import ColdArchiveMoverEventRuleDeployer
from deployers.aws.core.cold_archive_mover_iam_role import ColdArchiveMoverIamRoleDeployer
from deployers.aws.core.cold_archive_mover_lambda_function import ColdArchiveMoverLambdaFunctionDeployer
from deployers.aws.core.cold_s3_bucket import ColdS3BucketDeployer
from deployers.base import Deployer

class L3ColdDeployer(Deployer):
  def log(self, message):
    print(message)

  def deploy(self):
    ColdS3BucketDeployer().deploy()
    ColdArchiveMoverIamRoleDeployer().deploy()
    ColdArchiveMoverLambdaFunctionDeployer().deploy()
    ColdArchiveMoverEventRuleDeployer().deploy()

  def destroy(self):
    ColdArchiveMoverEventRuleDeployer().destroy()
    ColdArchiveMoverLambdaFunctionDeployer().destroy()
    ColdArchiveMoverIamRoleDeployer().destroy()
    ColdS3BucketDeployer().destroy()

  def info(self):
    ColdS3BucketDeployer().info()
    ColdArchiveMoverIamRoleDeployer().info()
    ColdArchiveMoverLambdaFunctionDeployer().info()
    ColdArchiveMoverEventRuleDeployer().info()
