"""
System path configuration for Brokkr, loaded first.
"""

# Local imports
import brokkr.config.systempathhandler


# System path config dict; static
SYSTEMPATH_CONFIG_HANDLER = (
    brokkr.config.systempathhandler.CONFIG_HANDLER_SYSTEMPATH)
SYSTEMPATH_CONFIGS = SYSTEMPATH_CONFIG_HANDLER.read_configs()
SYSTEMPATH_CONFIG = SYSTEMPATH_CONFIG_HANDLER.render_config(SYSTEMPATH_CONFIGS)
