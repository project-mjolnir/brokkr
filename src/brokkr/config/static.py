"""
System configuration for Brokkr; loaded after logging but before dynamic.
"""

# Standard library imports
import logging

# Local imports
import brokkr.config.handlers


logger = logging.getLogger(__name__)


# Master config dict; currently static
STATIC_CONFIG_HANDLER = brokkr.config.handlers.CONFIG_HANDLER_STATIC
logger.debug("Reading Brokkr static config at %r",
             STATIC_CONFIG_HANDLER.default_config_path.as_posix())

CONFIGS = STATIC_CONFIG_HANDLER.read_configs()
logger.debug("Loaded static config: %r", CONFIGS)
CONFIG = STATIC_CONFIG_HANDLER.render_config(CONFIGS)
logger.info("Rendered static config: %r", CONFIG)
