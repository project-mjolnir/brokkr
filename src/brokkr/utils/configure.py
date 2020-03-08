"""
Setup and configuration commands and utilities for Brokkr.
"""

# Standard library imports
import logging
from pathlib import Path

# Local imports
from brokkr.constants import (
    CONFIG_NAME_SYSTEM,
    CONFIG_NAME_UNIT,
    )
import brokkr.config.handlers
import brokkr.utils.log


ALL_RESET = "all"
DEFAULT_CONFIG_LEVEL = "local"


def _write_config_file_wrapper(config_name, config_data,
                               config_level=DEFAULT_CONFIG_LEVEL):
    logging.debug("Setting up %s config with data: %r",
                  config_name, config_data)
    config_handler = brokkr.config.handlers.ALL_CONFIG_HANDLERS[config_name]
    config_source = config_handler.config_levels[config_level]
    config_source.write_config(config_data)
    logging.info("%s config file updated in %r", config_name.title(),
                 config_source.path.as_posix())


@brokkr.utils.log.basic_logging
def configure_reset(reset_names=ALL_RESET, reset_levels=ALL_RESET,
                    include_system=None):
    # Include system config in configs to reset only if explictly specified
    if include_system is None:
        include_system = (
            reset_names != ALL_RESET
            and CONFIG_NAME_SYSTEM in reset_names)
    if include_system:
        config_handlers = brokkr.config.handlers.ALL_CONFIG_HANDLERS
    else:
        config_handlers = brokkr.config.handlers.CONFIG_HANDLERS

    # Ensure value of all is handled properly
    reset_names = ALL_RESET if reset_names[0] == ALL_RESET else reset_names
    reset_levels = ALL_RESET if reset_levels[0] == ALL_RESET else reset_levels

    # Reset each specified config name and level
    for config_name, handler in config_handlers.items():
        if reset_names == ALL_RESET or config_name in reset_names:
            for level_name, level_source in handler.config_levels.items():
                if reset_levels == ALL_RESET or level_name in reset_levels:
                    if not getattr(level_source, "preset", True):
                        logging.debug("Resetting %s configuration for %s",
                                      level_name, config_name)
                        level_source.write_config()

    logging.info("Reset %s configuration for %s", reset_levels, reset_names)


@brokkr.utils.log.basic_logging
def configure_unit(number, network_interface, site_description=""):
    unit_config_data = {
        "number": number,
        "network_interface": network_interface,
        "site_description": site_description,
        }
    _write_config_file_wrapper(
        CONFIG_NAME_UNIT, unit_config_data)
    return unit_config_data


@brokkr.utils.log.basic_logging
def configure_system(system_config_path):
    system_config_data = {
        "system_path": Path(system_config_path).as_posix(),
        }
    _write_config_file_wrapper(
        CONFIG_NAME_SYSTEM, system_config_data)
    return system_config_data
