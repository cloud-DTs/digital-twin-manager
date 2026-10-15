from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from tests.aws_stubs import StubAwsClient, StubStsClient, install_aws_stubs

install_aws_stubs()

import globals
from deployers.aws.core.hot_reader_lambda_function import HotReaderLambdaFunctionDeployer


class RecordingLambdaClient(StubAwsClient):
  def __init__(self):
    super().__init__()
    self.add_permission_calls = []

  def create_function(self, **kwargs):
    pass

  def add_permission(self, **kwargs):
    self.add_permission_calls.append(kwargs)


class RoleIamClient:
  def get_role(self, RoleName):
    return {"Role": {"Arn": f"arn:aws:iam::123456789012:role/{RoleName}"}}


class HotReaderLambdaPermissionTests(unittest.TestCase):
  def setUp(self) -> None:
    self.original_globals = {
      name: getattr(globals, name, None)
      for name in ("config", "aws_iam_client", "aws_lambda_client", "aws_sts_client")
    }

    globals.config = {
      "digital_twin_name": "dtc-y-01",
      "hot_storage_size_in_days": 30,
      "cold_storage_size_in_days": 60,
    }
    globals.aws_iam_client = RoleIamClient()
    globals.aws_lambda_client = RecordingLambdaClient()
    globals.aws_sts_client = StubStsClient()

    patcher = patch("util.compile_lambda_function", return_value=b"zip")
    patcher.start()
    self.addCleanup(patcher.stop)

  def tearDown(self) -> None:
    for name, value in self.original_globals.items():
      setattr(globals, name, value)

  def test_twinmaker_invoke_permission_is_limited_to_this_account(self) -> None:
    HotReaderLambdaFunctionDeployer().deploy()

    calls = globals.aws_lambda_client.add_permission_calls
    self.assertEqual(len(calls), 1)
    self.assertEqual(calls[0]["Principal"], "iottwinmaker.amazonaws.com")
    self.assertEqual(calls[0]["Action"], "lambda:InvokeFunction")
    self.assertEqual(calls[0]["SourceAccount"], "123456789012")


if __name__ == "__main__":
  unittest.main()
