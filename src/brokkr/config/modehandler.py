"""
The configuration handler for the config modes system, loaded second.
"""

# Local imports
import brokkr.config.base
from brokkr.config.constants import (
    CONFIG_NAME_BOOTSTRAP,
    CONFIG_NAME_DYNAMIC,
    CONFIG_NAME_MODE,
    LEVEL_NAME_SYSTEM,
    LEVEL_NAME_SYSTEM_CLIENT,
    OUTPUT_PATH_BASE,
    OUTPUT_SUBPATH_REALTIME,
    OUTPUT_SUBPATH_TEST,
    PACKAGE_NAME,
    SYSTEM_SUBPATH_CONFIG,
    )
from brokkr.config.system import SYSTEM_CONFIG


SYSTEM_CONFIG_PATH = SYSTEM_CONFIG["system_path"] / SYSTEM_SUBPATH_CONFIG


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
                "monitor_interval_s": 5,
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
                "monitor_interval_s": 10,
                },
            },
        },
    }
PATH_VARIABLES_MODE = [
    ("test", CONFIG_NAME_BOOTSTRAP, "output_path_client"),
    ("realtime", CONFIG_NAME_BOOTSTRAP, "output_path_client"),
    ]
ENVIRONMENT_VARIABLES_MODE = {
    (PACKAGE_NAME.upper() + "_MODE"): ("mode",)}
CLI_ARGUMENTS_MODE = {"mode": ("mode",)}

CONFIG_TYPE_MODE = brokkr.config.base.ConfigType(
    CONFIG_NAME_MODE,
    defaults=DEFAULT_CONFIG_MODE,
    preset_config_path=SYSTEM_CONFIG_PATH,
    path_variables=PATH_VARIABLES_MODE,
    )
CONFIG_LEVELS_MODE = [
    brokkr.config.base.FileConfigLevel(
        name=LEVEL_NAME_SYSTEM, config_type=CONFIG_TYPE_MODE,
        preset=True, append_level=False),
    brokkr.config.base.FileConfigLevel(
        name=LEVEL_NAME_SYSTEM_CLIENT, config_type=CONFIG_TYPE_MODE,
        preset=True),
    brokkr.config.base.FileConfigLevel(
        config_type=CONFIG_TYPE_MODE, append_level=False),
    brokkr.config.base.EnvVarsConfigLevel(
        config_type=CONFIG_TYPE_MODE, mapping=ENVIRONMENT_VARIABLES_MODE),
    brokkr.config.base.CLIArgsConfigLevel(
        config_type=CONFIG_TYPE_MODE, mapping=CLI_ARGUMENTS_MODE),
    ]
CONFIG_HANDLER_MODE = brokkr.config.base.ConfigHandler(
    config_type=CONFIG_TYPE_MODE,
    config_levels=CONFIG_LEVELS_MODE,
)
