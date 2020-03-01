"""
Dynamic configuration for Brokkr; loaded after primary initialization.
"""

# Local imports
import brokkr.config.handlers


# Dynamic config dict
DYNAMIC_CONFIG_HANDLER = brokkr.config.handlers.CONFIG_HANDLER_DYNAMIC
DYNAMIC_CONFIGS = DYNAMIC_CONFIG_HANDLER.read_configs()
DYNAMIC_CONFIG = DYNAMIC_CONFIG_HANDLER.render_config(DYNAMIC_CONFIGS)
