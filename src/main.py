import argparse
import os
import sys

import globals
import deployers.aws.core.all
import deployers.aws.iot.all
import deployers.aws.hierarchy.all
import deployers.aws.event_actions.all
import deployers.aws.init_values.all
import deployers.aws.all
import deployment_state
import generate_federation
import sanity_checker
import validation
from dependency_graph.dependency_analyzer import analyze_plan_dependencies
from dependency_graph.loader import load_template_graph
from dependency_graph.runtime_graph_builder import build_runtime_graph

def help_menu():
  print("""
    Available commands:
      deploy                       - Deploys core and IoT services and resources.
      destroy                      - Destroys core and IoT services and resources.
      info                         - Lists all the deployed resources.
      plan                         - Plans core resource changes without modifying AWS.
      apply                        - Loads and sorts saved plan actions for apply.
      init-state                   - Copies current deploy config files into redeployment state.
      help                         - Show this help menu.
      exit                         - Exit the program.
  """)


def _print_missing_state_help(error):
  print(error)
  print(
    "Start with 'init-state' if the AWS resources already exist, "
    "or 'deploy' if this is a fresh deployment."
  )


def _try_initialize_last_applied_config_state():
  try:
    deployment_state.initialize_last_applied_config_state()
    return True
  except FileNotFoundError as error:
    _print_missing_state_help(error)
    return False


def _dependency_template_path():
  return os.path.join(globals.project_path(), "dependency", "template.json")


def _build_previous_dependency_graph(template_graph):
  return build_runtime_graph(
    template_graph,
    deployment_state.last_applied_config,
    deployment_state.last_applied_config_iot_devices,
    deployment_state.last_applied_config_events,
    deployment_state.last_applied_config_hierarchy,
  )


def _build_desired_dependency_graph(template_graph):
  return build_runtime_graph(
    template_graph,
    globals.config,
    globals.config_iot_devices,
    globals.config_events,
    globals.config_hierarchy,
  )


def _analyze_plan_dependencies(plan_groups):
  template_graph = load_template_graph(_dependency_template_path())
  previous_graph = _build_previous_dependency_graph(template_graph)
  desired_graph = _build_desired_dependency_graph(template_graph)
  return analyze_plan_dependencies(previous_graph, desired_graph, plan_groups)


def _blocked_plan_actions(plan_groups):
  for group in plan_groups:
    group_name = group.get("group", "<unknown group>")

    for layer in group.get("layers", []):
      layer_name = layer.get("layer", "<unknown layer>")

      for action in layer.get("actions", []):
        if action.get("blocked", False):
          yield group_name, layer_name, action


def _print_plan_blockers(plan_groups):
  blocked_actions = list(_blocked_plan_actions(plan_groups))

  if not blocked_actions:
    return

  print(f"Blocked plan actions: {len(blocked_actions)}")

  for group_name, layer_name, action in blocked_actions:
    graph_id = action.get("graph_id") or "<missing graph_id>"
    resource_type = action.get("resource_type") or "<unknown resource_type>"
    resource = action.get("resource") or "<unknown resource>"
    action_name = action.get("action") or "<unknown action>"

    print(
      f"- {group_name}/{layer_name}: "
      f"{action_name} {resource_type}/{resource} [{graph_id}]"
    )

    for blocker in action.get("blockers", []):
      print(f"  - {blocker}")


CONFIG_ARGUMENTS = {
  "config": "config.json",
  "iot_devices": "config_iot_devices.json",
  "events": "config_events.json",
  "hierarchy": "config_hierarchy.json",
  "providers": "config_providers.json",
}

COMMANDS = ["deploy", "destroy", "info", "plan", "apply", "init-state", "help"]


def parse_arguments():
  parser = argparse.ArgumentParser(description="Digital Twin Manager")
  parser.add_argument("command", nargs="?", choices=COMMANDS,
                      help="Command to run once. Without a command the interactive shell starts.")
  parser.add_argument("--config", help="Path to config.json")
  parser.add_argument("--iot_devices", help="Path to config_iot_devices.json")
  parser.add_argument("--events", help="Path to config_events.json")
  parser.add_argument("--hierarchy", help="Path to config_hierarchy.json")
  parser.add_argument("--providers", help="Path to config_providers.json")
  parser.add_argument("--state", help="State folder")
  parser.add_argument("--plan", help="Path to plan.json")
  parser.add_argument("--pems", help="Folder for the IoT device certificates")
  parser.add_argument("--output", help="Folder for the federation input file")
  return parser.parse_args()


def apply_path_arguments(args):
  config_files = {
    file_name: getattr(args, argument)
    for argument, file_name in CONFIG_ARGUMENTS.items()
    if getattr(args, argument)
  }
  if config_files:
    original_config_path = globals.config_path
    globals.config_path = lambda file_name: config_files.get(file_name) or original_config_path(file_name)

  if args.state:
    os.environ[deployment_state.STATE_DIR_ENV] = args.state

  if args.plan:
    plan_path = args.plan
    os.makedirs(os.path.dirname(os.path.abspath(plan_path)), exist_ok=True)
    deployment_state.state_plan_file_path = lambda: plan_path

  if args.pems:
    os.makedirs(args.pems, exist_ok=True)
    globals.iot_data_path = args.pems


  if args.output:
    os.makedirs(args.output, exist_ok=True)
    os.chdir(args.output)


def initialize():

    globals.initialize_config()
    globals.initialize_config_iot_devices()
    globals.initialize_config_credentials()
    globals.initialize_config_events()
    globals.initialize_config_hierarchy()
    globals.initialize_config_providers()
    validation.validate_all_configs(
      globals.config,
      globals.config_credentials,
      globals.config_events,
      globals.config_hierarchy,
      globals.config_iot_devices,
      globals.config_providers,
    )
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
    _try_initialize_last_applied_config_state()


def run_command(command):
  """Runs one command. Returns False if the command could not be carried out."""
  if command == "deploy":
    sanity_checker.check()
    deployers.aws.core.all.AllDeployer().deploy()
    deployers.aws.iot.all.AllDeployer().deploy()
    deployers.aws.hierarchy.all.AllDeployer().deploy()
    deployers.aws.event_actions.all.AllDeployer().deploy()
    deployers.aws.init_values.all.AllDeployer().deploy()
    deployment_state.save_last_applied_config_state()
    print(f"State configs saved to: {deployment_state.state_config_dir_path()}")
    generate_federation.generate_federation_input()

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

  elif command == "plan":
    sanity_checker.check()
    if not _try_initialize_last_applied_config_state():
      return False

    plan_groups = [deployers.aws.core.all.AllDeployer().plan(), deployers.aws.iot.all.AllDeployer().plan(),
                   deployers.aws.hierarchy.all.AllDeployer().plan(),
                   deployers.aws.event_actions.all.AllDeployer().plan(),
                   deployers.aws.init_values.all.AllDeployer().plan()]

    plan_groups = _analyze_plan_dependencies(plan_groups)
    _print_plan_blockers(plan_groups)

    plan_path = deployment_state.save_plan(plan_groups)
    print(f"Plan saved to: {plan_path}")

  elif command == "apply":
    if not _try_initialize_last_applied_config_state():
      return False

    plan = deployment_state.load_plan()

    if not plan:
      print("No saved plan found. Run 'plan' first.")
      return False

    print(f"Loaded plan from: {deployment_state.state_plan_file_path()}")
    deployers.aws.all.AllDeployer().apply(plan)
    deployment_state.save_last_applied_config_state()
    print(f"State configs saved to: {deployment_state.state_config_dir_path()}")
    generate_federation.generate_federation_input()

  elif command == "init-state":
    sanity_checker.check()
    deployment_state.save_last_applied_config_state()
    print(f"Redeployment state configs saved to: {deployment_state.state_config_dir_path()}")

  elif command == "help":
    help_menu()

  else:
    print(f"Unknown command: {command}. Type 'help' for a list of commands.")
    return False

  return True


def interactive_shell():
  print("Welcome to the Digital Twin Manager. Type 'help' for commands.")

  while True:
    try:
      user_input = input(">>> ").strip()
    except (EOFError, KeyboardInterrupt):
      print("Goodbye!")
      break

    if not user_input:
      continue

    command = user_input.split()[0]

    if command == "exit":
      print("Goodbye!")
      break

    run_command(command)


def main():
  args = parse_arguments()
  apply_path_arguments(args)
  initialize()

  if args.command is None:
    interactive_shell()
    return

  sys.exit(0 if run_command(args.command) else 1)


if __name__ == "__main__":
  main()