## Usage
- The Digital Twin can be configured through the configuration files.
- The Digital Twin can be deployed with the `deploy` command.
- The Digital Twin can be destroyed with the `destroy` command.
- With the `info` command you can retrieve information about the Digital Twin cloud resources.

## Code Explanation
- The core concept is a **deployer**. A deployer manages **deploy entities**, and each deploy entity is responsible for deploying, deleting, and retrieving information about a **resource entity**. A resource entity can represent one or more cloud resources (see example below).
- Configuration files are used to define parameters for deployers.
- The main function simply executes the `deploy`, `destroy`, or `info` function on all deployers based on user input.
- Deployer example:

## Conventions
- Every deployer should be implemented in its own file.
- Keep components separated, self-contained, and independent.
  Each deploy entity should only be aware of itself. While this is not always achievable, it should be aimed for whenever possible.
- Every Digital Twin resource name should be prefixed with the Digital Twin name.
  This gives all Digital Twin resources a dedicated namespace and makes them clearly distinguishable from unrelated resources in the AWS account.

## Future Ideas
- Use a single provider for layer 3. For AWS, consider using S3 lifecycle rules to transition hot → cold → archive data.
- Improve the handling of constant values. This is less about the deployer itself and more about establishing a consistent mechanism for managing constants across the Digital Twin.
- Possibly remove processor Lambda functions, or refactor them so the processor does not directly invoke the persister.
- Object-oriented design. Create a `Deployer` class.
- Testing system or unit tests.
- Recovery mechanism for failed deployments. For example, store the point of failure and provide a `deploy_continue` option to resume.
- Redeployment strategy. For example, when configuration changes, how should the system destroy the old state and deploy the new state?
- Group IAM role deployments to speed up deployment (reducing propagation delays). But keep in mind that this may introduce coupling and reduce the self-contained design.

## Deployer Example
```python
# deployer file

# deploy entity 1
def deploy_resource_1():
    ...

def destroy_resource_1():
    ...

def info_resource_1():
    ...


# deploy entity 2
def deploy_resource_2():
    ...

def destroy_resource_2():
    ...

def info_resource_2():
    ...


# deployer
def deploy():
    deploy_resource_1()
    deploy_resource_2()

def destroy():
    destroy_resource_2()
    destroy_resource_1()

def info():
    info_resource_1()
    info_resource_2()


def log(string):
    print(f"Deployer Name: " + string)
```
