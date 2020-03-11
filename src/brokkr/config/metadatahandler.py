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
    )
import brokkr.utils.misc


SYSTEM_PATH = brokkr.utils.misc.get_system_path(SYSTEMPATH_CONFIG)

CONFIG_HANDLER_FACTORY = brokkr.config.base.ConfigHandlerFactory(
    preset_config_path=SYSTEM_PATH,
    config_version=CONFIG_VERSION,
    )


EMPTY_VARS_METADATA = [
    "name_full", "author", "description", "homepage", "repo", "version"]
EMPTY_VARS_METADATA_DICT = {key: "" for key in EMPTY_VARS_METADATA}

DEFAULT_CONFIG_METADATA = {
    "name": "mjolnir",
    **EMPTY_VARS_METADATA_DICT,
    "brokkr_version_min": "0.3.0",
    "sindri_version_min": "0.3.0",
    }

CONFIG_HANDLER_METADATA = CONFIG_HANDLER_FACTORY.create_config_handler(
    name=CONFIG_NAME_METADATA,
    config_levels=[
        LEVEL_NAME_SYSTEM,
        ],
    defaults=DEFAULT_CONFIG_METADATA,
    )
