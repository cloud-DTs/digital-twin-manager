from deployers.base import Deployer
from datetime import datetime, timezone
import time
import globals
import util
from botocore.exceptions import ClientError

class HotDynamodbTableDeployer(Deployer):
  def log(self, message):
    print(f"Core: {message}")

  def deploy(self):
    table_name = globals.hot_dynamodb_table_name()

    globals.aws_dynamodb_client.create_table(
      TableName=table_name,
      KeySchema=[
        {'AttributeName': 'iotDeviceId', 'KeyType': 'HASH'},  # partition key
        {'AttributeName': 'id', 'KeyType': 'RANGE'}           # sort key
      ],
      AttributeDefinitions=[
        {'AttributeName': 'iotDeviceId', 'AttributeType': 'S'},
        {'AttributeName': 'id', 'AttributeType': 'S'}
      ],
      BillingMode='PAY_PER_REQUEST'
    )

    self.log(f"Creation of DynamoDb table initiated: {table_name}")

    waiter = globals.aws_dynamodb_client.get_waiter('table_exists')
    waiter.wait(TableName=table_name)

    self.log(f"Created DynamoDb table: {table_name}")

  def destroy(self):
    table_name = globals.hot_dynamodb_table_name()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    backup_name = f"{table_name}-backup-{timestamp}"

    try:
      response = globals.aws_dynamodb_client.create_backup(TableName=table_name, BackupName=backup_name)
    except ClientError as e:
      if e.response["Error"]["Code"] == "TableNotFoundException":
        return
      else:
        raise

    backup_arn = response["BackupDetails"]["BackupArn"]
    self.log(f"Backup of DynamoDb table initiated: {backup_name}, {backup_arn}")

    while True:
      response_d = globals.aws_dynamodb_client.describe_backup(BackupArn=backup_arn)
      status = response_d["BackupDescription"]["BackupDetails"]["BackupStatus"]

      if status == "AVAILABLE" or status == "ACTIVE":
        break

      time.sleep(5)

    self.log("Backup creation of DynamoDb table succeeded.")

    globals.aws_dynamodb_client.delete_table(TableName=table_name)
    self.log(f"Deletion of DynamoDb table initiated: {table_name}")

    waiter = globals.aws_dynamodb_client.get_waiter("table_not_exists")
    waiter.wait(TableName=table_name)

    self.log(f"Deleted DynamoDb table: {table_name}")

  def info(self):
    table_name = globals.hot_dynamodb_table_name()

    try:
      globals.aws_dynamodb_client.describe_table(TableName=table_name)
      self.log(f"✅ DynamoDb Table exists: {util.link_to_dynamodb_table(table_name)}")
    except ClientError as e:
      if e.response["Error"]["Code"] == "ResourceNotFoundException":
        self.log(f"❌ DynamoDb Table missing: {table_name}")
      else:
        raise
