import globals
import core_services
import info
import iot_services

def help_menu():
  print("""depl
    Available commands:
      deploy_core            - Deploys core services and resources (workspaces etc.)
      destroy_core           - Destroys core services and resources (workspaces etc.)
      add_iot_device_type    - Deploys services and resources for a new iot device type (TwinMaker connecter etc.)
      add_iot_device         - Deploys services and resources for a new iot device entity (IoT thing etc.)
      help                   - Show this help menu
      exit                   - Exit the program
  """)

def main():
    globals.initialize_config()
    globals.initialize_config_iot_devices()
    globals.initialize_aws_iam_client()
    globals.initialize_aws_lambda_client()
    globals.initialize_aws_iot_client()
    globals.initialize_aws_sts_client()
    globals.initialize_aws_events_client()
    globals.initialize_aws_dynamodb_client()
    globals.initialize_aws_s3_client()
    globals.initialize_aws_twinmaker_client()
    globals.initialize_aws_grafana_client()

    print("Welcome to the Digital Twin Manager. Type 'help' for commands.")

    while True:
      try:
        user_input = input(">>> ").strip()
      except (EOFError, KeyboardInterrupt):
        print("\nExiting.")
        break

      if not user_input:
        continue

      parts = user_input.split()
      command = parts[0]
      args = parts[1:]

      if command == "deploy_core":
        core_services.deploy()
      elif command == "destroy_core":
        core_services.destroy()
      elif command == "deploy_iot":
        iot_services.deploy()
      elif command == "destroy_iot":
        iot_services.destroy()
      elif command == "info":
        info.check()
      elif command == "help":
        help_menu()
      elif command == "exit":
        print("Goodbye!")
        break
      else:
        print(f"Unknown command: {command}. Type 'help' for a list of commands.")

if __name__ == "__main__":
  main()
