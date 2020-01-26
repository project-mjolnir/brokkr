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
UNIT_CONFIG_LEVEL_MAIN = "local"


@basic_logging
def configure_reset(config_names=ALL_RESET, config_levels=ALL_RESET):
    for config, handler in ALL_CONFIG_HANDLERS.items():
        if config_names == ALL_RESET or config in config_names:
            for type_name, type_obj in handler.config_levels.items():
                if ((config_levels == ALL_RESET or type_name in config_levels)
                        and type_obj.extension is not None
                        and type_obj.managed):
                    logging.debug("Resetting %s configuration for %s",
                                  type_name, config)
                    handler.generate_config(type_name)

    logging.info("Reset %s configuration for %s", config_levels, config_names)


@basic_logging
def configure_unit(number, network_interface, description=""):
    unit_config = {
        "number": number,
        "network_interface": network_interface,
        "description": description,
        }
    logging.debug("Setting up unit config...")
    brokkr.config.unit.CONFIG_HANDLER.generate_config(
        config_name=UNIT_CONFIG_LEVEL_MAIN, config_data=unit_config)
    logging.info("Unit config files updated in %s",
                 brokkr.config.unit.CONFIG_HANDLER.config_dir)
    return unit_config
