from __future__ import annotations

import json
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from dependency_graph_helpers import ensure_src_path
from tests.aws_stubs import AWS_REGION, StubAwsClient, StubStsClient, install_aws_stubs


ensure_src_path()
install_aws_stubs()


import deployment_state
import deployers.aws.core.all
import deployers.aws.event_actions.all
import deployers.aws.hierarchy.all
import deployers.aws.init_values.all
import deployers.aws.iot.all
import globals
import main
from dependency_graph.dependency_analyzer import analyze_plan_dependencies
from dependency_graph.models import (
  DependencyType,
  RuntimeDependency,
  RuntimeGraph,
  RuntimeNode,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_ANALYSIS_CONFIGS_DIR = REPO_ROOT / "configs" / "plan-analysis"
CONFIG_CASES_DIR = PLAN_ANALYSIS_CONFIGS_DIR / "config-cases"
SYNTHETIC_BLOCKERS_DIR = PLAN_ANALYSIS_CONFIGS_DIR / "synthetic-blockers"

CONFIG_CASES_WITH_NO_BLOCKERS = [
  ("no-change", {"DESTROY": 0, "DEPLOY": 0}),
  ("full-replacement", {"DESTROY": "present", "DEPLOY": "present"}),
  ("added-iot-device", {"DEPLOY": "present"}),
  ("removed-iot-device", {"DESTROY": "present"}),
  ("removed-hierarchy-entity-component", {"DESTROY": "present", "DEPLOY": "present"}),
  ("changed-event-action", {"DESTROY": "present", "DEPLOY": "present"}),
  ("removed-event-action", {"DESTROY": "present", "DEPLOY": "present"}),
  ("init-values-changed", {"DESTROY": 0, "DEPLOY": "present"}),
]

SYNTHETIC_BLOCKER_CASES = [
  ("missing-prerequisite-deploy", "missing from desired graph"),
  ("reverse-dependent-destroy", "still depends on it"),
]


class PlanAnalysisConfigFixtureTests(unittest.TestCase):
  def test_config_cases_have_expected_plan_actions_without_blockers(self) -> None:
    for case_name, expected_counts in CONFIG_CASES_WITH_NO_BLOCKERS:
      with self.subTest(case_name=case_name):
        load_plan_analysis_case(case_name)

        with redirect_stdout(StringIO()):
          plan_groups = build_plan_groups()

        counts_before_analysis = action_counts(plan_groups)

        main._analyze_plan_dependencies(plan_groups)

        assert_expected_counts(self, counts_before_analysis, expected_counts)
        self.assertEqual([], blocked_action_summaries(plan_groups))

  def test_shared_component_type_is_deployed_once(self) -> None:
    load_plan_analysis_case("shared-component-type")

    with redirect_stdout(StringIO()):
      plan_groups = build_plan_groups()

    main._analyze_plan_dependencies(plan_groups)

    self.assertEqual([], blocked_action_summaries(plan_groups))

    component_type_deploys = [
      action
      for _, layer_name, action in iter_plan_actions(plan_groups)
      if layer_name == "iot_l4"
      and action["resource_type"] == "twinmaker_component_type"
      and action["action"] == "DEPLOY"
    ]

    self.assertEqual(
      1,
      len(component_type_deploys),
      "Two IoT devices sharing one componentTypeId should deploy a single "
      f"TwinMaker Component Type, got: {component_type_deploys}",
    )

  def test_synthetic_blocker_cases_have_expected_blockers(self) -> None:
    for case_name, blocker_text in SYNTHETIC_BLOCKER_CASES:
      with self.subTest(case_name=case_name):
        previous_graph, desired_graph, plan_groups = load_synthetic_blocker_case(
          case_name
        )

        analyze_plan_dependencies(previous_graph, desired_graph, plan_groups)

        blocked_summaries = blocked_action_summaries(plan_groups)
        self.assertEqual(1, len(blocked_summaries))
        self.assertIn(blocker_text, blocked_summaries[0])


def assert_expected_counts(
  test_case: unittest.TestCase,
  counts: dict[str, int],
  expected_counts: dict[str, int | str],
) -> None:
  for action_name, expectation in expected_counts.items():
    if expectation == "present":
      test_case.assertGreater(counts[action_name], 0)
    else:
      test_case.assertEqual(expectation, counts[action_name])


def load_plan_analysis_case(case_name: str) -> None:
  case_dir = CONFIG_CASES_DIR / case_name
  previous_configs = read_config_set(case_dir / "previous")
  desired_configs = read_config_set(case_dir / "desired")

  globals.config = desired_configs["config"]
  globals.config_iot_devices = desired_configs["config_iot_devices"]
  globals.config_events = desired_configs["config_events"]
  globals.config_hierarchy = desired_configs["config_hierarchy"]

  deployment_state.last_applied_config = previous_configs["config"]
  deployment_state.last_applied_config_iot_devices = (
    previous_configs["config_iot_devices"]
  )
  deployment_state.last_applied_config_events = previous_configs["config_events"]
  deployment_state.last_applied_config_hierarchy = (
    previous_configs["config_hierarchy"]
  )
  deployment_state.last_applied_state_metadata = {"awsRegion": AWS_REGION}

  globals.aws_s3_client = StubAwsClient()
  globals.aws_twinmaker_client = StubAwsClient()
  globals.aws_grafana_client = StubAwsClient()
  globals.aws_lambda_client = StubAwsClient()
  globals.aws_iot_client = StubAwsClient()
  globals.aws_sts_client = StubStsClient()


def read_config_set(config_dir: Path) -> dict:
  return {
    "config": read_json(config_dir / "config.json"),
    "config_events": read_json(config_dir / "config_events.json"),
    "config_hierarchy": read_json(config_dir / "config_hierarchy.json"),
    "config_iot_devices": read_json(config_dir / "config_iot_devices.json"),
  }


def load_synthetic_blocker_case(
  case_name: str,
) -> tuple[RuntimeGraph, RuntimeGraph, list[dict]]:
  case_dir = SYNTHETIC_BLOCKERS_DIR / case_name

  return (
    parse_runtime_graph(read_json(case_dir / "previous_graph.json")),
    parse_runtime_graph(read_json(case_dir / "desired_graph.json")),
    read_json(case_dir / "plan_groups.json"),
  )


def parse_runtime_graph(value: dict) -> RuntimeGraph:
  return RuntimeGraph(
    version=value["version"],
    nodes=tuple(parse_runtime_node(node) for node in value["nodes"]),
  )


def parse_runtime_node(value: dict) -> RuntimeNode:
  return RuntimeNode(
    id=value["id"],
    template_id=value["template_id"],
    owner_deployer=value["owner_deployer"],
    logical_name=value["logical_name"],
    physical_name=value.get("physical_name"),
    depends_on=tuple(
      parse_runtime_dependency(dependency)
      for dependency in value.get("depends_on", [])
    ),
    lifecycle_artifact=value.get("lifecycle_artifact", False),
  )


def parse_runtime_dependency(value: dict) -> RuntimeDependency:
  return RuntimeDependency(
    id=value["id"],
    template_id=value["template_id"],
    type=DependencyType.from_value(value["type"]),
  )


def read_json(path: Path):
  with open(path, "r", encoding="utf-8") as file:
    return json.load(file)


def build_plan_groups() -> list[dict]:
  return [
    deployers.aws.core.all.AllDeployer().plan(),
    deployers.aws.iot.all.AllDeployer().plan(),
    deployers.aws.hierarchy.all.AllDeployer().plan(),
    deployers.aws.event_actions.all.AllDeployer().plan(),
    deployers.aws.init_values.all.AllDeployer().plan(),
  ]


def action_counts(plan_groups: list[dict]) -> dict[str, int]:
  counts = {
    "DESTROY": 0,
    "DEPLOY": 0,
    "NO_CHANGE": 0,
  }

  for _, _, action in iter_plan_actions(plan_groups):
    counts[action["action"]] += 1

  return counts


def blocked_action_summaries(plan_groups: list[dict]) -> list[str]:
  summaries = []

  for group_name, layer_name, action in iter_plan_actions(plan_groups):
    if not action.get("blocked", False):
      continue

    summaries.append(
      f"{group_name}/{layer_name}: "
      f"{action['action']} {action['resource_type']}/{action['resource']} "
      f"{action.get('blockers', [])}"
    )

  return summaries


def iter_plan_actions(plan_groups: list[dict]):
  for group in plan_groups:
    for layer in group["layers"]:
      for action in layer["actions"]:
        yield group["group"], layer["layer"], action


if __name__ == "__main__":
  unittest.main()
