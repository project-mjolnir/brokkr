"""
Main configuration for Brokkr; loaded after logging starts.
"""

# Standard library imports
import logging

# Local imports
import brokkr.config.handlers


logger = logging.getLogger(__name__)


# Master config dict; currently static
CONFIG_HANDLER = brokkr.config.handlers.CONFIG_HANDLER_MAIN
logger.debug("Reading Brokkr config at %r",
             CONFIG_HANDLER.default_config_path.as_posix())

CONFIGS = CONFIG_HANDLER.read_configs()
logger.debug("Loaded config: %r", CONFIGS)
CONFIG = CONFIG_HANDLER.render_config(CONFIGS)
logger.info("Rendered config: %r", CONFIG)
