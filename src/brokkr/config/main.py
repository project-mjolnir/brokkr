"""
Main configuration for Brokkr; loaded after primary initialization.
"""

# Local imports
import brokkr.config.handlers


# Master config dict; currently static
MAIN_CONFIG_HANDLER = brokkr.config.handlers.CONFIG_HANDLER_MAIN
CONFIGS = MAIN_CONFIG_HANDLER.read_configs()
CONFIG = MAIN_CONFIG_HANDLER.render_config(CONFIGS)
