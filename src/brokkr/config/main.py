"""
Main configuration for Brokkr; loaded after primary initialization.
"""

# Local imports
from brokkr.config.confighandlers import CONFIG_HANDLER_MAIN


# Main config dict
CONFIGS = CONFIG_HANDLER_MAIN.read_configs()
CONFIG = CONFIG_HANDLER_MAIN.render_config(CONFIGS)
