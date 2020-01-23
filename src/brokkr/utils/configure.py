"""
Setup and configuration commands and utilities for Brokkr.
"""

# Standard library imports
import logging

# Local imports
import brokkr.config.log
import brokkr.config.main
from brokkr.utils.misc import basic_logging


@basic_logging
def configure_reset(config_type="all"):
    logging.debug("Resetting Brokkr configuration: %s", config_type)

    for config, handler in (("log", brokkr.config.log.CONFIG_HANDLER),
                            ("main", brokkr.config.main.CONFIG_HANDLER)):
        if config_type in ("all", config):
            logging.debug("Restting %s config...", config)
            for config_subtype in handler.config_types:
                handler.generate_config(config_subtype)

    logging.info("Reset Brokker configuration: %s", config_type)
