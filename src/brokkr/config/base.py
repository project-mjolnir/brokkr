"""
Baseline hiearchical configuration setup functions for Brokkr.
"""

# Standard library imports
import collections
import copy
import os
from pathlib import Path

# Third party imports
import toml

# Local imports
import brokkr.utils.misc


# General static constants
CONFIG_EXTENSION = "toml"
DEFAULT_CONFIG_DIR = Path().home() / ".config" / "brokkr"
LOCAL_OVERRIDE = "local_override"

ConfigType = collections.namedtuple(
    'ConfigType', ("include_sections", "default", "local"))

DEFAULT_CONFIG_TYPES = {
    "default": ConfigType(True, True, False),
    "global": ConfigType(False, False, False),
    "network": ConfigType("network", False, False),
    "site": ConfigType("site", False, False),
    "override": ConfigType(False, False, False),
    "local": ConfigType(True, False, True),
    }


def get_config_path(config_file, config_dir=DEFAULT_CONFIG_DIR):
    if "." not in config_file:
        config_file += ("." + CONFIG_EXTENSION)
    return Path(config_dir) / config_file


class ConfigHandler:
    name = None
    defaults = None
    path_variables = None
    config_types = None
    write_sections = None
    config_dir = None

    def __init__(self,
                 name,
                 defaults,
                 path_variables=(),
                 config_types=DEFAULT_CONFIG_TYPES,
                 write_sections=True,
                 config_dir=DEFAULT_CONFIG_DIR,
                 ):
        self.name = name
        self.defaults = defaults
        self.path_variables = path_variables
        self.config_types = config_types
        self.write_sections = write_sections
        self.config_dir = Path(config_dir)

    def get_config_path(self, config_name):
        if self.name not in config_name:
            config_name = "_".join((self.name, config_name))
        return get_config_path(config_name, self.config_dir)

    def write_config_data(self, config_name, config_data=None):
        if config_data is None:
            config_data = self.defaults
        os.makedirs(self.config_dir, exist_ok=True)
        with open(self.get_config_path(config_name), mode="w",
                  encoding="utf-8", newline="\n") as config_file:
            return toml.dump(config_data, config_file)

    def generate_config(self, config_name):
        config_data = {}
        include_sections = self.config_types[config_name].include_sections
        if include_sections is True:
            config_data = copy.deepcopy(self.defaults)
        elif not (self.write_sections and include_sections):
            pass
        elif include_sections in self.config_types.keys():
            config_data[include_sections] = copy.deepcopy(
                self.defaults[include_sections])
        else:
            for section in include_sections:
                config_data[section] = copy.deepcopy(
                    self.defaults[section])
        return self.write_config_data(config_name, config_data=config_data)

    def read_config(self, config_name):
        if self.config_types[config_name].default:
            return copy.deepcopy(self.defaults)
        try:
            initial_config = toml.load(self.get_config_path(config_name))
        # Generate config_name file if it does not yet exist.
        except FileNotFoundError:
            initial_config = toml.loads(self.generate_config(config_name))
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
                    not self.config_types[config_name].local
                    or configs[config_name].get(LOCAL_OVERRIDE)):
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
                del rendered_config[LOCAL_OVERRIDE]
            except Exception:  # Ignore if key isn't present
                pass
        return rendered_config
