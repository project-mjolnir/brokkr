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
def configure_reset(config_type="all"):
    logging.debug("Resetting Brokkr configuration: %s", config_type)

    for config, handler in (
            ("log", brokkr.config.log.CONFIG_HANDLER),
            ("main", brokkr.config.main.CONFIG_HANDLER),
            ("unit", brokkr.config.unit.CONFIG_HANDLER),
            ):
        if config_type in ("all", config):
            logging.debug("Restting %s config...", config)
            for config_subtype in handler.config_types:
                handler.generate_config(config_subtype)

    logging.info("Reset Brokker configuration: %s", config_type)


@basic_logging
def configure_unit(number, network_interface, description=""):
    unit_config = {
        "number": number,
        "network_interface": network_interface,
        "description": description,
        }
    logging.debug("Setting up unit config...")
    brokkr.config.unit.CONFIG_HANDLER.write_config_data(
        config_name="local", config_data=unit_config)
    logging.info("Unit config files updated in %s",
                 brokkr.config.unit.CONFIG_HANDLER.config_dir)
    return unit_config
