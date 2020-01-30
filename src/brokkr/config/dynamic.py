"""
Dynamic configuration for Brokkr; loaded after logging starts.
"""

# Standard library imports
import logging

# Local imports
import brokkr.config.handlers


logger = logging.getLogger(__name__)


# Dynamic config dict
DYNAMIC_CONFIG_HANDLER = brokkr.config.handlers.CONFIG_HANDLER_DYNAMIC
logger.debug("Reading Brokkr dynamic config at %r",
             DYNAMIC_CONFIG_HANDLER.default_config_path.as_posix())

DYNAMIC_CONFIGS = DYNAMIC_CONFIG_HANDLER.read_configs()
logger.debug("Loaded dynamic config: %r", DYNAMIC_CONFIGS)
DYNAMIC_CONFIG = DYNAMIC_CONFIG_HANDLER.render_config(DYNAMIC_CONFIGS)
logger.info("Rendered dynamic config: %r", DYNAMIC_CONFIG)
