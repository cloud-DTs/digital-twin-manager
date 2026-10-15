from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from tests.aws_stubs import StubAwsClient, StubStsClient, install_aws_stubs

install_aws_stubs()

import globals
from deployers.aws.iot.iot_thing import IotThingDeployer


class RecordingIotClient(StubAwsClient):
  def __init__(self):
    super().__init__()
    self.create_policy_calls = []
    self.attach_policy_calls = []

  def create_thing(self, **kwargs):
    pass

  def create_keys_and_certificate(self, **kwargs):
    return {
      "certificateArn": "arn:aws:iot:eu-west-1:123456789012:cert/abc",
      "certificateId": "abc",
      "certificatePem": "pem",
      "keyPair": {"PrivateKey": "private", "PublicKey": "public"},
    }

  def create_policy(self, **kwargs):
    self.create_policy_calls.append(kwargs)

  def attach_thing_principal(self, **kwargs):
    pass

  def attach_policy(self, **kwargs):
    self.attach_policy_calls.append(kwargs)


class IotDevicePolicyTests(unittest.TestCase):
  def setUp(self) -> None:
    self.original_globals = {
      name: getattr(globals, name, None)
      for name in ("config", "config_events", "aws_iot_client", "aws_sts_client", "iot_data_path")
    }

    self.tmp_dir = tempfile.TemporaryDirectory()
    self.addCleanup(self.tmp_dir.cleanup)

    globals.config = {
      "digital_twin_name": "dtc-y-01",
      "hot_storage_size_in_days": 30,
      "cold_storage_size_in_days": 60,
    }
    globals.config_events = [
      {
        "action": {
          "feedback": {"type": "mqtt", "topic": "dtc-y-01-custom-topic", "payload": "action-result"}
        }
      },
      {
        "action": {
          "feedback": {"type": "mqtt", "iotDeviceId": "other-device", "payload": "action-result"}
        }
      },
      {"action": {"type": "lambda"}},
    ]
    globals.aws_iot_client = RecordingIotClient()
    globals.aws_sts_client = StubStsClient()
    globals.iot_data_path = self.tmp_dir.name

  def tearDown(self) -> None:
    for name, value in self.original_globals.items():
      setattr(globals, name, value)

  def _deployed_policy(self):
    IotThingDeployer().deploy({"id": "device-1"})

    calls = globals.aws_iot_client.create_policy_calls
    self.assertEqual(len(calls), 1)
    return json.loads(calls[0]["policyDocument"])

  def _statement_for(self, policy, action):
    matching = [s for s in policy["Statement"] if s["Action"] == action]
    self.assertEqual(len(matching), 1, f"expected exactly one {action} statement")
    return matching[0]

  def test_device_policy_has_no_wildcards(self) -> None:
    policy = self._deployed_policy()

    for statement in policy["Statement"]:
      actions = statement["Action"] if isinstance(statement["Action"], list) else [statement["Action"]]
      resources = statement["Resource"] if isinstance(statement["Resource"], list) else [statement["Resource"]]

      for action in actions:
        self.assertNotIn("*", action)
      for resource in resources:
        self.assertNotIn("*", resource)

  def test_device_can_only_connect_as_itself(self) -> None:
    statement = self._statement_for(self._deployed_policy(), "iot:Connect")

    self.assertEqual(
      statement["Resource"],
      "arn:aws:iot:eu-west-1:123456789012:client/device-1",
    )

  def test_device_can_only_publish_to_the_ingest_topic(self) -> None:
    statement = self._statement_for(self._deployed_policy(), "iot:Publish")

    self.assertEqual(
      statement["Resource"],
      "arn:aws:iot:eu-west-1:123456789012:topic/dtc-y-01/iot-data",
    )

  def test_device_can_only_read_its_own_and_configured_feedback_topics(self) -> None:
    policy = self._deployed_policy()
    topics = ["dtc-y-01-custom-topic", "dtc-y-01-device-1"]

    subscribe = self._statement_for(policy, "iot:Subscribe")
    receive = self._statement_for(policy, "iot:Receive")

    self.assertEqual(
      subscribe["Resource"],
      [f"arn:aws:iot:eu-west-1:123456789012:topicfilter/{topic}" for topic in topics],
    )
    self.assertEqual(
      receive["Resource"],
      [f"arn:aws:iot:eu-west-1:123456789012:topic/{topic}" for topic in topics],
    )

  def test_policy_is_attached_to_the_device_certificate(self) -> None:
    self._deployed_policy()

    self.assertEqual(
      [call["target"] for call in globals.aws_iot_client.attach_policy_calls],
      ["arn:aws:iot:eu-west-1:123456789012:cert/abc"],
    )


if __name__ == "__main__":
  unittest.main()
