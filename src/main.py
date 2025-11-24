import json
import globals
import deployers.core_deployer
import deployers.iot_deployer
import info
import deployers.hierarchy_deployer
import deployers.event_actions_deployer
import deployers.init_values_deployer
import sanity_checker

def help_menu():
  print("""
    Available commands:
      deploy                                                            - Deploys core and IoT services and resources.
      destroy                                                           - Destroys core and IoT services and resources.
      info                                                              - Lists all the deployed resources.
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
    globals.initialize_aws_sf_client()
    globals.initialize_aws_iot_data_client()

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
        sanity_checker.check()
        deployers.core_deployer.deploy()
        deployers.iot_deployer.deploy()
        deployers.hierarchy_deployer.deploy()
        deployers.event_actions_deployer.deploy()
        deployers.init_values_deployer.deploy()

      elif command == "destroy":
        deployers.init_values_deployer.destroy()
        deployers.event_actions_deployer.destroy()
        deployers.hierarchy_deployer.destroy()
        deployers.iot_deployer.destroy()
        deployers.core_deployer.destroy()

      elif command == "info":
        info.check()
        deployers.hierarchy_deployer.info()
        deployers.event_actions_deployer.info()
        deployers.init_values_deployer.info()

      elif command == "help":
        help_menu()

      elif command == "exit":
        print("Goodbye!")
        break

      else:
        print(f"Unknown command: {command}. Type 'help' for a list of commands.")

if __name__ == "__main__":
  main()
