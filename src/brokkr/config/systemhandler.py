# -*- coding: utf-8 -*-
"""
The configuration handler for the system preset path, loaded first.
"""

# Local imports
import brokkr.config.base
from brokkr.config.constants import PACKAGE_NAME


SYSTEM_NAME = "system"
DEFAULT_CONFIG_SYSTEM = {
    "system_path": "",
    }
PATH_VARIABLES_SYSTEM = [("system_path",)]
ENVIRONMENT_VARIABLES_SYSTEM = {
    (PACKAGE_NAME.upper() + "_SYSTEM_PATH"): ("system_path",)}
CLI_ARGUMENTS_SYSTEM = {"system_path": ("system_path",)}

CONFIG_TYPE_SYSTEM = brokkr.config.base.ConfigType(
    SYSTEM_NAME,
    defaults=DEFAULT_CONFIG_SYSTEM,
    path_variables=PATH_VARIABLES_SYSTEM,
    )
CONFIG_LEVELS_SYSTEM = [
    brokkr.config.base.FileConfigLevel(
        config_type=CONFIG_TYPE_SYSTEM, append_level=False),
    brokkr.config.base.EnvVarsConfigLevel(
        config_type=CONFIG_TYPE_SYSTEM, mapping=ENVIRONMENT_VARIABLES_SYSTEM),
    brokkr.config.base.CLIArgsConfigLevel(
        config_type=CONFIG_TYPE_SYSTEM, mapping=CLI_ARGUMENTS_SYSTEM),
    ]
CONFIG_HANDLER_SYSTEM = brokkr.config.base.ConfigHandler(
    config_type=CONFIG_TYPE_SYSTEM,
    config_levels=CONFIG_LEVELS_SYSTEM,
)
