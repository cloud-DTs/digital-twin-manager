import boto3
import os
import json
import datetime


DIGITAL_TWIN_INFO = json.loads(os.environ.get("DIGITAL_TWIN_INFO", None))
SOURCE_S3_BUCKET_NAME = os.environ.get("SOURCE_S3_BUCKET_NAME", None)
TARGET_S3_BUCKET_NAME = os.environ.get("TARGET_S3_BUCKET_NAME", None)

s3_client = boto3.client("s3")

cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=DIGITAL_TWIN_INFO["config"]["cold_storage_size_in_days"])
cutoff_iso = cutoff.isoformat(timespec='milliseconds').replace('+00:00', 'Z')


def lambda_handler(event, context):
    print("Hello from Cold To Archive Mover!")
    print("Event: " + json.dumps(event))

    paginator = s3_client.get_paginator("list_objects_v2")

    for page in paginator.paginate(Bucket=SOURCE_S3_BUCKET_NAME):
        if "Contents" not in page:
            continue

        for obj in page["Contents"]:
            key = obj["Key"]
            last_modified = obj["LastModified"]

            if last_modified < cutoff:
                s3_client.copy_object(
                    CopySource={"Bucket": SOURCE_S3_BUCKET_NAME, "Key": key},
                    Bucket=TARGET_S3_BUCKET_NAME,
                    Key=key,
                    StorageClass="DEEP_ARCHIVE",
                    MetadataDirective="COPY"
                )

                s3_client.delete_object(Bucket=SOURCE_S3_BUCKET_NAME, Key=key)

                print(f"Moved {key} from {SOURCE_S3_BUCKET_NAME} to {TARGET_S3_BUCKET_NAME}")
