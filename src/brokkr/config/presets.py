"""
Preset configuration for Brokkr; loaded after primary initialization.
"""

# Local imports
from brokkr.config.confighandlers import CONFIG_HANDLER_PRESETS


# Preset config dict
PRESET_CONFIGS = CONFIG_HANDLER_PRESETS.read_configs()
PRESETS = CONFIG_HANDLER_PRESETS.render_config(PRESET_CONFIGS)
