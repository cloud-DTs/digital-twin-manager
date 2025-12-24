from deployers.aws.iot.twinmaker_component_type import TwinmakerComponentTypeDeployer
from deployers.base import Deployer
import globals

class L4Deployer(Deployer):
  def log(self, message):
    print(f"IoT: {message}")

  def deploy(self):
    for iot_device in globals.config_iot_devices:
      TwinmakerComponentTypeDeployer().deploy(iot_device)

  def destroy(self):
    for iot_device in globals.config_iot_devices:
      TwinmakerComponentTypeDeployer().destroy(iot_device)

  def info(self):
    for iot_device in globals.config_iot_devices:
      TwinmakerComponentTypeDeployer().info(iot_device)
