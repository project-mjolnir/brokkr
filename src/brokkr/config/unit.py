"""
Per-unit configuration for Brokkr, loaded early.
"""

# Local imports
import brokkr.config.base


# General static constants
CONFIG_VERSION = 1
DEFAULT_CONFIG = {
    "number": 0,
    "network_interface": "wlan0",
    "description": "",
    }
CONFIG_LEVELS = ["default", "local"]

CONFIG_HANDLER = brokkr.config.base.ConfigHandler(
    "unit",
    defaults=DEFAULT_CONFIG,
    config_levels=CONFIG_LEVELS,
    config_version=CONFIG_VERSION,
    )

# Unit config dict; static
UNIT_CONFIGS = CONFIG_HANDLER.read_configs()
UNIT_CONFIG = CONFIG_HANDLER.render_config(UNIT_CONFIGS)
