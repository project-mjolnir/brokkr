"""
Baseline hierarchical configuration setup functions for Brokkr.
"""

# Standard library imports
import abc
import argparse
import collections.abc
import copy
import json
import logging
import os
from pathlib import Path

# Third party imports
import toml
import toml.decoder

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
LEVEL_NAME_CLI_ARGS = "cli_args"
LEVEL_NAME_DEFAULTS = "defaults"
LEVEL_NAME_ENV_VARS = "env_vars"
LEVEL_NAME_FILE = "local"
LEVEL_NAME_OVERLAY = "overlay"
LEVEL_NAME_PRESETS = "presets"

EXTENSION_TOML = "toml"
EXTENSION_JSON = "json"
EXTENSION_DEFAULT = EXTENSION_TOML
EXTENSIONS_SUPPORTED = [EXTENSION_TOML, EXTENSION_JSON]

VERSION_KEY = "config_version"
EMPTY_CONFIG = ("config_is_empty", True)
JSON_SEPERATORS = (",", ":")
CONFIG_VERSION_DEFAULT = 1

LEVEL_CLASS = "level_class"
LEVEL_ARGS = "level_args"


# --- Utility functions --- #

def check_extension_supported(extension):
    if extension not in EXTENSIONS_SUPPORTED:
        raise ValueError("Extension must be one of "
                         f"{EXTENSIONS_SUPPORTED}, not {extension}")


def convert_paths(config_data, path_variables):
    # Format string paths as pathlib paths with username expanded
    for key_name in path_variables:
        inner_dict = config_data
        try:
            inner_dict = brokkr.utils.misc.get_inner_dict(
                obj=config_data, keys=key_name[:-1])
            inner_dict[key_name[-1]] = brokkr.utils.misc.convert_path(
                inner_dict[key_name[-1]])
        # Ignore missing keys
        except KeyError:
            continue
    return config_data


def read_config_file(path, extension=None, logger=None):
    if logger is True:
        logger = logging.getLogger(__name__)
    path = Path(path)
    if extension is None:
        extension = path.suffix.strip(".")
    check_extension_supported(extension)
    if extension == EXTENSION_TOML:
        try:
            config_data = toml.load(path)
        except toml.decoder.TomlDecodeError as e:
            if logger is not None:
                logger.error("%s reading TOML config file %r: %s",
                             type(e).__name__, path.as_posix(), e)
                logger.info("Error details:", exc_info=True)
                raise SystemExit(1)
            raise
    elif extension == EXTENSION_JSON:
        with open(path, "r", encoding="utf-8") as config_file:
            try:
                config_data = json.load(config_file)
            except Exception as e:
                if logger is not None:
                    logger.error("%s reading JSON config file %r: %s",
                                 type(e).__name__, path.as_posix(), e)
                    logger.info("Error details:", exc_info=True)
                    raise SystemExit(1)
                raise

    return config_data


def write_config_file(config_data, path, extension=None):
    path = Path(path)
    if extension is None:
        extension = Path(path).suffix.strip(".")
    check_extension_supported(extension)
    os.makedirs(path.parent, exist_ok=True)
    with open(path, mode="w", encoding="utf-8", newline="\n") as config_file:
        if extension == EXTENSION_TOML:
            toml.dump(config_data, config_file)
        elif extension == EXTENSION_JSON:
            json.dump(config_data, config_file,
                      allow_nan=False, separators=JSON_SEPERATORS)


def insert_values(config_data, insert_items, logger=None):
    # pylint: disable=too-many-nested-blocks, too-many-branches
    if logger is True:
        logger = logging.getLogger(__name__)

    # Insert the specified values into the given keys
    for preset_name, preset_data in config_data.items():
        for table_name, target_key in insert_items:
            if (preset_data.get(table_name, None) is None
                    or preset_data.get(target_key, None) is None):
                continue  # Skip if source or target table is not preset
            if preset_data[table_name].get(
                    target_key, None) is not None:
                # If target key is present at first level, use that
                target_tables = {table_name: preset_data[table_name]}
            else:
                # Otherwise, check for the key in the table's subdicts
                target_tables = preset_data[table_name]
            for target_name, target_table in target_tables.items():
                if target_table.get(target_key, None) is None:
                    continue  # Skip target tables that lack the key at all
                if not target_table[target_key]:
                    # If key is empty, fill it with the entire source table
                    target_table[target_key] = preset_data[target_key]
                    continue
                # Otherwise, do a lookup in the source table
                try:
                    if brokkr.utils.misc.is_iterable(
                            target_table[target_key]):
                        if isinstance(preset_data[target_key],
                                      collections.abc.Mapping):
                            # If the target is an iterable and the src a dict,
                            # look up each value in the source table
                            target_table[target_key] = {
                                inner_key: preset_data[target_key][inner_key]
                                for inner_key in target_table[target_key]}
                        else:
                            # Otherwise, if both are lists, merge them
                            target_table[target_key] = set(
                                target_table[target_key]
                                + preset_data[target_key])
                    else:
                        # Otherwise, look up the value in the source table
                        # and merge them, keeping values in the original
                        merged_table = brokkr.utils.misc.update_dict_recursive(
                            preset_data[target_key][target_table[target_key]],
                            target_table)
                        target_table.update(merged_table)
                        # And remove the now-redundant item
                        del target_table[target_key]
                except KeyError as e:
                    if not logger:
                        raise
                    logger.error(
                        "%s inserting value for preset %r: "
                        "Can't find inner key %s in key %r to insert into "
                        "table %r, subtable %r",
                        type(e).__name__, preset_name, e, target_key,
                        table_name, target_name)
                    logger.info("Error details:", exc_info=True)
                    logger.info("Possible keys: %r",
                                list(preset_data[target_key].keys()))
                    raise SystemExit(1)

    return config_data


# --- Config type --- #

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


# --- Config level classes #

class ConfigLevel(brokkr.utils.misc.AutoReprMixin, metaclass=abc.ABCMeta):
    def __init__(
            self,
            name,
            config_type=None,
            logger=None,
                ):
        self.name = name
        self.config_type = (ConfigType(DEFAULT_CONFIG_TYPE_NAME)
                            if config_type is None else config_type)
        self.logger = logger

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
            path=None,
            extension=EXTENSION_DEFAULT,
            preset=False,
            append_level=False,
            **kwargs,
                ):
        check_extension_supported(extension)
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
                config_data = read_config_file(
                    path=self.path,
                    extension=self.extension,
                    logger=self.logger,
                    )
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

        write_config_file(config_data, self.path)
        return config_data


class PresetsConfigLevel(ConfigLevel):
    def __init__(
            self,
            name=LEVEL_NAME_PRESETS,
            path=None,
            filename_glob=f"*.preset.{EXTENSION_DEFAULT}",
            key_name="name",
            template=None,
            insert_items=None,
            **kwargs,
                ):
        super().__init__(name=name, **kwargs)
        self.filename_glob = filename_glob
        self.key_name = key_name
        self.template = {} if template is None else template
        self.insert_items = {} if insert_items is None else insert_items

        if path is not None:
            self.path = Path(path)
        else:
            self.path = self.config_type.local_config_path

    def read_config(self, input_data=None):
        if input_data is None:
            preset_paths = self.path.glob(self.filename_glob)
            presets = {
                path: brokkr.utils.misc.update_dict_recursive(
                    copy.deepcopy(self.template), read_config_file(
                        path=path, logger=self.logger))
                for path in preset_paths}
            config_data = {
                preset.get(self.key_name, path.stem.split(".")[0]): preset
                for path, preset in presets.items()}
            config_data = insert_values(
                config_data, self.insert_items, logger=self.logger)

        else:
            config_data = copy.deepcopy(input_data)

        config_data = super().read_config(input_data=config_data)
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


# --- Config handler classes #

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
