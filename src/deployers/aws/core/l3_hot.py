from deployers.aws.core.hot_cold_mover_event_rule import HotColdMoverEventRuleDeployer
from deployers.aws.core.hot_cold_mover_iam_role import HotColdMoverIamRoleDeployer
from deployers.aws.core.hot_cold_mover_lambda_function import HotColdMoverLambdaFunctionDeployer
from deployers.aws.core.hot_dynamodb_table import HotDynamodbTableDeployer
from deployers.aws.core.hot_reader_iam_role import HotReaderIamRoleDeployer
from deployers.aws.core.hot_reader_lambda_function import HotReaderLambdaFunctionDeployer
from deployers.base import Deployer

class L3HotDeployer(Deployer):
  def log(self, message):
    print(message)

  def deploy(self):
    HotDynamodbTableDeployer().deploy()
    HotColdMoverIamRoleDeployer().deploy()
    HotColdMoverLambdaFunctionDeployer().deploy()
    HotColdMoverEventRuleDeployer().deploy()
    HotReaderIamRoleDeployer().deploy()
    HotReaderLambdaFunctionDeployer().deploy()

  def destroy(self):
    HotReaderLambdaFunctionDeployer().destroy()
    HotReaderIamRoleDeployer().destroy()
    HotColdMoverEventRuleDeployer().destroy()
    HotColdMoverLambdaFunctionDeployer().destroy()
    HotColdMoverIamRoleDeployer().destroy()
    HotDynamodbTableDeployer().destroy()

  def info(self):
    HotDynamodbTableDeployer().info()
    HotColdMoverIamRoleDeployer().info()
    HotColdMoverLambdaFunctionDeployer().info()
    HotColdMoverEventRuleDeployer().info()
    HotReaderIamRoleDeployer().info()
    HotReaderLambdaFunctionDeployer().info()
