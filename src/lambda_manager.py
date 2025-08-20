import globals
import util


def update_function(function_name, local_function_name, environment=None):
  if local_function_name == "default-processor":
    compiled_function = util.compile_lambda_function(local_function_name)

    for iot_device in globals.config_iot_devices:
      function_name = globals.config.get("general", "digital_twin_name") + "-" + iot_device["name"] + "-processor"

      globals.aws_lambda_client.update_function_code(
        FunctionName=function_name,
        ZipFile=compiled_function,
        Publish=True
      )

      waiter = globals.aws_lambda_client.get_waiter("function_updated")
      waiter.wait(FunctionName=function_name)

      if environment is not None:
        globals.aws_lambda_client.update_function_configuration(
          FunctionName=function_name,
          Environment=environment
        )

      print(f"Updated Lambda Function: {function_name}")

    return

  globals.aws_lambda_client.update_function_code(
    FunctionName=function_name,
    ZipFile=util.compile_lambda_function(local_function_name),
    Publish=True
  )

  waiter = globals.aws_lambda_client.get_waiter("function_updated")
  waiter.wait(FunctionName=function_name)

  if environment is not None:
    globals.aws_lambda_client.update_function_configuration(
      FunctionName=function_name,
      Environment=environment
    )

  print(f"Updated Lambda Function: {function_name}")


def fetch_logs(function_name, n=10, filter_system_logs=True):
  log_group = f"/aws/lambda/{function_name}"

  streams = globals.aws_logs_client.describe_log_streams( logGroupName=log_group, orderBy="LastEventTime", descending=True, limit=1)
  latest_stream = streams["logStreams"][0]["logStreamName"]

  events = globals.aws_logs_client.get_log_events(logGroupName=log_group, logStreamName=latest_stream, limit=n, startFromHead=False)
  messages = [e["message"] for e in events["events"]][-n:]

  if not filter_system_logs:
    return messages
  else:
    system_prefixes = ("INIT_START", "START", "END", "REPORT")
    return [message for message in messages if not message.startswith(system_prefixes)]
