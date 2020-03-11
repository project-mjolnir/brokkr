"""
Mode preset configuration for Brokkr, loaded second.
"""

# Local imports
from brokkr.config.modehandler import CONFIG_HANDLER_MODE


# Mode config dict
MODE_CONFIGS = CONFIG_HANDLER_MODE.read_configs()
MODE_CONFIG = CONFIG_HANDLER_MODE.render_config(MODE_CONFIGS)
