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
import brokkr.utils.misc


# General static constants
CONFIG_EXTENSIONS = ("toml", "json")
DEFAULT_CONFIG_DIR = Path().home() / ".config" / "brokkr"
OVERRIDE_CONFIG = "override_config"
VERSION_KEY = "config_version"
EMPTY_CONFIG = ("config_is_empty", True)


# Configuration level types
CONFIG_PRESETS = {
    "default": {"include_defaults": True, "extension": None},
    "remote": {"extension": "json"},
    "local": {},
    "override": {"include_defaults": True, "override": True},
    }


# Python 3.7: Replace with a dataclass
class ConfigLevel:
    def __init__(
            self,
            name,
            append_name=True,
            extension="toml",
            path=None,
            include_defaults=False,
            override=False,
            managed=True
            ):
        if path is not None:
            path = Path(path)
        self.name = name
        self.append_name = append_name
        self.extension = extension
        self.path = path
        self.include_defaults = include_defaults
        self.override = override
        self.managed = managed


class ConfigHandler:
    def __init__(
            self,
            name,
            defaults=None,
            config_levels=("default", "local"),
            config_dir=DEFAULT_CONFIG_DIR,
            config_version=None,
            path_variables=(),
            ):
        self.name = name
        self.defaults = defaults if defaults is not None else {}
        self.config_dir = Path(config_dir)
        self.config_version = config_version
        self.path_variables = path_variables

        # Set up preset config levels
        self.config_levels = {}
        for config_level in config_levels:
            if not isinstance(config_level, ConfigLevel):
                config_level = ConfigLevel(
                    config_level, **CONFIG_PRESETS[config_level])
            self.config_levels[config_level.name] = config_level

    def get_config_path(self, config_name):
        config_level = self.config_levels[config_name]
        if config_level.extension is None:
            return None
        config_path = (config_level.path if config_level.path is not None
                       else self.config_dir)
        if config_level.append_name and self.name not in config_name:
            config_name = "_".join((self.name, config_name))
        if config_name.split(".")[-1] != config_level.extension:
            config_name += ("." + config_level.extension)
        return Path(config_path / config_name)

    def write_config(self, config_name, config_data):
        config_path_full = self.get_config_path(config_name)
        os.makedirs(config_path_full.parent, exist_ok=True)
        with open(config_path_full, mode="w",
                  encoding="utf-8", newline="\n") as config_file:
            if self.config_levels[config_name].extension == "toml":
                toml.dump(config_data, config_file)
            elif self.config_levels[config_name].extension == "json":
                json.dump(config_data, config_file,
                          allow_nan=False, separators=(",", ":"))
        return config_path_full

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
        if not config_data:
            config_data = {EMPTY_CONFIG[0]: EMPTY_CONFIG[1]}

        self.write_config(config_name, config_data)
        return config_data

    def read_config(self, config_name):
        config_level = self.config_levels[config_name]
        if config_level.extension is None:
            return copy.deepcopy(self.defaults)
        try:
            if config_level.extension == "toml":
                initial_config = toml.load(self.get_config_path(config_name))
            elif config_level.extension == "json":
                with open(self.get_config_path(config_name), mode="r",
                          encoding="utf-8") as config_file:
                    initial_config = json.load(config_file)
        # Generate or ignore config_name file if it does not yet exist
        except FileNotFoundError:
            if config_level.managed:
                initial_config = self.generate_config(config_name)
            else:
                initial_config = {}

        # Delete empty config key, added to avoid unreadable empty JSONs
        try:
            del initial_config[EMPTY_CONFIG[0]]
        except KeyError:
            pass
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
