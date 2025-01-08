"""
Common utilities for the USPTO Patents Processing Python project

This module provides common utilities for the USPTO Patents Processing Python project. It includes functions to load configuration files, load application keys, and load modules dynamically.

Todos:
- Add more functions for common utilities.
- Add more error handling and logging.
- Add more documentation.
- Add monitoring and alerting
"""
import importlib.util
import json
import logging
import os
import socket
import sys

from pathlib import Path

class EnvTools:
    @staticmethod
    def find_repo_root():
        current_path = Path.cwd()
        while current_path != current_path.parent:
            if (current_path / '.git').exists():
                return current_path
            current_path = current_path.parent
        return None

    @staticmethod
    def get_hostname():
        return socket.gethostname()

    @staticmethod
    def load_settings(json_file, file_path=None):
        if file_path is None:
            repo_root = EnvTools.find_repo_root()
            if repo_root is None:
                logging.critical("Repository root not found.")
                return None
            file_path = repo_root / json_file
        else:
            file_path = file_path / json_file

        # Check if the configuration file exists, then load it
        if not os.path.exists(file_path):
            logging.debug(f"Settings file {file_path} not found at {file_path}")
            return None

        with open(file_path, 'r') as file:
            config = json.load(file)

        def remove_comments(d):
            if isinstance(d, dict):
                return {k: remove_comments(v) for k, v in d.items() if not k.startswith('_comment')}
            return d

        return remove_comments(config)

    @staticmethod
    def load_workspace_module(module_parent, module_name):
        # Calculate the absolute path to the Modules directory
        module_path = module_parent / 'workspace_packages'

        logging.debug(f"Modules Path: {module_path}")

        # Add the Modules directory to the sys.path
        sys.path.append(module_path)

        # Check if the module file exists
        module_file_path = os.path.join(module_path, f'{module_name}.py')
        if not os.path.exists(module_file_path):
            logging.error(f"Module {module_name}.py not found in the Modules directory")
            return None
        else:
            # Load the module dynamically
            spec = importlib.util.spec_from_file_location(module_name, module_file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module

def main():
    env_tools = EnvTools()

    print(f"Hostname: {env_tools.get_hostname()}")
    print(f"Repository Root: {env_tools.find_repo_root()}")
    print(f"Settings: {env_tools.load_settings('config.json')}")

if __name__ == '__main__':
    main()

#
# The following method works for the sub-projects like {repo}/{sub-project}
#
# Determine the grandparent directory dynamically
#current_file_path = Path(__file__).resolve()
#parent_dir = current_file_path.parents[1]
#grandparent_dir = current_file_path.parents[2]
# directories = [parent_dir, grandparent_dir]
# Define the path to the configuration file
#config_path = directories / 'config.json'

# Add explicit path for Pylance
#sys.path.append(f"{folder}/packages")
