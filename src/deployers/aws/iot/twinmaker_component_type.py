from deployers.base import Deployer
import globals
from botocore.exceptions import ClientError
import time
import util

class TwinmakerComponentTypeDeployer(Deployer):
  def log(self, message):
    print(f"IoT: {message}")

  def deploy(self, iot_device):
    connector_function_name = globals.hot_reader_lambda_function_name()
    workspace_name = globals.twinmaker_workspace_name()
    component_type_id = globals.twinmaker_component_type_id(iot_device)

    response = globals.aws_lambda_client.get_function(FunctionName=connector_function_name)
    connector_function_arn = response["Configuration"]["FunctionArn"]

    property_definitions = {}

    if "properties" in iot_device:
      for property in iot_device["properties"]:
        property_definitions[property["name"]] = {
          "dataType": {
            "type": property["dataType"]
          },
          "isTimeSeries": True,
          "isStoredExternally": True
        }

    functions = {}

    functions = {
      "dataReader": {
        "implementedBy": {
          "lambda": {
            "arn": connector_function_arn
          }
        }
      }
    }

    globals.aws_twinmaker_client.create_component_type(
      workspaceId=workspace_name,
      componentTypeId=component_type_id,
      propertyDefinitions=property_definitions,
      functions=functions
    )

    self.log(f"Creation of IoT Twinmaker Component Type initiated: {component_type_id}")

    while True:
      response = globals.aws_twinmaker_client.get_component_type(workspaceId=workspace_name, componentTypeId=component_type_id)
      if response["status"]["state"] == "ACTIVE":
        break
      time.sleep(2)

    self.log(f"Created IoT Twinmaker Component Type: {component_type_id}")

  def destroy(self, iot_device):
    workspace_name = globals.twinmaker_workspace_name()
    component_type_id = globals.twinmaker_component_type_id(iot_device)

    try:
      globals.aws_twinmaker_client.get_component_type(workspaceId=workspace_name, componentTypeId=component_type_id)
    except ClientError as e:
      if e.response['Error']['Code'] == 'ResourceNotFoundException':
        return

    try:
      response = globals.aws_twinmaker_client.list_entities(workspaceId=workspace_name)

      for entity in response.get("entitySummaries", []):
        entity_details = globals.aws_twinmaker_client.get_entity(workspaceId=workspace_name, entityId=entity["entityId"])
        components = entity_details.get("components", {})
        component_updates = {}

        for comp_name, comp in components.items():
          if comp.get("componentTypeId") == component_type_id:
            component_updates[comp_name] = {"updateType": "DELETE"}

        if component_updates:
          globals.aws_twinmaker_client.update_entity(workspaceId=workspace_name, entityId=entity["entityId"], componentUpdates=component_updates)
          self.log("Deletion of components initiated.")

          while True:
            entity_details_2 = globals.aws_twinmaker_client.get_entity(workspaceId=workspace_name, entityId=entity["entityId"])
            components_2 = entity_details_2.get("components", {})

            if not set(component_updates.keys()) & set(components_2.keys()):
              self.log(f"Deleted components.")
              break
            else:
              time.sleep(2)

    except ClientError as e:
      if e.response["Error"]["Code"] != "ValidationException":
        raise

    self.log(f"Deleted all IoT Twinmaker Components with component type id: {component_type_id}")

    globals.aws_twinmaker_client.delete_component_type(workspaceId=workspace_name, componentTypeId=component_type_id)

    self.log(f"Deletion of IoT Twinmaker Component Type initiated: {component_type_id}")

    while True:
      try:
        globals.aws_twinmaker_client.get_component_type(workspaceId=workspace_name, componentTypeId=component_type_id)
        time.sleep(2)
      except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
          break
        else:
          raise

    self.log(f"Deleted IoT Twinmaker Component Type: {component_type_id}")

  def info(self, iot_device):
    workspace_name = globals.twinmaker_workspace_name()
    component_type_id = globals.twinmaker_component_type_id(iot_device)

    try:
      globals.aws_twinmaker_client.get_component_type(workspaceId=workspace_name, componentTypeId=component_type_id)
      self.log(f"✅ Twinmaker Component Type {component_type_id} exists: {util.link_to_twinmaker_component_type(workspace_name, component_type_id)}")
    except ClientError as e:
      if e.response["Error"]["Code"] == "ResourceNotFoundException":
        self.log(f"❌ Twinmaker Component Type {component_type_id} missing: {component_type_id}")
      else:
        raise
