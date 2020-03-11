"""
Logging configuration for Brokkr; loaded early before primary initialization.
"""

# Local imports
from brokkr.config.confighandlers import CONFIG_HANDLER_LOG


# Logging config dicts
LOG_CONFIGS = CONFIG_HANDLER_LOG.read_configs()
LOG_CONFIG = CONFIG_HANDLER_LOG.render_config(LOG_CONFIGS)
