"""
Dynamic configuration for Brokkr; loaded after primary initialization.
"""

# Standard library imports
import logging

# Local imports
import brokkr.config.handlers


LOGGER = logging.getLogger(__name__)


# Dynamic config dict
DYNAMIC_CONFIG_HANDLER = brokkr.config.handlers.CONFIG_HANDLER_DYNAMIC
LOGGER.debug(
    "Reading dynamic config at system path %r and local path %r",
    DYNAMIC_CONFIG_HANDLER.config_type.preset_config_path.as_posix(),
    DYNAMIC_CONFIG_HANDLER.config_type.main_config_path.as_posix(),
    )

DYNAMIC_CONFIGS = DYNAMIC_CONFIG_HANDLER.read_configs()
LOGGER.debug("Loaded dynamic config: %r", DYNAMIC_CONFIGS)
DYNAMIC_CONFIG = DYNAMIC_CONFIG_HANDLER.render_config(DYNAMIC_CONFIGS)
LOGGER.info("Rendered dynamic config: %r", DYNAMIC_CONFIG)
