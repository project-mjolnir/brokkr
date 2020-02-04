"""
Mode preset configuration for Brokkr, loaded second.
"""

# Local imports
import brokkr.config.modehandler


# System config dict; static
MODE_CONFIG_HANDLER = brokkr.config.modehandler.CONFIG_HANDLER_MODE
MODE_CONFIGS = MODE_CONFIG_HANDLER.read_configs()
MODE_CONFIG = MODE_CONFIG_HANDLER.render_config(MODE_CONFIGS)
