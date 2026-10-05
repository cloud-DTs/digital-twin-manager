from __future__ import annotations
import unittest
from src.validation import config_hierarchy
from validation_helpers import clone, valid_config_hierarchy


class ConfigHierarchyValidationTests(unittest.TestCase):
  def test_valid_config_hierarchy_passes(self) -> None:
    config_hierarchy.validate(valid_config_hierarchy())

  def test_root_component_fails(self) -> None:
    value = [
      {
        "type": "component",
        "name": "temperatureSensor",
        "iotDeviceId": "sensor-1",
      }
    ]

    with self.assertRaisesRegex(ValueError, "must be one of"):
      config_hierarchy.validate(value)

  def test_component_without_source_fails(self) -> None:
    value = valid_config_hierarchy()
    del value[0]["children"][0]["iotDeviceId"]

    with self.assertRaisesRegex(ValueError, "at least one"):
      config_hierarchy.validate(value)

  def test_component_with_component_type_id_only_passes(self) -> None:
    value = valid_config_hierarchy()
    del value[0]["children"][0]["iotDeviceId"]
    value[0]["children"][0]["componentTypeId"] = "shared-sensor-type"

    config_hierarchy.validate(value)

  def test_component_with_both_sources_passes(self) -> None:
    value = valid_config_hierarchy()
    value[0]["children"][0]["componentTypeId"] = "shared-sensor-type"

    config_hierarchy.validate(value)

  def test_duplicate_entity_id_fails(self) -> None:
    value = valid_config_hierarchy()
    duplicate_entity = clone(value[0]["children"][1])
    duplicate_entity["id"] = "room-1"
    value[0]["children"].append(duplicate_entity)

    with self.assertRaisesRegex(ValueError, "duplicated"):
      config_hierarchy.validate(value)

  def test_duplicate_component_name_in_same_entity_fails(self) -> None:
    value = valid_config_hierarchy()
    duplicate_component = clone(value[0]["children"][0])
    value[0]["children"].append(duplicate_component)

    with self.assertRaisesRegex(ValueError, "duplicated in the same entity"):
      config_hierarchy.validate(value)


if __name__ == "__main__":
  unittest.main()
