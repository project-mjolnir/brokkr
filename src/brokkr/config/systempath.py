"""
System path configuration for Brokkr, loaded first.
"""

# Local imports
from brokkr.config.systempathhandler import CONFIG_HANDLER_SYSTEMPATH


# System path config dict
SYSTEMPATH_CONFIGS = CONFIG_HANDLER_SYSTEMPATH.read_configs()
SYSTEMPATH_CONFIG = CONFIG_HANDLER_SYSTEMPATH.render_config(SYSTEMPATH_CONFIGS)
