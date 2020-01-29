"""
Baseline hiearchical configuration setup functions for Brokkr.
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
import brokkr.utils.misc


# General static constants
EXTENSION_TOML = "toml"
EXTENSION_JSON = "json"
SUPPORTED_EXTENSIONS = [EXTENSION_TOML, EXTENSION_JSON]

DEFAULT_CONFIG_PATH = Path().home() / ".config" / "brokkr"
VERSION_KEY = "config_version"
EMPTY_CONFIG = ("config_is_empty", True)
JSON_SEPERATORS = (",", ":")
CONFIG_VERSION = 1


def convert_paths(config_data, path_variables):
    # Format string paths as pathlib paths with username expanded
    for key_name in path_variables:
        inner_dict = config_data
        try:
            for key in key_name[:-1]:
                inner_dict = inner_dict[key]
            inner_dict[key_name[-1]] = Path(
                inner_dict[key_name[-1]]).expanduser()
        # Ignore missing keys
        except KeyError:
            continue
    return config_data


@brokkr.utils.misc.auto_repr(exclude=("handler",))
class ConfigSource(abc.ABC):
    def __init__(
            self,
            name,
            handler,
            ):
        self.name = name
        self.handler = handler

    def write_config(self, config_data=None):
        raise NotImplementedError("Cannot write this config level type")

    @abc.abstractmethod
    def read_config(self, config_data=None):
        config_data = convert_paths(config_data, self.handler.path_variables)
        return config_data

    def generate_config(self):
        if self.handler.config_version is not None:
            config_data = {VERSION_KEY: self.handler.config_version}
        else:
            config_data = {}
        return config_data


class DefaultsConfigSource(ConfigSource):
    def __init__(self, name, handler):
        super().__init__(name=name, handler=handler)

    def read_config(self):
        config_data = copy.deepcopy(self.handler.defaults)
        return super().read_config(config_data)

    def generate_config(self):
        config_data = super().generate_config()
        config_data = config_data.update(self.handler.defaults)
        return config_data


class FileConfigSource(ConfigSource):
    def __init__(
            self,
            name,
            handler,
            extension=EXTENSION_TOML,
            path=None,
            create=True,
            ):
        if extension not in SUPPORTED_EXTENSIONS:
            raise ValueError("Extension must be one of "
                             f"{SUPPORTED_EXTENSIONS}, not {extension}")

        self._extension = extension
        self._create = create
        super().__init__(name=name, handler=handler)

        # Setup full config path given defaults
        self._path = (Path(path) if path is not None
                      else self.handler.default_config_path)
        if not self._path.suffix == self._extension:
            config_name = "_".join((self.handler.name, self.name))
            config_name += ("." + self._extension)
            self._path = self._path / config_name

    def generate_config(self):
        config_data = super().generate_config()
        # Prevent JSON errors from serializing/deserializing empty dict
        if not config_data and self._extension == EXTENSION_JSON:
            config_data = {EMPTY_CONFIG[0]: EMPTY_CONFIG[1]}
        return config_data

    def write_config(self, config_data=None):
        if config_data is None:
            config_data = self.generate_config()
        os.makedirs(self._path.parent, exist_ok=True)
        with open(self._path, mode="w",
                  encoding="utf-8", newline="\n") as config_file:
            if self._extension == EXTENSION_TOML:
                toml.dump(config_data, config_file)
            elif self._extension == EXTENSION_JSON:
                json.dump(config_data, config_file,
                          allow_nan=False, separators=JSON_SEPERATORS)
        return config_data

    def read_config(self):
        try:
            if self._extension == EXTENSION_TOML:
                config_data = toml.load(self._path)
            elif self._extension == EXTENSION_JSON:
                with open(self._path, "r", encoding="utf-8") as config_file:
                    config_data = json.load(config_file)
        # Generate or ignore config_name file if it does not yet exist
        except FileNotFoundError:
            if self._create:
                config_data = self.write_config()
            else:
                config_data = {}

        # Delete empty config key, added to avoid unreadable empty JSONs
        try:
            del config_data[EMPTY_CONFIG[0]]
        except KeyError:
            pass

        config_data = super().read_config(config_data)
        return config_data


class MappingConfigSource(ConfigSource):
    def __init__(
            self,
            name,
            handler,
            mapping=None,
            ):
        if mapping is None:
            raise NotImplementedError("Mapping must be passed explictly")
        self._mapping = mapping
        super().__init__(name=name, handler=handler)

    def read_config(self, input_args):
        config_data = {}
        for src_key, config_keys in self._mapping.items():
            config_value = input_args.get(src_key, None)
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


class EnvVarsConfigSource(MappingConfigSource):
    def __init__(
            self,
            name,
            handler,
            mapping=None,
            ):
        mapping = (mapping if mapping is not None
                   else handler.environment_variables)
        super().__init__(name=name, handler=handler, mapping=mapping)

    def read_config(self):
        config_data = super().read_config(os.environ)
        return config_data


class CLIArgsConfigSource(MappingConfigSource):
    def __init__(
            self,
            name,
            handler,
            mapping=None,
            ):
        mapping = (mapping if mapping is not None
                   else handler.cli_arguments)
        super().__init__(name=name, handler=handler, mapping=mapping)

    def read_config(self):
        arg_parser = argparse.ArgumentParser(
            argument_default=argparse.SUPPRESS)
        for arg_name in self._mapping.keys():
            arg_parser.add_argument(f"--{arg_name.replace('_', '-')}")

        cli_args, __ = arg_parser.parse_known_args()
        config_data = super().read_config(vars(cli_args))
        return config_data


CONFIG_LEVEL_PRESETS = {
    "defaults": {"source": DefaultsConfigSource},
    "remote": {"source": FileConfigSource,
               "args": {"extension": EXTENSION_JSON}},
    "local": {"source": FileConfigSource},
    "env_vars": {"source": EnvVarsConfigSource},
    "cli_args": {"source": CLIArgsConfigSource},
    }


@brokkr.utils.misc.auto_repr(exclude=())
class ConfigHandler:
    def __init__(
            self,
            name,
            defaults=None,
            config_levels=("defaults", "local"),
            default_config_path=DEFAULT_CONFIG_PATH,
            config_version=CONFIG_VERSION,
            path_variables=None,
            environment_variables=None,
            cli_arguments=None,
            ):
        self.name = name
        self.defaults = defaults if defaults is not None else {}
        self.default_config_path = Path(default_config_path)
        self.config_version = config_version
        self.path_variables = (
            path_variables if path_variables is not None else [])
        self.environment_variables = (
            environment_variables if environment_variables is not None else [])
        self.cli_arguments = (
            cli_arguments if cli_arguments is not None else [])

        # Set up preset config levels
        self.config_levels = {}
        for config_level in config_levels:
            if not isinstance(config_level, ConfigSource):
                config_preset = CONFIG_LEVEL_PRESETS[config_level]
                config_level = config_preset["source"](
                    config_level, handler=self,
                    **copy.deepcopy(config_preset.get("args", {})),
                    )
            config_level.handler = self
            self.config_levels[config_level.name] = config_level

    def read_configs(self, config_names=None):
        configs = {}
        if config_names is None:
            config_names = self.config_levels.keys()
        configs = {config_name: self.config_levels[config_name].read_config()
                   for config_name in config_names}
        return configs

    def render_config(self, configs=None):
        if configs is None:
            configs = self.read_configs()

        # Recursively build final config dict from succession of loaded configs
        rendered_config = copy.deepcopy(
            configs[list(self.config_levels.keys())[0]])
        for config_name in list(self.config_levels.keys())[1:]:
            if configs[config_name]:
                rendered_config = brokkr.utils.misc.update_dict_recursive(
                    rendered_config, configs[config_name])

        return rendered_config
