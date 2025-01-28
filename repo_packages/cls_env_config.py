from cls_env_tools import EnvTools
from json import load

import os
import threading

class EnvConfigSingleton:
    _instance = None
    _lock = threading.Lock()  # For thread safety

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if not cls._instance:
                cls._instance = super(EnvConfigSingleton, cls).__new__(cls, *args, **kwargs)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # Initialize the configuration settings here
        self._load_env_config()
        self._initialized = True

    def _load_env_config(self):
        hostname = EnvTools.get_hostname()

        self._config = EnvTools.load_settings('config.json')

        # Load local config file if it exists which should have settings specific to the local machine
        local_config_file = f'config.{hostname}.json'
        self._local_config = EnvTools.load_settings(local_config_file)
        if self._local_config is not None:
            self._merge_dicts(self._config, self._local_config)

        # Load app keys which might be property values or a relative path to a key file
        self._app_keys = EnvTools.load_settings('app_keys.json')
        if self._app_keys is not None:
            self._merge_dicts(self._config, self._app_keys)

        # Optionally load from environment variables
        self._repo_root = EnvTools.find_repo_root()
        self._workspace_root = os.getenv('WORKSPACE_ROOT', None)
        #self.config["DEBUG_MODE"] = os.getenv("DEBUG_MODE", str(self.config["DEBUG_MODE"])).lower() in ['true', '1', 't']

    def _merge_dicts(self, base, updates):
        for key, value in updates.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                self._merge_dicts(base[key], value)
            else:
                base[key] = value

    @property
    def merged_config(self):
        return self._config

    @property
    def repo_root(self):
        return self._repo_root

    @property
    def workspace_root(self):
        return self._workspace_root

    def get(self, key, default=None):
        return self.merged_config.get(key, default)

    def set(self, key, value):
        self.merged_config[key] = value

    def app_key(self, app_key, key):
        return self.merged_config['keys'][app_key][key]

    def app_keys(self, app_keys):
        return self.merged_config['keys'][app_keys]

    def all_app_keys(self):
        return self.merged_config['keys']

    def get_source_psycopg2_params(self, server_alias="source", database="postgres"):
        pgSourceKey = self.merged_config['pgServers'][server_alias]
        pgsql_params = self.merged_config['pgConnStrs'][pgSourceKey][database].copy()
        pgsql_params.pop('database', None)  # Remove 'database' key if it exists
        #pgsql_params['password'] = self.merged_config['pgPwds'][pgSourceKey][database]['password']
        return pgsql_params

    def get_source_asyncpg_params(self, server_alias="source", database="postgres"):
        pgSourceKey = self.merged_config['pgServers'][server_alias]
        pgsql_params = self.merged_config['pgConnStrs'][pgSourceKey][database].copy()
        pgsql_params.pop('dbname', None)  # Remove 'database' key if it exists
        #pgsql_params['password'] = self.merged_config['pgPwds'][pgSourceKey][database]['password']
        return pgsql_params

    def get_target_psycopg2_params(self, server_alias="target", database="postgres"):
        pgTargetKey = self.merged_config['pgServers'][server_alias]
        if pgTargetKey is None or pgTargetKey == '':
            raise ValueError('No targetPostgresDev key found in config.json')
        pgsql_params = self.merged_config['pgConnStrs'][pgTargetKey][database].copy()
        pgsql_params.pop('database', None)
        #pgsql_params['password'] = self._app_keys['pgPwds'][pgTargetKey][database]['password']
        return pgsql_params

import json

# Usage example
if __name__ == "__main__":
    config1 = EnvConfigSingleton()
    config2 = EnvConfigSingleton()

    # Both variables should reference the same instance
    assert config1 is config2

    print("\nRepository root: ", config1.repo_root)
    print("Workspace root: ", config1.workspace_root)

    # Setting a value in one instance affects the other
    config1.set("NEW_SETTING", "value")
    print("\nNEW_SETTING", config2.get("NEW_SETTING"))  # Output: value

    if (config1.get("keys") is not None):
        print("\nAll Keys\n", config1.all_app_keys())

    print("\nSource asynpg Postgres: ", config1.get_source_asyncpg_params("postgres"))
    print("Source psycopg2 Postgres: ", config1.get_source_psycopg2_params("postgres"))
    print("Target psycopg2 Postgres: ", config1.get_target_psycopg2_params_prod("postgres"))

    print("\nFull merged config: ", json.dumps(config1.merged_config, indent=2))
