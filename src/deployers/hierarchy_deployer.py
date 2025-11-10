import time
import globals
import util
from botocore.exceptions import ClientError



def create_twinmaker_entity(entity_info, parent_info=None):
  create_entity_params = {
    "workspaceId": globals.twinmaker_workspace_name(),
    "entityName": entity_info.get("name") or entity_info["id"],
    "entityId": entity_info["id"],
  }

  if parent_info is not None:
    create_entity_params["parentEntityId"] = parent_info["id"]

  response = globals.aws_twinmaker_client.create_entity(**create_entity_params)

  log(f"Created IoT TwinMaker Entity: {response["entityId"]}")

  for child in entity_info["children"]:
    if child["type"] == "entity":
      create_twinmaker_entity(child, entity_info)
    elif child["type"] == "component":
      create_twinmaker_component(child, entity_info)

def create_twinmaker_component(component_info, parent_info):
  if "componentTypeId" in component_info:
    component_type_id = component_info["componentTypeId"]
  else:
    component_type_id = f"{globals.config["digital_twin_name"]}-{component_info["iotDeviceId"]}"

  globals.aws_twinmaker_client.update_entity(
    workspaceId=globals.twinmaker_workspace_name(),
    entityId=parent_info["id"],
    componentUpdates={
        component_info["name"]: {
            "updateType": "CREATE",
            "componentTypeId": component_type_id
        }
    }
  )

  log(f"Created IoT TwinMaker Component: {component_info["name"]}")


def create_twinmaker_hierarchy():
  for entity in globals.config_hierarchy:
    create_twinmaker_entity(entity)

def destroy_twinmaker_hierarchy():
  workspace_name = globals.twinmaker_workspace_name()
  deleting_entities = []

  for entity in globals.config_hierarchy:
    try:
      globals.aws_twinmaker_client.delete_entity(workspaceId=workspace_name, entityId=entity["id"], isRecursive=True)
      deleting_entities.append(entity)
    except ClientError as e:
      if e.response["Error"]["Code"] != "ResourceNotFoundException":
        raise

  for entity in deleting_entities:
    while True:
      try:
        globals.aws_twinmaker_client.get_entity(workspaceId=workspace_name, entityId=entity["id"])
        time.sleep(2)
      except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
          break
        else:
          raise

    log(f"Deleted IoT TwinMaker Entity: {entity["id"]}")

def info_twinmaker_hierarchy(hierarchy=None, parent=None):
  workspace_name = globals.twinmaker_workspace_name()

  if hierarchy is None:
    hierarchy = globals.config_hierarchy

  for entry in hierarchy:
    if entry["type"] == "entity":
      try:
        response = globals.aws_twinmaker_client.get_entity(workspaceId=workspace_name, entityId=entry["id"])
        log(f"✅ IoT TwinMaker Entity exists: {util.link_to_twinmaker_entity(workspace_name, entry["id"])}")

        if parent is not None and parent["entityId"] != response.get("parentEntityId"):
          log(f"❌ IoT TwinMaker Entity {entry["id"]} is missing parent: {parent["entityId"]}")

        if "children" in entry:
          info_twinmaker_hierarchy(entry["children"], response)
      except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
          log(f"❌ IoT TwinMaker Entity missing: {entry["id"]}")
        else:
          raise

    elif entry["type"] == "component":
      if parent is None:
        continue

      if entry["name"] not in parent.get("components", {}):
        log(f"❌ IoT TwinMaker Entity {parent["entityId"]} is missing component: {entry["name"]}")
        continue

      log(f"✅ IoT TwinMaker Component exists: {util.link_to_twinmaker_component(workspace_name, parent["entityId"], entry["name"])}")

      component_info = parent["components"][entry["name"]]

      if "componentTypeId" in entry:
        entry_component_type_id = entry["componentTypeId"]
      else:
        entry_component_type_id = f"{globals.config["digital_twin_name"]}-{entry["iotDeviceId"]}"

      if component_info["componentTypeId"] != entry_component_type_id:
        log(f"❌ IoT TwinMaker Component {entry["name"]} has the wrong component type: {component_info["componentTypeId"]}")


def deploy_l4():
  create_twinmaker_hierarchy()

def destroy_l4():
  destroy_twinmaker_hierarchy()

def info_l4():
  info_twinmaker_hierarchy()


def deploy():
  deploy_l4()

def destroy():
  destroy_l4()

def info():
  info_l4()


def log(string):
  print(f"Hierarchy Deployer: " + string)
