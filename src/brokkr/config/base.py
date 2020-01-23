"""
Baseline hiearchical configuration setup functions for Brokkr.
"""

# Standard library imports
import collections
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

ConfigType = collections.namedtuple(
    'ConfigType', ("include_default", "override", "extension"))

DEFAULT_CONFIG_TYPES = {
    "default": ConfigType(
        include_default=True, override=False, extension=None),
    "remote": ConfigType(
        include_default=False, override=False, extension="json"),
    "local": ConfigType(
        include_default=True, override=True, extension="toml"),
    }


class ConfigHandler:

    def __init__(self,
                 name,
                 defaults=None,
                 path_variables=(),
                 config_types=DEFAULT_CONFIG_TYPES,
                 config_dir=DEFAULT_CONFIG_DIR,
                 config_version=None,
                 ):
        self.name = name
        self.defaults = defaults
        self.path_variables = path_variables
        self.config_types = config_types
        self.config_dir = Path(config_dir)
        self.config_version = config_version

        if self.defaults is None:
            self.defaults = {}

    def get_config_path(self, config_name):
        config_extension = self.config_types[config_name].extension
        if config_extension is None:
            return None
        if self.name not in config_name:
            config_name = "_".join((self.name, config_name))
        if "." not in config_name:
            config_name += ("." + config_extension)
        return Path(self.config_dir) / config_name

    def write_config_data(self, config_name, config_data=None):
        config_extension = self.config_types[config_name].extension
        if config_extension is None:
            return
        if config_data is None:
            config_data = self.defaults
        elif (not config_data and self.config_version is None
              and config_extension == "json"):
            config_data = {EMPTY_CONFIG[0]: EMPTY_CONFIG[1]}

        if self.config_version is not None:
            config_data = {**{VERSION_KEY: self.config_version}, **config_data}

        os.makedirs(self.config_dir, exist_ok=True)
        with open(self.get_config_path(config_name), mode="w",
                  encoding="utf-8", newline="\n") as config_file:
            if config_extension == "toml":
                toml.dump(config_data, config_file)
            elif config_extension == "json":
                json.dump(config_data, config_file,
                          allow_nan=False, separators=(",", ":"))

    def generate_config(self, config_name):
        config_data = {}
        if self.config_types[config_name].include_default:
            config_data = self.defaults
        if self.config_types[config_name].override:
            config_data[OVERRIDE_CONFIG] = False
        self.write_config_data(config_name, config_data=config_data)
        return config_data

    def read_config(self, config_name):
        config_extension = self.config_types[config_name].extension
        if config_extension is None:
            return copy.deepcopy(self.defaults)
        try:
            if config_extension == "toml":
                initial_config = toml.load(self.get_config_path(config_name))
            elif config_extension == "json":
                with open(self.get_config_path(config_name), mode="r",
                          encoding="utf-8") as config_file:
                    initial_config = json.load(config_file)
        # Generate config_name file if it does not yet exist.
        except FileNotFoundError:
            initial_config = self.generate_config(config_name)
        # Delete empty config key if found to avoid unreadable empty JSONs
        try:
            del initial_config[EMPTY_CONFIG[0]]
        except KeyError:
            pass
        return initial_config

    def read_configs(self, config_names=None):
        configs = {}
        if config_names is None:
            config_names = self.config_types.keys()
        for config_name in config_names:
            configs[config_name] = self.read_config(config_name)
        return configs

    def render_config(self, configs, remove_override=False):
        rendered_config = copy.deepcopy(
            configs[list(self.config_types.keys())[0]])
        for config_name in list(self.config_types.keys())[1:]:
            if configs[config_name] and (
                    not self.config_types[config_name].override
                    or configs[config_name].get(OVERRIDE_CONFIG)):
                rendered_config = brokkr.utils.misc.update_dict_recursive(
                    rendered_config, configs[config_name])
        for key_name in self.path_variables:
            inner_dict = rendered_config
            for key in key_name[:-1]:
                inner_dict = inner_dict[key]
            inner_dict[key_name[-1]] = Path(
                inner_dict[key_name[-1]]).expanduser()
        if remove_override:
            try:
                del rendered_config[OVERRIDE_CONFIG]
            except Exception:  # Ignore if key isn't present
                pass
        return rendered_config
