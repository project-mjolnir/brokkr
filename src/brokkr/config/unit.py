"""
Per-unit configuration for Brokkr, loaded early.
"""

# Local imports
import brokkr.config.handlers


# Unit config dict; static
CONFIG_HANDLER = brokkr.config.handlers.CONFIG_HANDLER_UNIT
UNIT_CONFIGS = CONFIG_HANDLER.read_configs()
UNIT_CONFIG = CONFIG_HANDLER.render_config(UNIT_CONFIGS)
