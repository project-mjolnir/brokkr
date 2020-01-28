"""
Logging configuration for Brokkr; loaded first before anything else.
"""

# Local imports
import brokkr.config.handlers


# Master config dict; currently static
CONFIG_HANDLER = brokkr.config.handlers.CONFIG_HANDLER_LOG
LOG_CONFIGS = CONFIG_HANDLER.read_configs()
LOG_CONFIG = CONFIG_HANDLER.render_config(LOG_CONFIGS)
