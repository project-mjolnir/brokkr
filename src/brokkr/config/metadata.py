"""
Metadata configuration for Brokkr; loaded early before primary initialization.
"""

# Local imports
import brokkr.config.handlers


# Metadata config dict
METADATA_CONFIG_HANDLER = brokkr.config.handlers.CONFIG_HANDLER_METADATA
METADATA_CONFIGS = METADATA_CONFIG_HANDLER.read_configs()
METADATA = METADATA_CONFIG_HANDLER.render_config(METADATA_CONFIGS)
