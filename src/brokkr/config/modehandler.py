"""
The configuration handler for the config modes system, loaded second.
"""

# Local imports
import brokkr.config.base
from brokkr.config.constants import (
    CONFIG_NAME_BOOTSTRAP,
    CONFIG_NAME_DYNAMIC,
    CONFIG_NAME_MODE,
    CONFIG_PATH_MAIN,
    CONFIG_VERSION,
    LEVEL_NAME_SYSTEM,
    LEVEL_NAME_SYSTEM_CLIENT,
    LEVEL_NAME_LOCAL,
    OUTPUT_PATH_BASE,
    OUTPUT_SUBPATH_REALTIME,
    OUTPUT_SUBPATH_TEST,
    PACKAGE_NAME,
    SYSTEM_SUBPATH_CONFIG,
    )
from brokkr.config.system import SYSTEM_CONFIG


CONFIG_PATH_SYSTEM = SYSTEM_CONFIG["system_path"] / SYSTEM_SUBPATH_CONFIG

CONFIG_HANDLER_FACTORY = brokkr.config.base.ConfigHandlerFactory(
    level_presets=brokkr.config.base.CONFIG_LEVEL_PRESETS,
    main_config_path=CONFIG_PATH_MAIN,
    preset_config_path=CONFIG_PATH_SYSTEM,
    config_version=CONFIG_VERSION,
    )


DEFAULT_CONFIG_MODE = {
    "mode": "default",
    "default": {},
    "production": {},
    "realtime": {
        CONFIG_NAME_BOOTSTRAP: {
            "output_path_client":
                (OUTPUT_PATH_BASE / OUTPUT_SUBPATH_REALTIME).as_posix(),
            },
        CONFIG_NAME_DYNAMIC: {
            "monitor": {
                "hs_timeout_s": 1,
                "monitor_interval_s": 1,
                },
            },
        },
    "test": {
        CONFIG_NAME_BOOTSTRAP: {
            "output_path_client":
                (OUTPUT_PATH_BASE / OUTPUT_SUBPATH_TEST).as_posix(),
            },
        CONFIG_NAME_DYNAMIC: {
            "monitor": {
                "monitor_interval_s": 5,
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
        LEVEL_NAME_SYSTEM_CLIENT,
        LEVEL_NAME_LOCAL,
        {brokkr.config.base.LEVEL_CLASS: brokkr.config.base.EnvVarsConfigLevel,
         brokkr.config.base.LEVEL_ARGS: {"mapping": ENV_VARIABLES_MODE}},
        {brokkr.config.base.LEVEL_CLASS: brokkr.config.base.CLIArgsConfigLevel,
         brokkr.config.base.LEVEL_ARGS: {"mapping": CLI_ARGUMENTS_MODE}},
        ],
    defaults=DEFAULT_CONFIG_MODE,
    path_variables=[
        ("test", CONFIG_NAME_BOOTSTRAP, "output_path_client"),
        ("realtime", CONFIG_NAME_BOOTSTRAP, "output_path_client"),
        ],
    )
