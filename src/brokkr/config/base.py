
"""
Baseline hierarchical configuration setup functions for Brokkr.
"""

# Standard library imports
import abc
import argparse
import copy
import json
import os
from pathlib import Path

# Third party imports
import toml

# Local imports
from brokkr.constants import (
    LEVEL_NAME_LOCAL,
    LEVEL_NAME_REMOTE,
    LEVEL_NAME_SYSTEM,
    LEVEL_NAME_SYSTEM_CLIENT,
    )
import brokkr.utils.misc


# General static constants
DEFAULT_CONFIG_TYPE_NAME = "config"
LEVEL_NAME_DEFAULTS = "defaults"
LEVEL_NAME_FILE = "local"
LEVEL_NAME_ENV_VARS = "env_vars"
LEVEL_NAME_CLI_ARGS = "cli_args"
LEVEL_NAME_OVERLAY = "overlay"

EXTENSION_TOML = "toml"
EXTENSION_JSON = "json"
SUPPORTED_EXTENSIONS = [EXTENSION_TOML, EXTENSION_JSON]

VERSION_KEY = "config_version"
EMPTY_CONFIG = ("config_is_empty", True)
JSON_SEPERATORS = (",", ":")
CONFIG_VERSION_DEFAULT = 1

LEVEL_CLASS = "level_class"
LEVEL_ARGS = "level_args"


def convert_paths(config_data, path_variables):
    # Format string paths as pathlib paths with username expanded
    for key_name in path_variables:
        inner_dict = config_data
        try:
            for key in key_name[:-1]:
                inner_dict = inner_dict[key]
            inner_dict[key_name[-1]] = brokkr.utils.misc.convert_path(
                inner_dict[key_name[-1]])
        # Ignore missing keys
        except KeyError:
            continue
    return config_data


class ConfigType(brokkr.utils.misc.AutoReprMixin):
    def __init__(
            self,
            name,
            defaults=None,
            overlay=None,
            local_config_path=None,
            preset_config_path=None,
            path_variables=None,
            config_version=CONFIG_VERSION_DEFAULT,
                ):
        self.name = name
        self.defaults = {} if defaults is None else defaults
        self.overlay = overlay
        self.local_config_path = (
            None if local_config_path is None else Path(local_config_path))
        self.preset_config_path = (
            None if preset_config_path is None else Path(preset_config_path))
        self.path_variables = [] if path_variables is None else path_variables
        self.config_version = config_version


class ConfigLevel(brokkr.utils.misc.AutoReprMixin, metaclass=abc.ABCMeta):
    def __init__(
            self,
            name,
            config_type=None,
                ):
        self.name = name
        self.config_type = (ConfigType(DEFAULT_CONFIG_TYPE_NAME)
                            if config_type is None else config_type)

    def generate_config(self):
        if self.config_type.config_version is not None:
            config_data = {VERSION_KEY: self.config_type.config_version}
        else:
            config_data = {}
        return config_data

    @abc.abstractmethod
    def read_config(self, input_data=None):
        config_data = convert_paths(
            input_data, self.config_type.path_variables)
        return config_data


class WritableConfigLevel(ConfigLevel, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def write_config(self, config_data=None):
        pass


class DefaultsConfigLevel(ConfigLevel):
    def __init__(self, name=LEVEL_NAME_DEFAULTS, **kwargs):
        super().__init__(name=name, **kwargs)

    def generate_config(self):
        config_data = super().generate_config()
        config_data = config_data.update(self.config_type.defaults)
        return config_data

    def read_config(self, input_data=None):
        if input_data is None:
            input_data = copy.deepcopy(self.config_type.defaults)
        else:
            input_data = copy.deepcopy(input_data)
        return super().read_config(input_data)


class FileConfigLevel(WritableConfigLevel):
    def __init__(
            self,
            name=LEVEL_NAME_FILE,
            extension=EXTENSION_TOML,
            preset=False,
            path=None,
            append_level=False,
            **kwargs,
                ):
        if extension not in SUPPORTED_EXTENSIONS:
            raise ValueError("Extension must be one of "
                             f"{SUPPORTED_EXTENSIONS}, not {extension}")

        super().__init__(name=name, **kwargs)
        self.extension = extension
        self.preset = preset

        # Setup full config path given defaults
        if path is not None:
            self.path = Path(path)
        elif self.preset:
            self.path = self.config_type.preset_config_path
        else:
            self.path = self.config_type.local_config_path

        # Generate filename and add to path if needed
        if self.path.suffix != self.extension:
            config_filename = self.config_type.name
            if append_level:
                config_filename = "_".join([config_filename, self.name])
            config_filename += ("." + self.extension)
            self.path = self.path / config_filename

    def read_config(self, input_data=None):
        if input_data is None:
            try:
                if self.extension == EXTENSION_TOML:
                    config_data = toml.load(self.path)
                elif self.extension == EXTENSION_JSON:
                    with open(self.path, "r", encoding="utf-8") as config_file:
                        config_data = json.load(config_file)

            # Generate or ignore config_name file if it does not yet exist
            except FileNotFoundError:
                if not self.preset:
                    config_data = self.write_config()
                else:
                    config_data = {}
        else:
            config_data = copy.deepcopy(input_data)

        # Delete empty config key, added to avoid unreadable empty JSONs
        try:
            del config_data[EMPTY_CONFIG[0]]
        except KeyError:
            pass

        config_data = super().read_config(config_data)
        return config_data

    def write_config(self, config_data=None):
        # Prevent JSON errors from serializing/deserializing empty dict
        if not config_data and self.extension == EXTENSION_JSON:
            config_data = {EMPTY_CONFIG[0]: EMPTY_CONFIG[1]}

        # Merge config data with generated baseline
        if not config_data:
            config_data = self.generate_config()
        else:
            config_data = {**self.generate_config(), **config_data}

        os.makedirs(self.path.parent, exist_ok=True)
        with open(self.path, mode="w",
                  encoding="utf-8", newline="\n") as config_file:
            if self.extension == EXTENSION_TOML:
                toml.dump(config_data, config_file)
            elif self.extension == EXTENSION_JSON:
                json.dump(config_data, config_file,
                          allow_nan=False, separators=JSON_SEPERATORS)
        return config_data


class MappingConfigLevel(ConfigLevel):
    def __init__(
            self,
            name,
            mapping,
            **kwargs,
                ):
        self.mapping = mapping
        super().__init__(name=name, **kwargs)

    def read_config(self, input_data=None):
        config_data = {}
        if input_data:
            for src_key, config_keys in self.mapping.items():
                config_value = input_data.get(src_key, None)
                # Recursively set config keys
                if config_value is not None:
                    inner_dict = config_data
                    for config_section in config_keys[:-1]:
                        try:
                            inner_dict = inner_dict[config_section]
                        except KeyError:
                            inner_dict[config_section] = {}
                            inner_dict = inner_dict[config_section]
                    inner_dict[config_keys[-1]] = config_value

        return super().read_config(config_data)


class EnvVarsConfigLevel(MappingConfigLevel):
    def __init__(self, name=LEVEL_NAME_ENV_VARS, mapping=None, **kwargs):
        super().__init__(name=name, mapping=mapping, **kwargs)

    def read_config(self, input_data=None):
        if input_data is None:
            input_data = os.environ
        config_data = super().read_config(input_data)
        return config_data


class CLIArgsConfigLevel(MappingConfigLevel):
    def __init__(self, name=LEVEL_NAME_CLI_ARGS, mapping=None, **kwargs):
        super().__init__(name=name, mapping=mapping, **kwargs)

    def read_config(self, input_data=None):
        if input_data is None:
            arg_parser = argparse.ArgumentParser(
                argument_default=argparse.SUPPRESS,
                usage=argparse.SUPPRESS,
                add_help=False,
                )
            for arg_name in self.mapping.keys():
                arg_parser.add_argument(f"--{arg_name.replace('_', '-')}")

            cli_args, __ = arg_parser.parse_known_args()
        else:
            input_data = cli_args

        # Convert to dict if cli_args is a namespace, ignoring errors
        try:
            cli_args = vars(cli_args)
        except TypeError:
            pass

        config_data = super().read_config(cli_args)
        return config_data


class ConfigHandler(brokkr.utils.misc.AutoReprMixin):
    def __init__(self, config_type=None, config_levels=None):
        self.config_type = (ConfigType(DEFAULT_CONFIG_TYPE_NAME)
                            if config_type is None else config_type)

        config_levels = [] if config_levels is None else config_levels
        self.config_levels = {}
        if (self.config_type.defaults is not None
                and not any([isinstance(config_level, DefaultsConfigLevel)
                             for config_level in config_levels])):
            defaults_config_level = DefaultsConfigLevel(
                config_type=self.config_type)
            config_levels = [defaults_config_level, *config_levels]
        for config_level in config_levels:
            self.config_levels[config_level.name] = config_level

    def read_configs(self, config_names=None):
        configs = {}
        if config_names is None:
            config_names = self.config_levels.keys()
        configs = {config_name: self.config_levels[config_name].read_config()
                   for config_name in config_names}
        if self.config_type.overlay is not None:
            configs[LEVEL_NAME_OVERLAY] = copy.deepcopy(
                self.config_type.overlay)
        return configs

    def render_config(self, configs=None):
        if configs is None:
            configs = self.read_configs()

        # Recursively build final config dict from succession of loaded configs
        rendered_config = copy.deepcopy(
            configs[list(configs.keys())[0]])
        for config_name in list(configs.keys())[1:]:
            if configs[config_name]:
                rendered_config = brokkr.utils.misc.update_dict_recursive(
                    rendered_config, configs[config_name])

        return rendered_config


CONFIG_LEVEL_PRESETS = {
    LEVEL_NAME_SYSTEM: {LEVEL_ARGS: {
        "preset": True}},
    LEVEL_NAME_SYSTEM_CLIENT: {LEVEL_ARGS: {
        "preset": True, "append_level": True}},
    LEVEL_NAME_REMOTE: {LEVEL_ARGS: {
        "extension": EXTENSION_JSON, "append_level": True}},
    LEVEL_NAME_LOCAL: {},
    }


class ConfigHandlerFactory(brokkr.utils.misc.AutoReprMixin):
    def __init__(
            self,
            level_presets=None,
            overlays=None,
            **default_type_kwargs,
                ):
        self.level_presets = (CONFIG_LEVEL_PRESETS if level_presets is None
                              else level_presets)
        self.overlays = overlays
        self.default_type_kwargs = default_type_kwargs

    def create_config_handler(self, name, config_levels, **type_kwargs):
        type_kwargs = {
            **self.default_type_kwargs,
            **{"overlay":
               None if self.overlays is None else self.overlays.get(name, {})},
            **type_kwargs,
            }
        config_type = ConfigType(name=name, **type_kwargs)

        rendered_config_levels = []
        for config_level in config_levels:
            if not isinstance(config_level, ConfigLevel):
                try:
                    level_preset = self.level_presets[config_level]
                except (KeyError, TypeError):
                    # If the level isn't in the preset dict or isn't a str
                    level_preset = config_level
                level_class = level_preset.get(LEVEL_CLASS, FileConfigLevel)
                level_args = level_preset.get(LEVEL_ARGS, {})
                # If the level was loaded from a preset, use the preset's name
                if level_preset != config_level:
                    level_args["name"] = level_args.get("name", config_level)
                config_level = level_class(
                    config_type=config_type, **level_args)
            rendered_config_levels.append(config_level)

        config_handler = ConfigHandler(config_type=config_type,
                                       config_levels=rendered_config_levels)
        return config_handler
