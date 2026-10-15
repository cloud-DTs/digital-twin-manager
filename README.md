## Usage
- The Digital Twin can be configured through the configuration files.
- The Digital Twin can be deployed with the `deploy` command.
- The Digital Twin can be destroyed with the `destroy` command.
- With the `info` command you can retrieve information about the Digital Twin cloud resources.

Run `plan`, then `apply`, to update an existing deployment. For every manager-owned Lambda (core, device processors and internal Event Actions), `plan` compares a reproducible ZIP hash with AWS `CodeSha256` and checks the function settings. Code or settings changes use `UPDATE` actions that keep the function ARN. The ZIP hash includes generated configuration files. Hot Reader planning also checks its IAM policy and can update that policy without replacing the role.

Before changing any resource, `apply` checks the planned Lambda packages, settings and AWS revisions, including `NO_CHANGE` actions. If they changed after planning, run `plan` again. Updates use `RevisionId`, wait for AWS completion and verify the deployed hash and settings before processing dependent resources. External Event Action Lambdas are not managed. Functions deployed with the previous ZIP packaging can require one initial code update. Saved plans without the new Lambda metadata must be regenerated.

MQTT Event Feedback planning compares the role's `EventFeedbackScopedAccess` policy in AWS with the configured topics. Topic changes update that policy without replacing the role. Adding the first MQTT feedback creates the policy; removing the last one deletes it. Before `apply` changes any resource, it checks the planned topic policy against the current configuration and the saved AWS policy snapshot. Create a new plan if either changed, or if the saved plan lacks Event Feedback policy metadata.

The Hot Reader supports both shared Component Types with an `iotDeviceId` property and legacy per-device types without that property. Legacy reads check the Component Type schema before deriving the device ID from its name. A shared type with a missing device ID produces an error. The role policy update grants `iottwinmaker:GetComponentType` for this check. Deployer credentials need `iam:GetRolePolicy`, `lambda:UpdateFunctionCode` and `lambda:UpdateFunctionConfiguration`; see [AWS permissions](docs/aws-permissions.md). No code hash needs to be added to `init-state`.

A hierarchy component can reference a managed type through its full `componentTypeId` alone. When that type maps to exactly one configured IoT device, the hierarchy deployer fills its native `iotDeviceId` value. A type shared by multiple devices requires an explicit `iotDeviceId`; configuration validation rejects an ambiguous reference. Run `plan`, then `apply`, to repair missing or incorrect inferred values on existing components through `UPDATE`. This preserves the entities and their other properties. Apply validates the planned inferred bindings for `DEPLOY` and `UPDATE` before changing resources. Updates also verify the saved AWS values and wait for the updated values before recording completion. Saved hierarchy deployment plans without binding metadata require a new `plan`. Legacy types without the native property and external types retain their existing behavior.

## Conventions
- Every deployer should be implemented in its own file.
- Keep components separated, self-contained, and independent.
  Each deploy entity should only be aware of itself. While this is not always achievable, it should be aimed for whenever possible.
- Every Digital Twin resource name should be prefixed with the Digital Twin name.
  This gives all Digital Twin resources a dedicated namespace and makes them clearly distinguishable from unrelated resources in the AWS account.

## Future Ideas
- Improve the handling of constant values. This is less about the deployer itself and more about establishing a consistent mechanism for managing constants across the Digital Twin.
- Possibly remove processor Lambda functions, or refactor them so the processor does not directly invoke the persister.
- Use pagination in Boto3 calls to handle large result sets.
- Testing system or unit tests.
- Recovery mechanism for failed deployments. For example, store the point of failure and provide a `deploy_continue` option to resume.
- Redeployment strategy. For example, when configuration changes, how should the system destroy the old state and deploy the new state?
- Group IAM role deployments to speed up deployment (reducing propagation delays). But keep in mind that this may introduce coupling and reduce the self-contained design.
