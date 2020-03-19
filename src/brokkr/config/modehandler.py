"""
The configuration handler for the config mode system, loaded after metadata.
"""

# Local imports
import brokkr.config.base
from brokkr.config.metadata import METADATA
from brokkr.config.systempath import SYSTEMPATH_CONFIG
from brokkr.constants import (
    CONFIG_NAME_MAIN,
    CONFIG_NAME_MODE,
    CONFIG_PATH_LOCAL,
    CONFIG_VERSION,
    LEVEL_NAME_SYSTEM,
    LEVEL_NAME_LOCAL,
    OUTPUT_PATH_BASE,
    OUTPUT_SUBPATH_REALTIME,
    OUTPUT_SUBPATH_TEST,
    PACKAGE_NAME,
    SYSTEM_SUBPATH_CONFIG,
    )
import brokkr.utils.misc


CONFIG_HANDLER_FACTORY = brokkr.config.base.ConfigHandlerFactory(
    local_config_path=CONFIG_PATH_LOCAL / METADATA["name"],
    preset_config_path=(brokkr.utils.misc.get_system_path(SYSTEMPATH_CONFIG)
                        / SYSTEM_SUBPATH_CONFIG),
    config_version=CONFIG_VERSION,
    )


DEFAULT_CONFIG_MODE = {
    "mode": "default",
    "default": {},
    "production": {},
    "realtime": {
        CONFIG_NAME_MAIN: {
            "general": {
                "output_path_client":
                    (OUTPUT_PATH_BASE / OUTPUT_SUBPATH_REALTIME).as_posix(),
                },
            },
        },
    "test": {
        CONFIG_NAME_MAIN: {
            "general": {
                "output_path_client":
                    (OUTPUT_PATH_BASE / OUTPUT_SUBPATH_TEST).as_posix(),
                },
            },
        },
    }
ENV_VARIABLES_MODE = {
    (PACKAGE_NAME.upper() + "_MODE"): ("mode",)}
CLI_ARGUMENTS_MODE = {"mode": ("mode",)}

CONFIG_HANDLER_MODE = CONFIG_HANDLER_FACTORY.create_config_handler(
    name=CONFIG_NAME_MODE,
    config_levels=[
        LEVEL_NAME_SYSTEM,
        LEVEL_NAME_LOCAL,
        {brokkr.config.base.LEVEL_CLASS: brokkr.config.base.EnvVarsConfigLevel,
         brokkr.config.base.LEVEL_ARGS: {"mapping": ENV_VARIABLES_MODE}},
        {brokkr.config.base.LEVEL_CLASS: brokkr.config.base.CLIArgsConfigLevel,
         brokkr.config.base.LEVEL_ARGS: {"mapping": CLI_ARGUMENTS_MODE}},
        ],
    defaults=DEFAULT_CONFIG_MODE,
    path_variables=[
        ("test", CONFIG_NAME_MAIN, "general", "output_path_client"),
        ("realtime", CONFIG_NAME_MAIN, "general", "output_path_client"),
        ],
    )
