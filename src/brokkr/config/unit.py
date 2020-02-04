"""
Unit configuration for Brokkr; loaded early before primary initialization.
"""

# Local imports
import brokkr.config.handlers


# Unit config dict
UNIT_CONFIG_HANDLER = brokkr.config.handlers.CONFIG_HANDLER_UNIT
UNIT_CONFIGS = UNIT_CONFIG_HANDLER.read_configs()
UNIT_CONFIG = UNIT_CONFIG_HANDLER.render_config(UNIT_CONFIGS)
