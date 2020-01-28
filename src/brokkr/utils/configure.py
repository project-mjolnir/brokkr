"""
Setup and configuration commands and utilities for Brokkr.
"""

# Standard library imports
import logging

# Local imports
import brokkr.config.base
import brokkr.config.log
import brokkr.config.main
import brokkr.config.unit
from brokkr.utils.misc import basic_logging


ALL_CONFIG_HANDLERS = {
    "unit": brokkr.config.unit.CONFIG_HANDLER,
    "log": brokkr.config.log.CONFIG_HANDLER,
    "main": brokkr.config.main.CONFIG_HANDLER,
    }

ALL_RESET = "all"
UNIT_CONFIG_LEVEL = "local"


@basic_logging
def configure_reset(reset_names=ALL_RESET, reset_levels=ALL_RESET):
    for config_name, handler in ALL_CONFIG_HANDLERS.items():
        if reset_names == ALL_RESET or config_name in reset_names:
            for level_name, level_source in handler.config_levels.items():
                if reset_levels == ALL_RESET or level_name in reset_levels:
                    try:
                        if level_source._create:
                            logging.debug("Resetting %s configuration for %s",
                                          level_name, config_name)
                            level_source.write_config()
                    # Ignore levels that don't have the create attribute
                    except AttributeError:
                        pass

    logging.info("Reset %s configuration for %s", reset_levels, reset_names)


@basic_logging
def configure_unit(number, network_interface, description=""):
    unit_config = {
        "number": number,
        "network_interface": network_interface,
        "description": description,
        }
    logging.debug("Setting up unit config with data: %r", unit_config)
    unit_config_handler = brokkr.config.unit.CONFIG_HANDLER
    unit_config_handler.config_levels[UNIT_CONFIG_LEVEL].write_config()
    logging.info("Unit config files updated in %r",
                 unit_config_handler.config_levels[UNIT_CONFIG_LEVEL]._path)
    return unit_config
