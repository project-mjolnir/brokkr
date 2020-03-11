"""
Metadata configuration for Brokkr; loaded early before primary initialization.
"""

# Local imports
from brokkr.config.metadatahandler import CONFIG_HANDLER_METADATA


# Metadata config dict
METADATA_CONFIGS = CONFIG_HANDLER_METADATA.read_configs()
METADATA = CONFIG_HANDLER_METADATA.render_config(METADATA_CONFIGS)
