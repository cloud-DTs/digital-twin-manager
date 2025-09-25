import json
import globals
import core_services
import info
import iot_services
import lambda_manager

def help_menu():
  print("""
    Available commands:
      deploy                                                            - Deploys core and IoT services and resources.
      destroy                                                           - Destroys core and IoT services and resources.
      info                                                              - Lists all the deployed resources.
      config_events_updated                                             - Redeploys the events.
      lambda_update <local_function_name> <o:environment>               - Deploys a new version of the specified lambda function.
      lambda_logs <local_function_name> <o:n> <o:filter_system_logs>    - Fetches the last n logged messages of the specified lambda function.
      help                                                              - Show this help menu.
      exit                                                              - Exit the program.
  """)

def main():
    globals.initialize_config()
    globals.initialize_config_iot_devices()
    globals.initialize_config_credentials()
    globals.initialize_config_events()
    globals.initialize_config_hierarchy()
    globals.initialize_aws_iam_client()
    globals.initialize_aws_lambda_client()
    globals.initialize_aws_iot_client()
    globals.initialize_aws_sts_client()
    globals.initialize_aws_events_client()
    globals.initialize_aws_dynamodb_client()
    globals.initialize_aws_s3_client()
    globals.initialize_aws_twinmaker_client()
    globals.initialize_aws_grafana_client()
    globals.initialize_aws_logs_client()

    print("Welcome to the Digital Twin Manager. Type 'help' for commands.")

    while True:
      try:
        user_input = input(">>> ").strip()
      except (EOFError, KeyboardInterrupt):
        print("Goodbye!")
        break

      if not user_input:
        continue

      parts = user_input.split()
      command = parts[0]
      args = parts[1:]

      if command == "deploy":
        core_services.deploy()
        iot_services.deploy()
      elif command == "destroy":
        iot_services.destroy()
        core_services.destroy()
      elif command == "info":
        info.check()
      elif command == "config_events_updated":
        core_services.config_events_updated()
      elif command == "lambda_update":
        if len(args) > 1:
          lambda_manager.update_function(args[0], json.loads(args[1]))
        else:
          lambda_manager.update_function(args[0])
      elif command == "lambda_logs":
        if len(args) > 2:
          print("".join(lambda_manager.fetch_logs(args[0], int(args[1]), args[2].lower() in ("true", "1", "yes", "y"))))
        elif len(args) > 1:
          print("".join(lambda_manager.fetch_logs(args[0], int(args[1]))))
        else:
          print("".join(lambda_manager.fetch_logs(args[0])))
      elif command == "lambda_invoke":
        if len(args) > 2:
          lambda_manager.invoke_function(args[0], json.loads(args[1]), args[2].lower() in ("true", "1", "yes", "y"))
        elif len(args) > 1:
          lambda_manager.invoke_function(args[0], json.loads(args[1]))
        else:
          lambda_manager.invoke_function(args[0])
      elif command == "help":
        help_menu()

        core_services.destroy_cold_archive_mover_lambda_function()
        core_services.create_cold_archive_mover_lambda_function()
      elif command == "exit":
        print("Goodbye!")
        break
      else:
        print(f"Unknown command: {command}. Type 'help' for a list of commands.")

if __name__ == "__main__":
  main()
