"""
The configuration handler for the system preset path, loaded first.
"""

# Local imports
import brokkr.config.base
from brokkr.constants import (
    CONFIG_NAME_SYSTEM,
    CONFIG_PATH_MAIN,
    CONFIG_VERSION,
    LEVEL_NAME_LOCAL,
    PACKAGE_NAME,
    )


CONFIG_HANDLER_FACTORY = brokkr.config.base.ConfigHandlerFactory(
    level_presets=brokkr.config.base.CONFIG_LEVEL_PRESETS,
    main_config_path=CONFIG_PATH_MAIN,
    config_version=CONFIG_VERSION,
    )


DEFAULT_CONFIG_SYSTEM = {
    "system_path": "",
    }
ENV_VARIABLES_SYSTEM = {
    (PACKAGE_NAME.upper() + "_SYSTEM_PATH"): ("system_path",)}
CLI_ARGUMENTS_SYSTEM = {"system_path": ("system_path",)}

CONFIG_HANDLER_SYSTEM = CONFIG_HANDLER_FACTORY.create_config_handler(
    name=CONFIG_NAME_SYSTEM,
    config_levels=[
        LEVEL_NAME_LOCAL,
        {brokkr.config.base.LEVEL_CLASS: brokkr.config.base.EnvVarsConfigLevel,
         brokkr.config.base.LEVEL_ARGS: {"mapping": ENV_VARIABLES_SYSTEM}},
        {brokkr.config.base.LEVEL_CLASS: brokkr.config.base.CLIArgsConfigLevel,
         brokkr.config.base.LEVEL_ARGS:
             {"mapping": CLI_ARGUMENTS_SYSTEM}},
        ],
    defaults=DEFAULT_CONFIG_SYSTEM,
    path_variables=[("system_path", )],
    )
