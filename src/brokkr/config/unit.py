"""
Per-unit configuration for Brokkr, loaded first.
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
CONFIG_TYPES = {
    **{"default": brokkr.config.base.DEFAULT_CONFIG_TYPES["default"]},
    **{"local": brokkr.config.base.ConfigType(
        include_default=False, override=False, extension="toml")},
    }
CONFIG_HANDLER = brokkr.config.base.ConfigHandler(
    "unit",
    defaults=DEFAULT_CONFIG,
    config_types=CONFIG_TYPES,
    config_version=CONFIG_VERSION,
    )

# Unit config dict; static
CONFIGS = CONFIG_HANDLER.read_configs()
CONFIG = CONFIG_HANDLER.render_config(CONFIGS)
