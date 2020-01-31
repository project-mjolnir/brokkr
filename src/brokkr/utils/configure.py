"""
Setup and configuration commands and utilities for Brokkr.
"""

# Standard library imports
import logging
from pathlib import Path

# Local imports
import brokkr.config.handlers
import brokkr.config.systemhandler
from brokkr.utils.misc import basic_logging


ALL_RESET = "all"
DEFAULT_CONFIG_LEVEL = "local"


def write_config_file(config_name, config_data,
                      config_level=DEFAULT_CONFIG_LEVEL):
    logging.debug("Setting up %s config with data: %r",
                  config_name, config_data)
    config_handler = brokkr.config.handlers.CONFIG_HANDLERS[config_name]
    config_source = config_handler.config_levels[config_level]
    config_data_default = config_source.generate_config()
    config_source.write_config({**config_data_default, **config_data})
    logging.info("%s config file updated in %r", config_name.title(),
                 config_source._path.as_posix())


@basic_logging
def configure_reset(reset_names=ALL_RESET, reset_levels=ALL_RESET):
    reset_names = ALL_RESET if reset_names[0] == ALL_RESET else reset_names
    reset_levels = ALL_RESET if reset_levels[0] == ALL_RESET else reset_levels
    for config_name, handler in brokkr.config.handlers.CONFIG_HANDLERS.items():
        if reset_names == ALL_RESET or config_name in reset_names:
            for level_name, level_source in handler.config_levels.items():
                if reset_levels == ALL_RESET or level_name in reset_levels:
                    if not getattr(level_source, "_preset", True):
                        logging.debug("Resetting %s configuration for %s",
                                      level_name, config_name)
                        level_source.write_config()

    logging.info("Reset %s configuration for %s", reset_levels, reset_names)


@basic_logging
def configure_unit(number, network_interface, site_description=""):
    unit_config_data = {
        "number": number,
        "network_interface": network_interface,
        "site_description": site_description,
        }
    write_config_file(brokkr.config.handlers.UNIT_NAME, unit_config_data)
    return unit_config_data


@basic_logging
def configure_system(system_config_path):
    system_config_data = {
        "system_path": Path(system_config_path).as_posix(),
        }
    write_config_file(brokkr.config.systemhandler.SYSTEM_NAME,
                      system_config_data)
    return system_config_data
