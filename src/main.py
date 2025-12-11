import globals
import deployers.aws.core.all
import deployers.aws.iot.all
import deployers.aws.hierarchy.all
import deployers.aws.event_actions.all
import deployers.aws.init_values.all
import sanity_checker

def help_menu():
  print("""
    Available commands:
      deploy                       - Deploys core and IoT services and resources.
      destroy                      - Destroys core and IoT services and resources.
      info                         - Lists all the deployed resources.
      help                         - Show this help menu.
      exit                         - Exit the program.
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
        deployers.aws.core.all.AllDeployer().deploy()
        deployers.aws.iot.all.AllDeployer().deploy()
        deployers.aws.hierarchy.all.AllDeployer().deploy()
        deployers.aws.event_actions.all.AllDeployer().deploy()
        deployers.aws.init_values.all.AllDeployer().deploy()

      elif command == "destroy":
        deployers.aws.init_values.all.AllDeployer().destroy()
        deployers.aws.event_actions.all.AllDeployer().destroy()
        deployers.aws.hierarchy.all.AllDeployer().destroy()
        deployers.aws.iot.all.AllDeployer().destroy()
        deployers.aws.core.all.AllDeployer().destroy()

      elif command == "info":
        deployers.aws.core.all.AllDeployer().info()
        deployers.aws.iot.all.AllDeployer().info()
        deployers.aws.hierarchy.all.AllDeployer().info()
        deployers.aws.event_actions.all.AllDeployer().info()
        deployers.aws.init_values.all.AllDeployer().info()

      elif command == "help":
        help_menu()

      elif command == "exit":
        print("Goodbye!")
        break

      else:
        print(f"Unknown command: {command}. Type 'help' for a list of commands.")

if __name__ == "__main__":
  main()
