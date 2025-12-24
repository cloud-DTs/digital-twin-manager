from deployers.aws.iot.processor_iam_role import ProcessorIamRoleDeployer
from deployers.aws.iot.processor_lambda_function import ProcessorLambdaFunctionDeployer
from deployers.base import Deployer
import globals

class L2Deployer(Deployer):
  def log(self, message):
    print(f"IoT: {message}")

  def deploy(self):
    for iot_device in globals.config_iot_devices:
      ProcessorIamRoleDeployer().deploy(iot_device)
      ProcessorLambdaFunctionDeployer().deploy(iot_device)

  def destroy(self):
    for iot_device in globals.config_iot_devices:
      ProcessorLambdaFunctionDeployer().destroy(iot_device)
      ProcessorIamRoleDeployer().destroy(iot_device)

  def info(self):
    for iot_device in globals.config_iot_devices:
      ProcessorIamRoleDeployer().info(iot_device)
      ProcessorLambdaFunctionDeployer().info(iot_device)
