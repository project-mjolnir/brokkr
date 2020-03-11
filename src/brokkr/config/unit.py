"""
Unit configuration for Brokkr; loaded early before primary initialization.
"""

# Local imports
from brokkr.config.confighandlers import CONFIG_HANDLER_UNIT


# Unit config dict
UNIT_CONFIGS = CONFIG_HANDLER_UNIT.read_configs()
UNIT_CONFIG = CONFIG_HANDLER_UNIT.render_config(UNIT_CONFIGS)
