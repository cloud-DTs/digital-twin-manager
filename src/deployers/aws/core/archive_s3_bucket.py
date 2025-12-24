from deployers.base import Deployer
import globals
import util
from botocore.exceptions import ClientError

class ArchiveS3BucketDeployer(Deployer):
  def log(self, message):
    print(f"Core: {message}")

  def deploy(self):
    bucket_name = globals.archive_s3_bucket_name()

    globals.aws_s3_client.create_bucket(
      Bucket=bucket_name,
      CreateBucketConfiguration={
          "LocationConstraint": globals.aws_s3_client.meta.region_name
      }
    )

    self.log(f"Created S3 Bucket: {bucket_name}")

  def destroy(self):
    bucket_name = globals.archive_s3_bucket_name()

    if util.destroy_s3_bucket(bucket_name):
      self.log(f"Deleted S3 bucket: {bucket_name}")

  def info(self):
    bucket_name = globals.archive_s3_bucket_name()

    try:
      globals.aws_s3_client.head_bucket(Bucket=bucket_name)
      self.log(f"✅ Archive S3 Bucket exists: {util.link_to_s3_bucket(bucket_name)}")
    except ClientError as e:
      if int(e.response["Error"]["Code"]) == 404:
        self.log(f"❌ Archive S3 Bucket missing: {bucket_name}")
      else:
        raise
