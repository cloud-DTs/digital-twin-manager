from deployers.aws.core.event_checker_iam_role import EventCheckerIamRoleDeployer
from deployers.aws.core.event_checker_lambda_function import EventCheckerLambdaFunctionDeployer
from deployers.aws.core.event_feedback_iam_role import EventFeedbackIamRoleDeployer
from deployers.aws.core.event_feedback_lambda_function import EventFeedbackLambdaFunctionDeployer
from deployers.aws.core.lambda_chain_iam_role import LambdaChainIamRoleDeployer
from deployers.aws.core.lambda_chain_step_function import LambdaChainStepFunctionDeployer
from deployers.aws.core.persister_iam_role import PersisterIamRoleDeployer
from deployers.aws.core.persister_lambda_function import PersisterLambdaFunctionDeployer
from deployers.base import Deployer

class L2Deployer(Deployer):
  def log(self, message):
    print(message)

  def deploy(self):
    PersisterIamRoleDeployer().deploy()
    PersisterLambdaFunctionDeployer().deploy()
    EventFeedbackIamRoleDeployer().deploy()
    EventFeedbackLambdaFunctionDeployer().deploy()
    EventCheckerIamRoleDeployer().deploy()
    EventCheckerLambdaFunctionDeployer().deploy()
    LambdaChainIamRoleDeployer().deploy()
    LambdaChainStepFunctionDeployer().deploy()

  def destroy(self):
    LambdaChainStepFunctionDeployer().destroy()
    LambdaChainIamRoleDeployer().destroy()
    EventCheckerLambdaFunctionDeployer().destroy()
    EventCheckerIamRoleDeployer().destroy()
    EventFeedbackLambdaFunctionDeployer().destroy()
    EventFeedbackIamRoleDeployer().destroy()
    PersisterLambdaFunctionDeployer().destroy()
    PersisterIamRoleDeployer().destroy()

  def info(self):
    PersisterIamRoleDeployer().info()
    PersisterLambdaFunctionDeployer().info()
    EventFeedbackIamRoleDeployer().info()
    EventFeedbackLambdaFunctionDeployer().info()
    EventCheckerIamRoleDeployer().info()
    EventCheckerLambdaFunctionDeployer().info()
    LambdaChainIamRoleDeployer().info()
    LambdaChainStepFunctionDeployer().info()
