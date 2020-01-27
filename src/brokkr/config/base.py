"""
Baseline hiearchical configuration setup functions for Brokkr.
"""

# Standard library imports
import copy
import json
import os
from pathlib import Path

# Third party imports
import toml

# Local imports
import brokkr.utils.cli
import brokkr.utils.misc


# General static constants
TYPE_DEFAULTS = "defaults"
TYPE_FILE = "file"
TYPE_ENV_VARS = "environment_variables"
TYPE_CLI_ARGS = "cli_arguments"

DEFAULT_CONFIG_DIR = Path().home() / ".config" / "brokkr"
OVERRIDE_CONFIG = "override_config"
VERSION_KEY = "config_version"
EMPTY_CONFIG = ("config_is_empty", True)


# Configuration level presets
CONFIG_PRESETS = {
    "defaults": {"source": {"type": TYPE_DEFAULTS}, "include_defaults": True},
    "remote": {"source": {"type": TYPE_FILE, "extension": "json"}},
    "local": {"source": {"type": TYPE_FILE, "extension": "toml"}},
    "override": {"source": {"type": TYPE_FILE, "extension": "toml"},
                 "include_defaults": True, "override": True},
    "env_vars": {"source": {"type": TYPE_ENV_VARS}},
    "cli_args": {"source": {"type": TYPE_CLI_ARGS}},
    }


# Python 3.7: Replace with a dataclass
class ConfigLevel:
    def __init__(
            self,
            name,
            source,
            include_defaults=False,
            override=False,
            ):
        self.name = name
        self.source = source
        self.include_defaults = include_defaults
        self.override = override


class ConfigHandler:
    def _setup_config_levels(self, config_levels):
        output_config_levels = {}
        for config_level in config_levels:
            if not isinstance(config_level, ConfigLevel):
                config_level = ConfigLevel(
                    config_level,
                    **copy.deepcopy(CONFIG_PRESETS[config_level]),
                    )

            if config_level.source["type"] == TYPE_FILE:
                config_path = config_level.source.get("path", self.config_dir)
                config_name = config_level.name
                if self.name not in config_name:
                    config_name = "_".join((self.name, config_name))
                if (config_name.split(".")[-1]
                        != config_level.source["extension"]):
                    config_name += ("." + config_level.source["extension"])
                config_level.source["path"] = Path(config_path / config_name)
            elif (config_level.source["type"] in {TYPE_ENV_VARS, TYPE_CLI_ARGS}
                  and config_level.source.get("mapping", None) is None):
                getattr(self, config_level.source["type"])
                config_level.source["mapping"] = getattr(
                    self, config_level.source["type"])

            output_config_levels[config_level.name] = config_level
        return output_config_levels

    def __init__(
            self,
            name,
            defaults=None,
            config_levels=("default", "local"),
            config_dir=DEFAULT_CONFIG_DIR,
            config_version=None,
            path_variables=None,
            environment_variables=None,
            cli_arguments=None,
            ):
        self.name = name
        self.defaults = defaults if defaults is not None else {}
        self.config_dir = Path(config_dir)
        self.config_version = config_version
        self.path_variables = (
            path_variables if path_variables is not None else [])
        self.environment_variables = environment_variables
        self.cli_arguments = cli_arguments

        # Set up preset config levels
        self.config_levels = self._setup_config_levels(config_levels)

    def write_config(self, config_name, config_data):
        config_level = self.config_levels[config_name]
        if config_level.source["type"] != TYPE_FILE:
            return None
        os.makedirs(config_level.source["path"].parent, exist_ok=True)
        with open(config_level.source["path"], mode="w",
                  encoding="utf-8", newline="\n") as config_file:
            if config_level.source["extension"] == "toml":
                toml.dump(config_data, config_file)
            elif config_level.source["extension"] == "json":
                json.dump(config_data, config_file,
                          allow_nan=False, separators=(",", ":"))
        return config_level.source["path"]

    def generate_config(self, config_name, config_data=None):
        config_level = self.config_levels[config_name]
        if config_data is None:
            config_data = (
                self.defaults if config_level.include_defaults else {})
        if self.config_levels[config_name].override:
            config_data[OVERRIDE_CONFIG] = {
                **{OVERRIDE_CONFIG: False}, **config_data}
        if self.config_version is not None:
            config_data = {**{VERSION_KEY: self.config_version}, **config_data}
        # Prevent JSON errors from serializing/deserializing empty dict
        if not config_data and config_level.source["type"] == TYPE_FILE:
            config_data = {EMPTY_CONFIG[0]: EMPTY_CONFIG[1]}

        self.write_config(config_name, config_data)
        return config_data

    def _read_config_mapping(self, source):
        initial_config = {}
        if source["type"] == TYPE_ENV_VARS:
            args = os.environ
        elif source["type"] == TYPE_CLI_ARGS:
            args = vars(brokkr.utils.cli.generate_argparser_main()
                        .parse_args())
        for src_key, config_keys in source["mapping"].items():
            config_value = args.get(src_key, None)

            # Recursively set config keys
            if config_value is not None:
                inner_dict = initial_config
                for config_section in config_keys[:-1]:
                    try:
                        inner_dict = inner_dict[config_section]
                    except KeyError:
                        inner_dict[config_section] = {}
                        inner_dict = inner_dict[config_section]
                inner_dict[config_keys[-1]] = config_value

        return initial_config

    def _read_config_file(self, source):
        if source["extension"] == "toml":
            initial_config = toml.load(source["path"])
        elif source["extension"] == "json":
            with open(source["path"], mode="r",
                      encoding="utf-8") as config_file:
                initial_config = json.load(config_file)

        # Delete empty config key, added to avoid unreadable empty JSONs
        try:
            del initial_config[EMPTY_CONFIG[0]]
        except KeyError:
            pass

        return initial_config

    def read_config(self, config_name):
        config_level = self.config_levels[config_name]
        if config_level.source["type"] == TYPE_DEFAULTS:
            initial_config = copy.deepcopy(self.defaults)
        elif config_level.source["type"] in {TYPE_ENV_VARS, TYPE_CLI_ARGS}:
            initial_config = self._read_config_mapping(config_level.source)
        elif config_level.source["type"] == TYPE_FILE:
            try:
                initial_config = self._read_config_file(config_level.source)
            # Generate or ignore config_name file if it does not yet exist
            except FileNotFoundError:
                if config_level.source.get("create", True):
                    self.generate_config(config_name)
                    initial_config = self._read_config_file(
                        config_level.source)
                else:
                    initial_config = {}

        return initial_config

    def read_configs(self, config_names=None):
        configs = {}
        if config_names is None:
            config_names = self.config_levels.keys()
        for config_name in config_names:
            configs[config_name] = self.read_config(config_name)
        return configs

    def render_config(self, configs=None, remove_override=False):
        if configs is None:
            configs = self.read_configs()

        # Recursively build final config dict from succession of loaded configs
        rendered_config = copy.deepcopy(
            configs[list(self.config_levels.keys())[0]])
        for config_name in list(self.config_levels.keys())[1:]:
            if configs[config_name] and (
                    not self.config_levels[config_name].override
                    or configs[config_name].get(OVERRIDE_CONFIG)):
                rendered_config = brokkr.utils.misc.update_dict_recursive(
                    rendered_config, configs[config_name])

        # Format string paths as pathlib paths with username expanded
        for key_name in self.path_variables:
            inner_dict = rendered_config
            for key in key_name[:-1]:
                inner_dict = inner_dict[key]
            inner_dict[key_name[-1]] = Path(
                inner_dict[key_name[-1]]).expanduser()

        # Remove key specifying whether to override the config from the result
        if remove_override:
            try:
                del rendered_config[OVERRIDE_CONFIG]
            except Exception:  # Ignore if key isn't present
                pass
        return rendered_config
