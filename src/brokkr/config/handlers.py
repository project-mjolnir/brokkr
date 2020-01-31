# -*- coding: utf-8 -*-
"""
Config handler setup for Brokkr's main managed configs.
"""

# Standard library imports
from pathlib import Path

# Local imports
import brokkr.config.base
from brokkr.config.constants import PACKAGE_NAME, OUTPUT_PATH_DEFAULT
from brokkr.config.system import SYSTEM_CONFIG
import brokkr.config.systemhandler


LEVEL_NAME_SYSTEM = "system"
LEVEL_NAME_COMMON = "common"
LEVEL_NAME_PACKAGE = PACKAGE_NAME
LEVEL_NAME_REMOTE = "remote"


UNIT_NAME = "unit"
DEFAULT_CONFIG_UNIT = {
    "number": 0,
    "network_interface": "wlan0",
    "site_description": "",
    }

CONFIG_TYPE_UNIT = brokkr.config.base.ConfigType(
    UNIT_NAME,
    defaults=DEFAULT_CONFIG_UNIT,
    preset_config_path=SYSTEM_CONFIG["system_path"],
    )
CONFIG_LEVELS_UNIT = [
    brokkr.config.base.FileConfigLevel(
        name=LEVEL_NAME_SYSTEM, config_type=CONFIG_TYPE_UNIT,
        preset=True, append_level=False),
    brokkr.config.base.FileConfigLevel(
        config_type=CONFIG_TYPE_UNIT, append_level=False),
    ]
CONFIG_HANDLER_UNIT = brokkr.config.base.ConfigHandler(
    config_type=CONFIG_TYPE_UNIT,
    config_levels=CONFIG_LEVELS_UNIT,
    )


METADATA_NAME = "metadata"
EMPTY_VARS_METADATA = [
    "name_full", "author", "description", "homepage", "repo", "version"]
EMPTY_VARS_METADATA_DICT = {key: "" for key in EMPTY_VARS_METADATA}

DEFAULT_CONFIG_METADATA = {
    "name": "mjolnir",
    **EMPTY_VARS_METADATA_DICT,
    "brokkr_version_min": "0.3.0",
    "sindri_version_min": "0.3.0",
    }

CONFIG_TYPE_METADATA = brokkr.config.base.ConfigType(
    METADATA_NAME,
    defaults=DEFAULT_CONFIG_METADATA,
    preset_config_path=SYSTEM_CONFIG["system_path"],
    )
CONFIG_LEVELS_METADATA = [
    brokkr.config.base.FileConfigLevel(
        name=LEVEL_NAME_SYSTEM, config_type=CONFIG_TYPE_METADATA,
        preset=True, append_level=False),
    brokkr.config.base.FileConfigLevel(
        config_type=CONFIG_TYPE_METADATA, append_level=False),
    ]
CONFIG_HANDLER_METADATA = brokkr.config.base.ConfigHandler(
    config_type=CONFIG_TYPE_METADATA,
    config_levels=CONFIG_LEVELS_METADATA,
    )


LOG_NAME = "log"
LOG_FORMAT_DETAILED = ("{asctime}.{msecs:0>3.0f} | {levelname} | {name} | "
                       "{message} (T+{relativeCreated:.0f} ms)")
DEFAULT_LOG_LEVEL = "INFO"

DEFAULT_CONFIG_LOG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "detailed": {
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "format": LOG_FORMAT_DETAILED,
            "style": "{",
            },
        },
    "handlers": {
        "file": {
            "backupCount": 10,
            "class": "logging.handlers.RotatingFileHandler",
            "filename":
                (OUTPUT_PATH_DEFAULT / "log"
                 / (PACKAGE_NAME + "_{system_name}_{unit_number:0>2}.log"))
                .as_posix(),
            "formatter": "detailed",
            "level": DEFAULT_LOG_LEVEL,
            "maxBytes": int(1e7),
            },
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "detailed",
            "level": DEFAULT_LOG_LEVEL,
            "stream": "ext://sys.stdout",
            },
        },
    "root": {
        "handlers": ["file", "console"],
        "level": DEFAULT_LOG_LEVEL,
        },
    }

CONFIG_TYPE_LOG = brokkr.config.base.ConfigType(
    LOG_NAME,
    defaults=DEFAULT_CONFIG_LOG,
    config_version=None,
    preset_config_path=SYSTEM_CONFIG["system_path"],
    )
CONFIG_LEVELS_LOG = [
    brokkr.config.base.FileConfigLevel(
        name=LEVEL_NAME_COMMON, config_type=CONFIG_TYPE_LOG, preset=True),
    brokkr.config.base.FileConfigLevel(
        name=LEVEL_NAME_PACKAGE, config_type=CONFIG_TYPE_LOG, preset=True),
    brokkr.config.base.FileConfigLevel(
        config_type=CONFIG_TYPE_LOG, append_level=False),
    ]
CONFIG_HANDLER_LOG = brokkr.config.base.ConfigHandler(
    config_type=CONFIG_TYPE_LOG,
    config_levels=CONFIG_LEVELS_LOG,
    )


STATIC_NAME = "static"
DEFAULT_CONFIG_STATIC = {
    "general": {
        "ip_sensor": "",
        "na_marker": "NA",
        "output_path_client": OUTPUT_PATH_DEFAULT.as_posix(),
        "output_filename_client":
            "{output_type}_{system_name}_{unit_number:0>2}_{utc_date!s}.csv",
        },
    "link": {
        "local_port": 22,
        "server_hostname": "",
        "server_port": 22,
        "server_username": "",
        "tunnel_port_offset": 10000,
        },
    "monitor": {
        "filename_args": {"output_type": "telemetry"},
        "hs_port": 8084,
        "output_path_client": Path("telemetry").as_posix(),
        "sleep_interval_s": 0.5,
        "sunsaver_pid_list": [],
        "sunsaver_port": "",
        "sunsaver_start_offset": 0,
        "sunsaver_unit": 1,
        },
    }
PATH_VARIABLES_STATIC = [
    ("general", "output_path_client"), ("monitor", "output_path_client")]

CONFIG_TYPE_STATIC = brokkr.config.base.ConfigType(
    STATIC_NAME,
    defaults=DEFAULT_CONFIG_STATIC,
    path_variables=PATH_VARIABLES_STATIC,
    preset_config_path=SYSTEM_CONFIG["system_path"],
    )
CONFIG_LEVELS_STATIC = [
    brokkr.config.base.FileConfigLevel(
        name=LEVEL_NAME_COMMON, config_type=CONFIG_TYPE_STATIC, preset=True),
    brokkr.config.base.FileConfigLevel(
        name=LEVEL_NAME_PACKAGE, config_type=CONFIG_TYPE_STATIC, preset=True),
    brokkr.config.base.FileConfigLevel(
        config_type=CONFIG_TYPE_STATIC, append_level=False),
    ]
CONFIG_HANDLER_STATIC = brokkr.config.base.ConfigHandler(
    config_type=CONFIG_TYPE_STATIC,
    config_levels=CONFIG_LEVELS_STATIC,
    )


DYNAMIC_NAME = "dynamic"
DEFAULT_CONFIG_DYNAMIC = {
    "monitor": {
        "monitor_interval_s": 60,
        "hs_timeout_s": 2,
        "ping_timeout_s": 1,
        },
    }

CONFIG_TYPE_DYNAMIC = brokkr.config.base.ConfigType(
    DYNAMIC_NAME,
    defaults=DEFAULT_CONFIG_DYNAMIC,
    preset_config_path=SYSTEM_CONFIG["system_path"],
    )
CONFIG_LEVELS_DYNAMIC = [
    brokkr.config.base.FileConfigLevel(
        name=LEVEL_NAME_COMMON, config_type=CONFIG_TYPE_DYNAMIC, preset=True),
    brokkr.config.base.FileConfigLevel(
        name=LEVEL_NAME_PACKAGE, config_type=CONFIG_TYPE_DYNAMIC, preset=True),
    brokkr.config.base.FileConfigLevel(
        name=LEVEL_NAME_REMOTE, config_type=CONFIG_TYPE_DYNAMIC,
        extension=brokkr.config.base.EXTENSION_JSON),
    brokkr.config.base.FileConfigLevel(config_type=CONFIG_TYPE_DYNAMIC),
    ]
CONFIG_HANDLER_DYNAMIC = brokkr.config.base.ConfigHandler(
    config_type=CONFIG_TYPE_DYNAMIC,
    config_levels=CONFIG_LEVELS_DYNAMIC,
    )


CONFIG_HANDLERS = {
    brokkr.config.systemhandler.SYSTEM_NAME: (
        brokkr.config.systemhandler.CONFIG_HANDLER_SYSTEM),
    UNIT_NAME: CONFIG_HANDLER_UNIT,
    METADATA_NAME: CONFIG_HANDLER_METADATA,
    LOG_NAME: CONFIG_HANDLER_LOG,
    STATIC_NAME: CONFIG_HANDLER_STATIC,
    DYNAMIC_NAME: CONFIG_HANDLER_DYNAMIC,
    }


CONFIG_LEVEL_NAMES = {
    config_level.name for handler in CONFIG_HANDLERS.values()
    for config_level in handler.config_levels.values()}
