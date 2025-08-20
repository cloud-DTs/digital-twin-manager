import globals
import core_services
import info
import iot_services

def help_menu():
  print("""
    Available commands:
      deploy                 - Deploys core and IoT services and resources.
      destroy                - Destroys core and IoT services and resources.
      deploy_core            - Deploys core services and resources.
      destroy_core           - Destroys core services and resources.
      deploy_iot             - Deploys services and resources for every specified iot device.
      destroy_iot            - Deploys services and resources for every specified iot device.
      info                   - Lists all the deployed resources.
      info_l1(-l5)           - Lists the deployed resources for the given layer.
      help                   - Show this help menu.
      exit                   - Exit the program.
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

      if command == "deploy":
        core_services.deploy()
        iot_services.deploy()
      elif command == "destroy":
        core_services.destroy()
        iot_services.destroy()
      elif command == "deploy_core":
        core_services.deploy()
      elif command == "destroy_core":
        core_services.destroy()
      elif command == "deploy_iot":
        iot_services.deploy()
      elif command == "destroy_iot":
        iot_services.destroy()
      elif command == "info":
        info.check()
      elif command == "info_l1":
        info.check_l1()
      elif command == "info_l2":
        info.check_l2()
      elif command == "info_l3":
        info.check_l3()
      elif command == "info_l4":
        info.check_l4()
      elif command == "info_l5":
        info.check_l5()
      elif command == "help":
        help_menu()
      elif command == "exit":
        print("Goodbye!")
        break
      else:
        print(f"Unknown command: {command}. Type 'help' for a list of commands.")

if __name__ == "__main__":
  main()
