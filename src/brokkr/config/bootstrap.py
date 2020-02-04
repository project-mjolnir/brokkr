"""
Bootstrap configuration for Brokkr; loaded first after the system path.
"""

# Local imports
import brokkr.config.handlers


# Bootstrap config dict
BOOTSTRAP_CONFIG_HANDLER = brokkr.config.handlers.CONFIG_HANDLER_BOOTSTRAP
BOOTSTRAP_CONFIGS = BOOTSTRAP_CONFIG_HANDLER.read_configs()
BOOTSTRAP_CONFIG = BOOTSTRAP_CONFIG_HANDLER.render_config(BOOTSTRAP_CONFIGS)
