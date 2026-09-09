# AWS Permissions

This document describes the IAM permissions required by `digital-twin-manager` when it runs against AWS using the credentials from `config_credentials.json`.

The permission set is derived from:

- Direct Boto3 calls in `src/`.
- The command flow in `src/main.py` for `deploy`, `info`, and `destroy`.
- AWS dependent permissions required by services such as Lambda, Step Functions, AWS IoT TwinMaker, and Amazon Managed Grafana.

The policy examples use `Resource: "*"` because the application creates resources with names derived from `digital_twin_name`, IoT device IDs, event action configuration, and generated AWS resource ARNs. A production policy should narrow resources where possible.

## Application-Managed Permissions

These permissions are required for resources that the application currently creates, checks, or destroys as part of its normal command flow.

### STS

Used to resolve the AWS account ID while building ARNs for Lambda permissions, Step Functions, and TwinMaker.

```text
sts:GetCallerIdentity
```

### IAM

Used to create and remove runtime IAM roles for Lambda, Step Functions, TwinMaker, and Grafana. The application also attaches AWS managed policies and writes inline policies to those roles.

```text
iam:CreateRole
iam:GetRole
iam:UpdateAssumeRolePolicy
iam:PutRolePolicy
iam:DeleteRolePolicy
iam:AttachRolePolicy
iam:DetachRolePolicy
iam:ListAttachedRolePolicies
iam:ListRolePolicies
iam:ListInstanceProfilesForRole
iam:RemoveRoleFromInstanceProfile
iam:DeleteRole
iam:PassRole
```

`iam:PassRole` is not called as a Boto3 IAM operation, but it is required when the application passes role ARNs to Lambda, Step Functions, TwinMaker, and Grafana create operations.

### Lambda

Used for core Lambdas, per-device processor Lambdas, optional internal event action Lambdas, and Lambda invoke permissions.

```text
lambda:CreateFunction
lambda:GetFunction
lambda:GetPolicy
lambda:DeleteFunction
lambda:AddPermission
lambda:RemovePermission
```

Internal event action Lambdas are only created when `config_events.json` contains an action with `"external": false`. The current checked-in configuration uses `"external": true`, but the application code supports internal actions.

### AWS IoT

Used for IoT Things, certificates, IoT policies, Thing/principal attachments, IoT rules, and init-value publishing.

```text
iot:CreateThing
iot:DescribeThing
iot:DeleteThing
iot:CreateKeysAndCertificate
iot:UpdateCertificate
iot:DeleteCertificate
iot:CreatePolicy
iot:DeletePolicy
iot:DeletePolicyVersion
iot:ListPolicyVersions
iot:AttachPolicy
iot:DetachPolicy
iot:AttachThingPrincipal
iot:DetachThingPrincipal
iot:ListThingPrincipals
iot:ListAttachedPolicies
iot:CreateTopicRule
iot:GetTopicRule
iot:ListTopicRules
iot:DeleteTopicRule
iot:Publish
```

`iot:Publish` is used by the init-values deployer when any configured IoT property has `initValue`. The current `config_iot_devices.json` contains init values, so this permission is part of the active deployment flow.

### EventBridge

Used for scheduled rules that trigger the hot-to-cold and cold-to-archive mover Lambdas.

```text
events:PutRule
events:DescribeRule
events:DeleteRule
events:PutTargets
events:ListTargetsByRule
events:RemoveTargets
```

### DynamoDB

Used for the hot storage table and for creating a table backup before table deletion.

```text
dynamodb:CreateTable
dynamodb:DescribeTable
dynamodb:DeleteTable
dynamodb:CreateBackup
dynamodb:DescribeBackup
```

### S3

Used for TwinMaker, cold storage, and archive buckets. The destroy flow empties buckets, including versioned objects and delete markers, before deleting the buckets.

```text
s3:CreateBucket
s3:PutBucketCORS
s3:GetBucketLocation
s3:ListBucket
s3:ListBucketVersions
s3:DeleteObject
s3:DeleteObjectVersion
s3:DeleteBucket
```

### AWS IoT TwinMaker

Used for the TwinMaker workspace, component types, entities, and entity component attachments.

```text
iottwinmaker:CreateWorkspace
iottwinmaker:GetWorkspace
iottwinmaker:DeleteWorkspace
iottwinmaker:CreateComponentType
iottwinmaker:GetComponentType
iottwinmaker:DeleteComponentType
iottwinmaker:ListComponentTypes
iottwinmaker:CreateEntity
iottwinmaker:GetEntity
iottwinmaker:UpdateEntity
iottwinmaker:DeleteEntity
iottwinmaker:ListEntities
```

### Amazon Managed Grafana

Used for the Grafana workspace created by Core L5.

```text
grafana:CreateWorkspace
grafana:DescribeWorkspace
grafana:DeleteWorkspace
grafana:ListWorkspaces
grafana:TagResource
```

`grafana:TagResource` is required because the application passes tags during `create_workspace`.

### Step Functions

Used for the Lambda Chain state machine.

```text
states:CreateStateMachine
states:DescribeStateMachine
states:DeleteStateMachine
```

## Cleanup and Scaffold Permissions

These permissions exist because the current destroy logic attempts to clean resources that may exist in the TwinMaker workspace, even though the current deploy flow does not create them.

```text
iottwinmaker:ListScenes
iottwinmaker:DeleteScene
```

The application does not create TwinMaker scenes. During `destroy`, `TwinmakerWorkspaceDeployer` lists and deletes scenes before deleting the workspace. This is defensive cleanup for externally-created or future scene resources.

## AWS-Dependent Permissions

These permissions are not direct Boto3 calls in the application code. They may be required by AWS while fulfilling the application-managed operations above.

### Managed Grafana Dependencies

Amazon Managed Grafana can require service-linked role, AWS IAM Identity Center, AWS Organizations, and EC2 describe permissions while creating or managing a workspace.

```text
iam:CreateServiceLinkedRole
sso:CreateManagedApplicationInstance
sso:DeleteManagedApplicationInstance
sso:DescribeRegisteredRegions
sso:GetSharedSsoConfiguration
organizations:DescribeOrganization
ec2:DescribeSecurityGroups
ec2:DescribeSubnets
ec2:GetManagedPrefixListEntries
```

These permissions are included because the application creates a Grafana workspace with AWS SSO authentication and customer-managed permissions.

## Full Practical Policy

The following policy is intended for the IAM principal whose access keys are stored in `config_credentials.json`.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "Identity",
      "Effect": "Allow",
      "Action": ["sts:GetCallerIdentity"],
      "Resource": "*"
    },
    {
      "Sid": "IamManagement",
      "Effect": "Allow",
      "Action": [
        "iam:CreateRole",
        "iam:GetRole",
        "iam:UpdateAssumeRolePolicy",
        "iam:PutRolePolicy",
        "iam:DeleteRolePolicy",
        "iam:AttachRolePolicy",
        "iam:DetachRolePolicy",
        "iam:ListAttachedRolePolicies",
        "iam:ListRolePolicies",
        "iam:ListInstanceProfilesForRole",
        "iam:RemoveRoleFromInstanceProfile",
        "iam:DeleteRole",
        "iam:CreateServiceLinkedRole"
      ],
      "Resource": "*"
    },
    {
      "Sid": "PassRolesToManagedServices",
      "Effect": "Allow",
      "Action": ["iam:PassRole"],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "iam:PassedToService": [
            "lambda.amazonaws.com",
            "states.amazonaws.com",
            "iottwinmaker.amazonaws.com",
            "grafana.amazonaws.com"
          ]
        }
      }
    },
    {
      "Sid": "Lambda",
      "Effect": "Allow",
      "Action": [
        "lambda:CreateFunction",
        "lambda:GetFunction",
        "lambda:GetPolicy",
        "lambda:DeleteFunction",
        "lambda:AddPermission",
        "lambda:RemovePermission"
      ],
      "Resource": "*"
    },
    {
      "Sid": "IoT",
      "Effect": "Allow",
      "Action": [
        "iot:CreateThing",
        "iot:DescribeThing",
        "iot:DeleteThing",
        "iot:CreateKeysAndCertificate",
        "iot:UpdateCertificate",
        "iot:DeleteCertificate",
        "iot:CreatePolicy",
        "iot:DeletePolicy",
        "iot:DeletePolicyVersion",
        "iot:ListPolicyVersions",
        "iot:AttachPolicy",
        "iot:DetachPolicy",
        "iot:AttachThingPrincipal",
        "iot:DetachThingPrincipal",
        "iot:ListThingPrincipals",
        "iot:ListAttachedPolicies",
        "iot:CreateTopicRule",
        "iot:GetTopicRule",
        "iot:ListTopicRules",
        "iot:DeleteTopicRule",
        "iot:Publish"
      ],
      "Resource": "*"
    },
    {
      "Sid": "EventBridge",
      "Effect": "Allow",
      "Action": [
        "events:PutRule",
        "events:DescribeRule",
        "events:DeleteRule",
        "events:PutTargets",
        "events:ListTargetsByRule",
        "events:RemoveTargets"
      ],
      "Resource": "*"
    },
    {
      "Sid": "DynamoDB",
      "Effect": "Allow",
      "Action": [
        "dynamodb:CreateTable",
        "dynamodb:DescribeTable",
        "dynamodb:DeleteTable",
        "dynamodb:CreateBackup",
        "dynamodb:DescribeBackup"
      ],
      "Resource": "*"
    },
    {
      "Sid": "S3",
      "Effect": "Allow",
      "Action": [
        "s3:CreateBucket",
        "s3:PutBucketCORS",
        "s3:GetBucketLocation",
        "s3:ListBucket",
        "s3:ListBucketVersions",
        "s3:DeleteObject",
        "s3:DeleteObjectVersion",
        "s3:DeleteBucket"
      ],
      "Resource": "*"
    },
    {
      "Sid": "IoTTwinMaker",
      "Effect": "Allow",
      "Action": [
        "iottwinmaker:CreateWorkspace",
        "iottwinmaker:GetWorkspace",
        "iottwinmaker:DeleteWorkspace",
        "iottwinmaker:CreateComponentType",
        "iottwinmaker:GetComponentType",
        "iottwinmaker:DeleteComponentType",
        "iottwinmaker:ListComponentTypes",
        "iottwinmaker:CreateEntity",
        "iottwinmaker:GetEntity",
        "iottwinmaker:UpdateEntity",
        "iottwinmaker:DeleteEntity",
        "iottwinmaker:ListEntities",
        "iottwinmaker:ListScenes",
        "iottwinmaker:DeleteScene"
      ],
      "Resource": "*"
    },
    {
      "Sid": "GrafanaAndDependencies",
      "Effect": "Allow",
      "Action": [
        "grafana:CreateWorkspace",
        "grafana:DescribeWorkspace",
        "grafana:DeleteWorkspace",
        "grafana:ListWorkspaces",
        "grafana:TagResource",
        "sso:CreateManagedApplicationInstance",
        "sso:DeleteManagedApplicationInstance",
        "sso:DescribeRegisteredRegions",
        "sso:GetSharedSsoConfiguration",
        "organizations:DescribeOrganization",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeSubnets",
        "ec2:GetManagedPrefixListEntries"
      ],
      "Resource": "*"
    },
    {
      "Sid": "StepFunctions",
      "Effect": "Allow",
      "Action": [
        "states:CreateStateMachine",
        "states:DescribeStateMachine",
        "states:DeleteStateMachine"
      ],
      "Resource": "*"
    }
  ]
}
```

## Runtime Role Policies Created by the Application

The permissions above are for the deployment principal. During deployment, the application creates runtime roles and attaches AWS managed or inline policies to those roles. Those runtime policies are not required directly on the deployment principal, except that the principal needs IAM permissions to create and attach them.

Managed policies attached by the application:

```text
arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
arn:aws:iam::aws:policy/service-role/AWSLambdaRole
```

`AWSLambdaBasicExecutionRole` (CloudWatch Logs) is attached to every runtime role. `AWSLambdaRole` (`lambda:InvokeFunction` on all functions) is attached only to the Dispatcher, LambdaChain, and per-device Processor roles, which invoke a downstream Lambda whose exact name isn't fixed at role-creation time. No runtime role uses an AWS-managed `*FullAccess`/`*ReadOnlyAccess`/`*DataAccess` policy — each role that needs DynamoDB, S3, IoT TwinMaker, Lambda, or Step Functions access gets a scoped inline policy instead (see below). This replaced an earlier version of this document/implementation where several roles held `AmazonDynamoDBFullAccess_v2`, `AWSLambda_ReadOnlyAccess`, `AWSStepFunctionsFullAccess`, `AWSIoTDataAccess`, and `AmazonS3FullAccess` — a source-level audit (see the ICSA evaluation, `EVALUATION.md` in the bundle root) found these granted far more than the corresponding Lambda's own source code ever calls.

### Inline Runtime Policies (Scoped)

Each policy is scoped to only the resources that role's Lambda (or, for TwinMaker/Grafana, AWS service) actually calls, using ARN builders in `src/deployers/aws/core/aws_arns.py`.

| Role | Grants | Scoped to |
|---|---|---|
| Persister | `dynamodb:PutItem`; `lambda:InvokeFunction` | this twin's Hot table; the Event-Checker Lambda |
| Event-Checker | `iottwinmaker:GetPropertyValueHistory`/`GetPropertyValue`; `lambda:GetFunction`/`InvokeFunction`; `states:StartExecution` | this twin's TwinMaker workspace; this twin's own `{digitalTwinName}-*` Lambda functions; this twin's LambdaChain state machine |
| TwinMaker service role | `s3:GetObject`/`PutObject`/`DeleteObject`/`ListBucket`; `lambda:InvokeFunction` | this twin's TwinMaker S3 bucket; the Hot Reader Lambda |
| Hot Reader | `dynamodb:Query`; `iottwinmaker:GetEntity` | this twin's Hot table; this twin's TwinMaker workspace |
| Hot-to-Cold Mover | `dynamodb:Query`/`BatchWriteItem`; `s3:PutObject` | this twin's Hot table; this twin's Cold bucket |
| Cold-to-Archive Mover | `s3:ListBucket`/`GetObject`/`DeleteObject` (source); `s3:PutObject` (target) | this twin's Cold bucket; this twin's Archive bucket |
| Event-Feedback | `iot:Publish` | every MQTT feedback topic found in `config_events.json` at deploy time (enumerated, not wildcarded) |
| Grafana execution role | `s3:GetObject`; `iottwinmaker:Get*`/`List*`; `iottwinmaker:ListWorkspaces` | this twin's TwinMaker S3 bucket; this twin's TwinMaker workspace; `Resource:"*"` (see exception below) |

Two statements are intentionally broader than "this twin's own resources" and are documented exceptions, not leftover over-broad grants:

- **Grafana's `iottwinmaker:ListWorkspaces` on `Resource:"*"`** — this is AWS's own documented requirement for the `grafana-iot-twinmaker-app` plugin (a List-level action that can't be scoped to one workspace; see [AWS's dashboard IAM role guide](https://docs.aws.amazon.com/iot-twinmaker/latest/guide/dashboard-IAM-role.html)), not an oversight. The rest of that role's policy matches AWS's documented "no video permissions" template. Grafana deployment is disabled by default via `deploy_managed_grafana`.
- There is deliberately **no third exception for cross-twin federation.** The repo has a "FunctionRegistry" SSM-registry lookup in Event-Checker (`lookup_registry()` in `lambda_functions/core/event-checker/lambda_function.py`, merged from elsewhere — see git history) that lets one twin invoke another twin's Lambda/Step Function. This scoping fix intentionally removed the `ssm:GetParameter` permission that supported it, since federation is out of scope for the current evaluation. The runtime code still *attempts* the SSM call unconditionally (`SSM_REGISTRY_PREFIX` is always set), but its failure is caught by a broad exception handler and falls back to normal local invocation — so this shows up as a harmless `AccessDenied` line in CloudWatch Logs on every action, not a functional break. If federation is needed again, re-adding a scoped `ssm:GetParameter` statement and a bounded federation-target exception is a follow-up, not part of this fix.

### Reconciliation caveat

None of these roles' `plan()` methods compare policy *content* — only the role *name*. A policy-content change in code only takes effect the next time a role is freshly created; it does not retrofit an already-deployed role with the same name. To apply a scoped policy to an existing twin, `destroy` and `deploy` that twin's core IAM roles (or the whole twin).

## Notes

- `Version: "2012-10-17"` in the JSON policy is the IAM policy language version, not an application version or policy creation date.
- CloudWatch Logs permissions are attached to runtime Lambda roles through `AWSLambdaBasicExecutionRole`; the deployment principal does not call CloudWatch Logs directly.
- If Grafana is removed from Core L5, the Grafana and AWS SSO dependent permissions can be removed from the deployment principal.
- If TwinMaker scene cleanup is removed from `TwinmakerWorkspaceDeployer.destroy`, `iottwinmaker:ListScenes` and `iottwinmaker:DeleteScene` can be removed.
