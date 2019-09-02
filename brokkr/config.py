"""
Baseline configuration for Brokkr plus tools and utilities.
"""

# Standard library imports
import collections.abc
import copy
import datetime
import os
from pathlib import Path

# Third party imports
import toml


# General static constants
CONFIG_EXTENSION = "toml"
CONFIG_DIR = Path().home() / ".config" / "brokkr"
CONFIG_HIEARCHY = ("default", "global", "network", "site", "override", "local")
OUTPUT_PATH = Path("~") / "data"

DEFAULT_CONFIG = {
    "override": False,
    "verbose": False,
    "general": {
        "name_prefix": "hamma",
        "sensor_ip": "10.10.10.1",
        "output_path": str(OUTPUT_PATH).replace(os.sep, "/")
        },
    "monitor": {
        "interval_s": 60,
        "output_path": str(OUTPUT_PATH / "monitoring").replace(os.sep, "/"),
        "sensor": {
            "ping_timeout_s": 1,
            },
        "sunsaver": {
            "pid_list": [24597, ],
            "port": "",
            "start_offset": 0x0008,
            "unit": 0x01,
            },
        },
    "network": {
        "name": "test",
        "longname": "Test Network (Default)",
        },
    "site": {
        "number": "",
        "description": "Test Sensor (Default)",
        "network": "test",
        },
    }

PATH_VARIABLES = (("general", "output_path"), ("monitor", "output_path"))


def get_config_path(config_file, config_dir=CONFIG_DIR):
    if "." not in config_file:
        config_file += ("." + CONFIG_EXTENSION)
    return Path(config_dir) / config_file


def write_config_file(config_file, config_dir=CONFIG_DIR,
                      config_data=DEFAULT_CONFIG):
    os.makedirs(config_dir, exist_ok=True)
    with open(get_config_path(config_file, config_dir), "w",
              encoding="utf-8", newline="\n") as cfg_f:
        return toml.dump(config_data, cfg_f)


def generate_config_file(config_file, include_section="auto",
                         config_dir=CONFIG_DIR):
    if not include_section:
        config_data = {}
    elif include_section == "all" or (
            include_section == "auto" and config_file in {"local", "default"}):
        config_data = copy.deepcopy(DEFAULT_CONFIG)
    elif include_section == "auto":
        try:
            config_data = {
                config_file: copy.deepcopy(DEFAULT_CONFIG[config_file])}
        # Ignore config file name that doesn't match a config section
        except KeyError:
            config_data = {}
    else:
        config_data = {copy.deepcopy(DEFAULT_CONFIG[include_section])}
    return write_config_file(config_file, config_dir=config_dir,
                             config_data=config_data)


def read_config_file(config_file, config_dir=CONFIG_DIR):
    if config_file == "default":
        return copy.deepcopy(DEFAULT_CONFIG)
    try:
        initial_config = toml.load(get_config_path(config_file, config_dir))
    # Generate config file if it does not yet exist.
    except FileNotFoundError:
        print(f"{datetime.datetime.utcnow()!s} "
              f"Could not find existing {config_file} config file in "
              f"{config_dir}; creating a fresh one.")
        initial_config = toml.loads(
            generate_config_file(config_file, config_dir=config_dir))
    return initial_config


def update_dict_recursive(base, update):
    for update_key, update_value in update.items():
        base_value = base.get(update_key, {})
        if not isinstance(base_value, collections.abc.Mapping):
            base[update_key] = update_value
        elif isinstance(update_value, collections.abc.Mapping):
            base[update_key] = update_dict_recursive(
                base_value, update_value)
        else:
            base[update_key] = update_value
    return base


def render_config(config):
    rendered_config = copy.deepcopy(config[CONFIG_HIEARCHY[0]])
    for config_level in CONFIG_HIEARCHY[1:]:
        if config[config_level] and (
                config_level != "local" or config[config_level]["override"]):
            rendered_config = update_dict_recursive(rendered_config,
                                                    config[config_level])
    for key_name in PATH_VARIABLES:
        inner_dict = rendered_config
        for key in key_name[:-1]:
            inner_dict = inner_dict[key]
        inner_dict[key_name[-1]] = Path(inner_dict[key_name[-1]]).expanduser()
    return rendered_config


def setup_config():
    config = {}
    for config_name in CONFIG_HIEARCHY:
        config[config_name] = read_config_file(config_name)
    rendered_config = render_config(config)
    config["initial"] = rendered_config
    config["permenant"] = copy.deepcopy(rendered_config)
    config["current"] = copy.deepcopy(rendered_config)
    return config


# Master config dict; currently static
CONFIGS = setup_config()
CONFIG = CONFIGS["current"]
