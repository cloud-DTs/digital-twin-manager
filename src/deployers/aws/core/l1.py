from deployers.aws.core.dispatcher_iam_role import DispatcherIamRoleDeployer
from deployers.aws.core.dispatcher_iot_rule import DispatcherIotRuleDeployer
from deployers.aws.core.dispatcher_lambda_function import DispatcherLambdaFunctionDeployer
from deployers.base import Deployer

class L1Deployer(Deployer):
  def log(self, message):
    print(message)

  def deploy(self):
    DispatcherIamRoleDeployer().deploy()
    DispatcherLambdaFunctionDeployer().deploy()
    DispatcherIotRuleDeployer().deploy()

  def destroy(self):
    DispatcherIotRuleDeployer().destroy()
    DispatcherLambdaFunctionDeployer().destroy()
    DispatcherIamRoleDeployer().destroy()

  def info(self):
    DispatcherIamRoleDeployer().info()
    DispatcherLambdaFunctionDeployer().info()
    DispatcherIotRuleDeployer().info()
