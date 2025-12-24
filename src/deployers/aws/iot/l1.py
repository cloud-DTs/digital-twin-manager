from deployers.aws.iot.iot_thing import IotThingDeployer
from deployers.base import Deployer
import globals

class L1Deployer(Deployer):
  def log(self, message):
    print(f"IoT: {message}")

  def deploy(self):
    for iot_device in globals.config_iot_devices:
      IotThingDeployer().deploy(iot_device)

  def destroy(self):
    for iot_device in globals.config_iot_devices:
      IotThingDeployer().destroy(iot_device)

  def info(self):
    for iot_device in globals.config_iot_devices:
      IotThingDeployer().info(iot_device)
