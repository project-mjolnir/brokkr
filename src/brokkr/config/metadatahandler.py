"""
The configuration handler for the system metadata, loaded after systempath.
"""

# Local imports
import brokkr.config.base
from brokkr.config.systempath import SYSTEMPATH_CONFIG
from brokkr.constants import (
    CONFIG_NAME_METADATA,
    CONFIG_VERSION,
    LEVEL_NAME_SYSTEM,
    METADATA_VARS,
    )
import brokkr.utils.misc


SYSTEM_PATH = brokkr.utils.misc.get_system_path(SYSTEMPATH_CONFIG)

CONFIG_HANDLER_FACTORY = brokkr.config.base.ConfigHandlerFactory(
    preset_config_path=SYSTEM_PATH,
    config_version=CONFIG_VERSION,
    )


DEFAULT_CONFIG_METADATA = {
    "name": "mjolnir",
    **{key: "" for key in METADATA_VARS},
    "license": "",
    "brokkr_version_min": "0.3.0",
    "brokkr_version_max": "",
    "sindri_version_min": "0.3.0",
    "sindri_version_max": "",
    }

CONFIG_HANDLER_METADATA = CONFIG_HANDLER_FACTORY.create_config_handler(
    name=CONFIG_NAME_METADATA,
    config_levels=[
        LEVEL_NAME_SYSTEM,
        ],
    defaults=DEFAULT_CONFIG_METADATA,
    )
