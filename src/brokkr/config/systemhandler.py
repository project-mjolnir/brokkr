# -*- coding: utf-8 -*-
"""
Bootstrap configuration handler for system path, loaded first.
"""

# Local imports
import brokkr.config.base
import brokkr.config.constants


SYSTEM_NAME = "system"
DEFAULT_CONFIG_SYSTEM = {
    "system_path": "",
    }
CONFIG_LEVELS_SYSTEM = ["defaults", "local", "env_vars", "cli_args"]
PATH_VARIABLES_SYSTEM = [("system_path",)]
CLI_ARGUMENTS_SYSTEM = {"system_path": ("system_path",)}
ENVIRONMENT_VARIABLES_SYSTEM = {brokkr.config.constants.PACKAGE_NAME.upper()
                                + "_SYSTEM_PATH": ("system_path",)}
CONFIG_HANDLER_SYSTEM = brokkr.config.base.ConfigHandler(
    SYSTEM_NAME,
    defaults=DEFAULT_CONFIG_SYSTEM,
    config_levels=CONFIG_LEVELS_SYSTEM,
    path_variables=PATH_VARIABLES_SYSTEM,
    environment_variables=ENVIRONMENT_VARIABLES_SYSTEM,
    cli_arguments=CLI_ARGUMENTS_SYSTEM,
    )
