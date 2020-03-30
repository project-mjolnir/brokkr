"""
The configuration handler for the system preset path, loaded first.
"""

# Local imports
import brokkr.config.base
from brokkr.constants import (
    CONFIG_NAME_SYSTEMPATH,
    CONFIG_PATH_LOCAL,
    CONFIG_VERSION,
    LEVEL_NAME_LOCAL,
    PACKAGE_NAME,
    SYSTEM_NAME_DEFAULT,
    )


CONFIG_HANDLER_FACTORY = brokkr.config.base.ConfigHandlerFactory(
    local_config_path=CONFIG_PATH_LOCAL,
    config_version=CONFIG_VERSION,
    )


DEFAULT_CONFIG_SYSTEMPATH = {
    "default_system": SYSTEM_NAME_DEFAULT,
    "system_path_override": "",
    "system_paths": {},
    }
ENV_VARIABLES_SYSTEMPATH = {
    (PACKAGE_NAME.upper() + "_SYSTEM"): ("default_system",),
    (PACKAGE_NAME.upper() + "_SYSTEM_PATH"): ("system_path_override",),
    }
CLI_ARGUMENTS_SYSTEMPATH = {
    "system": ("default_system",),
    "system_path": ("system_path_override",),
    }

CONFIG_HANDLER_SYSTEMPATH = CONFIG_HANDLER_FACTORY.create_config_handler(
    name=CONFIG_NAME_SYSTEMPATH,
    config_levels=[
        LEVEL_NAME_LOCAL,
        {brokkr.config.base.LEVEL_CLASS: brokkr.config.base.EnvVarsConfigLevel,
         brokkr.config.base.LEVEL_ARGS: {"mapping": ENV_VARIABLES_SYSTEMPATH}},
        {brokkr.config.base.LEVEL_CLASS: brokkr.config.base.CLIArgsConfigLevel,
         brokkr.config.base.LEVEL_ARGS: {"mapping": CLI_ARGUMENTS_SYSTEMPATH}},
        ],
    defaults=DEFAULT_CONFIG_SYSTEMPATH,
    path_variables=[("system_path", )],
    )
