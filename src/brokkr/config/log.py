"""
Logging configuration for Brokkr; loaded early before primary initialization.
"""

# Local imports
import brokkr.config.handlers


# Logging config dict
LOG_CONFIG_HANDLER = brokkr.config.handlers.CONFIG_HANDLER_LOG
LOG_CONFIGS = LOG_CONFIG_HANDLER.read_configs()
LOG_CONFIG = LOG_CONFIG_HANDLER.render_config(LOG_CONFIGS)
