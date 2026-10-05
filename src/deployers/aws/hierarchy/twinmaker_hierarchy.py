import deployment_state
import resource_names
from deployers.aws.apply_actions import ACTION_DESTROY, ACTION_DEPLOY
from deployers.aws.core.json_helpers import content_changed
from deployers.aws.iot.device_config import effective_iot_devices
from deployers.aws.core.plan_actions import plan_action
from deployers.base import Deployer
from dependency_graph import plan_graph_ids
import time
import globals
import util
from botocore.exceptions import ClientError

DELETE_POLL_SECONDS = 2
DELETE_PROGRESS_LOG_SECONDS = 30
DELETE_TIMEOUT_SECONDS = 60


class TwinmakerHierarchyDeployer(Deployer):
  def log(self, message):
    print(f"Hierarchy: {message}")

  def _root_entities_by_id(self, hierarchy):
    return {entity["id"]: entity for entity in hierarchy}

  def _ordered_root_ids(self, previous_hierarchy, desired_hierarchy):
    previous_entities = self._root_entities_by_id(previous_hierarchy)
    root_ids = []

    for entity in previous_hierarchy:
      root_ids.append(entity["id"])

    for entity in desired_hierarchy:
      if entity["id"] not in previous_entities:
        root_ids.append(entity["id"])

    return root_ids


  def _root_entity(self, hierarchy, entity_id):
    entity = self._root_entities_by_id(hierarchy).get(entity_id)

    if entity is None:
      raise ValueError(f"TwinMaker Hierarchy root entity not found: {entity_id}")

    return entity

  def _configured_iot_device_ids(self):
    return {
      iot_device["id"]
      for iot_device in effective_iot_devices(globals.config_iot_devices)
    }

  def _collect_missing_iot_device_ids_for_components(
    self,
    entity_info,
    configured_iot_device_ids,
    missing_iot_device_ids,
  ):
    for child in entity_info.get("children", []):
      if child["type"] == "entity":
        self._collect_missing_iot_device_ids_for_components(
          child,
          configured_iot_device_ids,
          missing_iot_device_ids,
        )
      elif child["type"] == "component" and "iotDeviceId" in child:
        iot_device_id = child["iotDeviceId"]

        if iot_device_id not in configured_iot_device_ids:
          missing_iot_device_ids.add(iot_device_id)

  def _validate_component_type_sources(self, hierarchy):
    configured_iot_device_ids = self._configured_iot_device_ids()
    missing_iot_device_ids = set()

    for entity in hierarchy:
      self._collect_missing_iot_device_ids_for_components(
        entity,
        configured_iot_device_ids,
        missing_iot_device_ids,
      )

    if missing_iot_device_ids:
      missing_ids = ", ".join(sorted(missing_iot_device_ids))
      raise ValueError(
        "Hierarchy references IoT device id(s) that are missing from "
        f"config_iot_devices.json: {missing_ids}. "
        "TwinMaker component types are deployed from config_iot_devices before "
        "hierarchy is applied."
      )

  def _wait_until_entity_deleted(self, workspace_name, entity):
    started_at = time.monotonic()
    last_log_at = started_at

    while True:
      try:
        response = globals.aws_twinmaker_client.get_entity(workspaceId=workspace_name, entityId=entity["id"])
        elapsed_seconds = int(time.monotonic() - started_at)

        if elapsed_seconds >= DELETE_TIMEOUT_SECONDS:
          status = response.get("status", {})
          state = status.get("state", "UNKNOWN")
          error_message = status.get("error", {}).get("message")
          details = f" Current state: {state}."

          if error_message:
            details += f" Error: {error_message}"

          # raise TimeoutError(
          #   f"Timed out waiting for IoT TwinMaker Entity deletion: {entity["id"]}."
          #   f"{details}"
          # )
          self.log(f"Timed out waiting for IoT TwinMaker Entity deletion: {entity["id"]}. Details: {details}. Continue execution.")
          break

        now = time.monotonic()

        if now - last_log_at >= DELETE_PROGRESS_LOG_SECONDS:
          state = response.get("status", {}).get("state", "UNKNOWN")
          self.log(
            f"Still waiting for IoT TwinMaker Entity deletion: {entity["id"]} "
            f"({elapsed_seconds}s, state: {state})"
          )
          last_log_at = now

        time.sleep(DELETE_POLL_SECONDS)
      except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
          break
        else:
          raise

    self.log(f"Deleted IoT TwinMaker Entity: {entity["id"]}")

  def _deploy_twinmaker_entity(self, entity_info, workspace_name, parent_info=None):
    create_entity_params = {
      "workspaceId": workspace_name,
      "entityName": entity_info.get("name") or entity_info["id"],
      "entityId": entity_info["id"],
    }

    if parent_info is not None:
      create_entity_params["parentEntityId"] = parent_info["id"]

    response = globals.aws_twinmaker_client.create_entity(**create_entity_params)

    self.log(f"Created IoT TwinMaker Entity: {response["entityId"]}")

    for child in entity_info["children"]:
      if child["type"] == "entity":
        self._deploy_twinmaker_entity(child, workspace_name, entity_info)
      elif child["type"] == "component":
        self._deploy_twinmaker_component(child, entity_info, workspace_name)

  def _deploy_twinmaker_component(self, component_info, parent_info, workspace_name):
    component_type_id = resource_names.hierarchy_component_type_id(
      globals.config,
      component_info,
    )

    component_update = {
      "updateType": "CREATE",
      "componentTypeId": component_type_id,
    }

    if "iotDeviceId" in component_info:
      component_update["propertyUpdates"] = {
        "iotDeviceId": {
          "updateType": "CREATE",
          "value": {"stringValue": str(component_info["iotDeviceId"])},
        }
      }

    globals.aws_twinmaker_client.update_entity(
      workspaceId=workspace_name,
      entityId=parent_info["id"],
      componentUpdates={
          component_info["name"]: component_update
      }
    )

    self.log(f"Created IoT TwinMaker Component: {component_info["name"]}")

  def plan(self):
    previous_hierarchy = deployment_state.last_applied_config_hierarchy
    desired_hierarchy = globals.config_hierarchy

    previous_workspace_name = deployment_state.last_applied_twinmaker_workspace_name()
    desired_workspace_name = globals.twinmaker_workspace_name()

    previous_entities = self._root_entities_by_id(previous_hierarchy)
    desired_entities = self._root_entities_by_id(desired_hierarchy)
    actions = []

    for entity_id in self._ordered_root_ids(previous_hierarchy, desired_hierarchy):
      previous_entity = previous_entities.get(entity_id)
      desired_entity = desired_entities.get(entity_id)

      if previous_entity is None:
        self.log(f"TwinMaker Hierarchy root entity {entity_id} is new.")
        actions.append(
          plan_action(
            entity_id,
            "twinmaker_hierarchy",
            action="DEPLOY",
            graph_id=plan_graph_ids.twinmaker_hierarchy(entity_id),
          )
        )
        continue

      if desired_entity is None:
        self.log(f"TwinMaker Hierarchy root entity {entity_id} was removed from config.")
        actions.append(
          plan_action(
            entity_id,
            "twinmaker_hierarchy",
            action="DESTROY",
            graph_id=plan_graph_ids.twinmaker_hierarchy(entity_id),
          )
        )
        continue

      if (
        previous_workspace_name == desired_workspace_name
        and not content_changed(previous_entity, desired_entity)
      ):
        self.log(f"TwinMaker Hierarchy root entity {entity_id} is up to date.")
        actions.append(
          plan_action(
            entity_id,
            "twinmaker_hierarchy",
            graph_id=plan_graph_ids.twinmaker_hierarchy(entity_id),
          )
        )
        continue

      if previous_workspace_name != desired_workspace_name:
        self.log(
          "TwinMaker Hierarchy workspace has changed from "
          f"{previous_workspace_name} to {desired_workspace_name}."
        )

      if content_changed(previous_entity, desired_entity):
        self.log(f"TwinMaker Hierarchy root entity {entity_id} has changed.")

      actions.extend([
        plan_action(
          entity_id,
          "twinmaker_hierarchy",
          action="DESTROY",
          graph_id=plan_graph_ids.twinmaker_hierarchy(entity_id),
        ),
        plan_action(
          entity_id,
          "twinmaker_hierarchy",
          action="DEPLOY",
          graph_id=plan_graph_ids.twinmaker_hierarchy(entity_id),
        ),
      ])

    return actions


  def deploy(self, entity_id=None, hierarchy=None, workspace_name=None):
    if hierarchy is None:
      hierarchy = globals.config_hierarchy

    workspace_name = workspace_name or globals.twinmaker_workspace_name()
    self._validate_component_type_sources(hierarchy)

    if entity_id is not None:
      self._deploy_twinmaker_entity(
        self._root_entity(hierarchy, entity_id),
        workspace_name,
      )
      return

    for entity in hierarchy:
      self._deploy_twinmaker_entity(entity, workspace_name)

  def destroy(self, entity_id=None, hierarchy=None, workspace_name=None):
    if hierarchy is None:
      hierarchy = globals.config_hierarchy

    workspace_name = workspace_name or globals.twinmaker_workspace_name()

    if entity_id is not None:
      hierarchy = [self._root_entity(hierarchy, entity_id)]

    deleting_entities = []

    for entity in hierarchy:
      try:
        globals.aws_twinmaker_client.delete_entity(workspaceId=workspace_name, entityId=entity["id"], isRecursive=True)
        deleting_entities.append(entity)
      except ClientError as e:
        error = e.response["Error"]

        if error["Code"] == "ResourceNotFoundException":
          continue

        if error["Code"] == "ValidationException" and "already in Deleting state" in error["Message"]:
          self.log(f"IoT TwinMaker Entity deletion already in progress: {entity["id"]}")
          deleting_entities.append(entity)
          continue

        raise

    for entity in deleting_entities:
      self._wait_until_entity_deleted(workspace_name, entity)

  def apply(self, action, resource):
    if action["action"] == ACTION_DESTROY:
      self.destroy(
        entity_id=resource,
        hierarchy=deployment_state.last_applied_config_hierarchy,
        workspace_name=deployment_state.last_applied_twinmaker_workspace_name(),
      )
    elif action["action"] == ACTION_DEPLOY:
      self.deploy(
        entity_id=resource,
        hierarchy=globals.config_hierarchy,
        workspace_name=globals.twinmaker_workspace_name(),
      )
    else:
      raise ValueError(f"Unsupported hierarchy action: {action['action']}")


  def info(self, hierarchy=None, parent=None):
    workspace_name = globals.twinmaker_workspace_name()

    if hierarchy is None:
      hierarchy = globals.config_hierarchy

    for entry in hierarchy:
      if entry["type"] == "entity":
        try:
          response = globals.aws_twinmaker_client.get_entity(workspaceId=workspace_name, entityId=entry["id"])
          self.log(f"✅ IoT TwinMaker Entity exists: {util.link_to_twinmaker_entity(workspace_name, entry["id"])}")

          if parent is not None and parent["entityId"] != response.get("parentEntityId"):
            self.log(f"❌ IoT TwinMaker Entity {entry["id"]} is missing parent: {parent["entityId"]}")

          if "children" in entry:
            self.info(entry["children"], response)
        except ClientError as e:
          if e.response["Error"]["Code"] == "ResourceNotFoundException":
            self.log(f"❌ IoT TwinMaker Entity missing: {entry["id"]}")
          else:
            raise

      elif entry["type"] == "component":
        if parent is None:
          continue

        if entry["name"] not in parent.get("components", {}):
          self.log(f"❌ IoT TwinMaker Entity {parent["entityId"]} is missing component: {entry["name"]}")
          continue

        self.log(f"✅ IoT TwinMaker Component exists: {util.link_to_twinmaker_component(workspace_name, parent["entityId"], entry["name"])}")

        component_info = parent["components"][entry["name"]]

        entry_component_type_id = resource_names.hierarchy_component_type_id(
          globals.config,
          entry,
        )

        if component_info["componentTypeId"] != entry_component_type_id:
          self.log(f"❌ IoT TwinMaker Component {entry["name"]} has the wrong component type: {component_info["componentTypeId"]}")
