"""Security audit of one deployed digital twin.

Runs a Prowler scan (read-only), keeps only the findings for the twin's resources,
and checks what Prowler does not cover: AWS IoT Core device policies, certificates
and topic rules.

Credentials come from the standard AWS environment (AWS_PROFILE, AWS_ACCESS_KEY_ID,
...), not from config_credentials.json. Use a read-only principal with the
SecurityAudit and ViewOnlyAccess managed policies.

Usage:
  uv run python scripts/security_audit.py --twin dtcBattery
  uv run python scripts/security_audit.py --twin dtcBattery --prowler-report out/x.ocsf.json
"""
import argparse
import collections
import datetime
import json
import pathlib
import subprocess
import sys

import boto3
from botocore.exceptions import ClientError

# Prowler has no IoT Core or TwinMaker checks; those are covered by iot_findings().
PROWLER_SERVICES = [
  "iam", "awslambda", "dynamodb", "s3", "cloudwatch", "eventbridge", "sns", "sqs", "kms",
]
SEVERITY_ORDER = ["Critical", "High", "Medium", "Low", "Informational"]
MAX_CERTIFICATE_YEARS = 5


def run_prowler(region, output_dir):
  output_dir.mkdir(parents=True, exist_ok=True)
  command = [
    "uvx", "--python", "3.12", "prowler", "aws",
    "--region", region,
    "--service", *PROWLER_SERVICES,
    "--output-formats", "json-ocsf", "html",
    "--output-directory", str(output_dir),
    "--no-banner",
  ]
  print(f"Running Prowler on {', '.join(PROWLER_SERVICES)} in {region} ...")
  # Prowler exits with 3 when the scan succeeded but found failures.
  result = subprocess.run(command)
  if result.returncode not in (0, 3):
    sys.exit(f"Prowler failed with exit code {result.returncode}")

  reports = sorted(output_dir.glob("*.ocsf.json"), key=lambda path: path.stat().st_mtime)
  if not reports:
    sys.exit(f"No Prowler report found in {output_dir}")
  return reports[-1]


def prowler_findings(report_path, twin):
  with open(report_path) as file:
    findings = json.load(file)

  def belongs_to_twin(finding):
    resource = finding.get("resources", [{}])[0]
    return twin.lower() in (resource.get("name", "") + resource.get("uid", "")).lower()

  return [
    {
      "source": "prowler",
      "service": finding["resources"][0].get("group", {}).get("name", "?"),
      "severity": finding["severity"],
      "status": finding["status_code"],
      "title": finding["finding_info"]["title"],
      "resource": finding["resources"][0].get("name") or finding["resources"][0].get("uid", ""),
    }
    for finding in findings
    if belongs_to_twin(finding)
  ]


def policy_statements(policy_document):
  statements = policy_document["Statement"]
  return [statements] if isinstance(statements, dict) else statements


def as_list(value):
  return value if isinstance(value, list) else [value]


def iot_findings(session, twin):
  iot = session.client("iot")
  findings = []

  def finding(severity, title, resource):
    findings.append({
      "source": "iot", "service": "iot", "severity": severity,
      "status": "FAIL", "title": title, "resource": resource,
    })

  def paginate(operation, key, **kwargs):
    for page in iot.get_paginator(operation).paginate(**kwargs):
      yield from page[key]

  prefixes = (f"{twin}-", f"{twin}_")

  # Device policies: no wildcard actions or resources.
  for policy in paginate("list_policies", "policies"):
    name = policy["policyName"]
    if not name.startswith(prefixes):
      continue

    document = json.loads(iot.get_policy(policyName=name)["policyDocument"])
    for statement in policy_statements(document):
      if statement["Effect"] != "Allow":
        continue
      if any("*" in action for action in as_list(statement["Action"])):
        finding("High", "IoT policy allows wildcard actions", name)
      if any("*" in resource for resource in as_list(statement["Resource"])):
        finding("High", "IoT policy applies to wildcard resources", name)

  # Certificates attached to the twin's things.
  for thing in paginate("list_things", "things"):
    thing_name = thing["thingName"]
    if not thing_name.startswith(prefixes):
      continue

    principals = iot.list_thing_principals(thingName=thing_name)["principals"]
    if len(principals) != 1:
      finding("Medium", f"IoT thing has {len(principals)} certificates (expected 1)", thing_name)

    for principal in principals:
      certificate_id = principal.rsplit("/", 1)[-1]
      description = iot.describe_certificate(certificateId=certificate_id)["certificateDescription"]
      validity = description["validity"]
      years = (validity["notAfter"] - validity["notBefore"]).days / 365

      if years > MAX_CERTIFICATE_YEARS:
        finding("Medium", f"IoT certificate is valid for {years:.0f} years", thing_name)
      if description["status"] != "ACTIVE":
        finding("Low", f"IoT certificate is {description['status']}", thing_name)

  # Topic rules.
  for rule in paginate("list_topic_rules", "rules"):
    name = rule["ruleName"]
    if not name.startswith(prefixes):
      continue

    try:
      definition = iot.get_topic_rule(ruleName=name)["rule"]
    except ClientError as error:
      finding("Informational", f"IoT topic rule not readable ({error.response['Error']['Code']})", name)
      continue

    if definition.get("ruleDisabled"):
      finding("Low", "IoT topic rule is disabled", name)
    if not definition.get("errorAction"):
      finding("Low", "IoT topic rule has no errorAction", name)
    if definition.get("awsIotSqlVersion", "2015-10-08") == "2015-10-08":
      finding("Low", "IoT topic rule uses the legacy SQL version 2015-10-08", name)

  return findings


def print_summary(findings, twin):
  failed = [item for item in findings if item["status"] == "FAIL"]
  passed = len(findings) - len(failed)
  print(f"\n{twin}: {len(findings)} findings, {passed} passed, {len(failed)} failed (IoT checks only report failures)")

  by_severity = collections.Counter(item["severity"] for item in failed)
  for severity in SEVERITY_ORDER:
    if by_severity[severity]:
      print(f"  {severity}: {by_severity[severity]}")

  groups = collections.defaultdict(list)
  for item in failed:
    groups[(item["severity"], item["service"], item["title"])].append(item["resource"])

  def severity_rank(key):
    return SEVERITY_ORDER.index(key[0]) if key[0] in SEVERITY_ORDER else len(SEVERITY_ORDER)

  print()
  for key in sorted(groups, key=lambda key: (severity_rank(key), key[1], key[2])):
    severity, service, title = key
    resources = sorted(set(groups[key]))
    shown = ", ".join(resources[:3]) + (" ..." if len(resources) > 3 else "")
    print(f"[{severity}] ({service}) {title} - {len(groups[key])}\n    {shown}")


def main():
  parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument("--twin", required=True, help="digital twin name; resources are matched by this prefix")
  parser.add_argument("--region", default=None, help="AWS region (default: from the AWS environment)")
  parser.add_argument("--output-dir", default="security-audit-output", help="where reports are written")
  parser.add_argument("--prowler-report", help="reuse an existing Prowler .ocsf.json instead of scanning")
  parser.add_argument("--fail-on", choices=["High", "Critical"], help="exit 1 if a failed finding has this severity or worse")
  args = parser.parse_args()

  session = boto3.Session(region_name=args.region)
  region = session.region_name
  if not region:
    sys.exit("No region: pass --region or set AWS_DEFAULT_REGION")

  identity = session.client("sts").get_caller_identity()
  print(f"Auditing as {identity['Arn']} (account {identity['Account']}, {region})")

  output_dir = pathlib.Path(args.output_dir)
  report_path = pathlib.Path(args.prowler_report) if args.prowler_report else run_prowler(region, output_dir)

  findings = prowler_findings(report_path, args.twin) + iot_findings(session, args.twin)
  print_summary(findings, args.twin)

  output_dir.mkdir(parents=True, exist_ok=True)
  result_path = output_dir / f"{args.twin}-findings.json"
  result_path.write_text(json.dumps({
    "twin": args.twin,
    "account": identity["Account"],
    "region": region,
    "created": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "prowler_report": str(report_path),
    "findings": findings,
  }, indent=2))
  print(f"\nFindings written to {result_path}")

  if args.fail_on:
    blocking = SEVERITY_ORDER[:SEVERITY_ORDER.index(args.fail_on) + 1]
    if any(item["status"] == "FAIL" and item["severity"] in blocking for item in findings):
      sys.exit(1)


if __name__ == "__main__":
  main()
