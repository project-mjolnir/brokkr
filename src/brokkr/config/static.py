"""
Static configuration for Brokkr; loaded after primary initialization.
"""

# Local imports
import brokkr.config.handlers


# Master config dict; currently static
STATIC_CONFIG_HANDLER = brokkr.config.handlers.CONFIG_HANDLER_STATIC
CONFIGS = STATIC_CONFIG_HANDLER.read_configs()
CONFIG = STATIC_CONFIG_HANDLER.render_config(CONFIGS)
