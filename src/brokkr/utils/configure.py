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


@basic_logging
def configure_reset(config_names="all", config_types="all"):
    for config, handler in (
            ("log", brokkr.config.log.CONFIG_HANDLER),
            ("main", brokkr.config.main.CONFIG_HANDLER),
            ("unit", brokkr.config.unit.CONFIG_HANDLER),
            ):
        if config_names == "all" or config in config_names:
            for type_name, type_obj in handler.config_types.items():
                if ((config_types == "all" or type_name in config_types)
                        and type_obj.extension is not None):
                    logging.debug("Resetting %s configuration for %s",
                                  type_name, config)
                    handler.generate_config(type_name)

    logging.info("Reset %s configuration for %s", config_types, config_names)


@basic_logging
def configure_unit(number, network_interface, description=""):
    unit_config = {
        "number": number,
        "network_interface": network_interface,
        "description": description,
        }
    logging.debug("Setting up unit config...")
    brokkr.config.unit.CONFIG_HANDLER.write_config(
        config_name="local", config_data=unit_config)
    logging.info("Unit config files updated in %s",
                 brokkr.config.unit.CONFIG_HANDLER.config_dir)
    return unit_config
