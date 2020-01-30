"""
System path configuration for Brokkr, loaded first.
"""

# Local imports
import brokkr.config.systemhandler


# System config dict; static
SYSTEM_CONFIG_HANDLER = brokkr.config.systemhandler.CONFIG_HANDLER_SYSTEM
SYSTEM_CONFIGS = SYSTEM_CONFIG_HANDLER.read_configs()
SYSTEM_CONFIG = SYSTEM_CONFIG_HANDLER.render_config(SYSTEM_CONFIGS)
