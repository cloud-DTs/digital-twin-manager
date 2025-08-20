import configparser
import os

config_path = "config.ini"
auth_files_path = ""

config = {}

def project_path():
  return os.path.dirname(os.path.dirname(__file__))

def initialize_config():
  global config
  config = configparser.ConfigParser()
  config.read(os.path.join(project_path(), config_path))
