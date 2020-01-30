# -*- coding: utf-8 -*-
"""
Config handler setup for Brokkr's main managed configs.
"""

# Local imports
import brokkr.config.base
import brokkr.config.constants
from brokkr.config.system import SYSTEM_CONFIG
import brokkr.config.systemhandler


UNIT_NAME = "unit"
DEFAULT_CONFIG_UNIT = {
    "number": 0,
    "network_interface": "wlan0",
    "site_description": "",
    }
CONFIG_LEVELS_UNIT = ["defaults", "system", "local"]
CONFIG_HANDLER_UNIT = brokkr.config.base.ConfigHandler(
    UNIT_NAME,
    defaults=DEFAULT_CONFIG_UNIT,
    config_levels=CONFIG_LEVELS_UNIT,
    preset_config_path=SYSTEM_CONFIG["system_path"],
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
CONFIG_LEVELS_METADATA = ["defaults", "system", "local"]
CONFIG_HANDLER_METADATA = brokkr.config.base.ConfigHandler(
    METADATA_NAME,
    defaults=DEFAULT_CONFIG_METADATA,
    config_levels=CONFIG_LEVELS_METADATA,
    preset_config_path=SYSTEM_CONFIG["system_path"],
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
            "filename": (
                brokkr.config.constants.OUTPUT_PATH_DEFAULT
                / (brokkr.config.constants.PACKAGE_NAME + ".log")).as_posix(),
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
CONFIG_LEVELS_LOG = ["defaults", "common",
                     brokkr.config.constants.PACKAGE_NAME, "local"]
PATH_VARIABLES_LOG = (("handlers", "file", "filename"), )
CONFIG_HANDLER_LOG = brokkr.config.base.ConfigHandler(
    LOG_NAME,
    defaults=DEFAULT_CONFIG_LOG,
    config_levels=CONFIG_LEVELS_LOG,
    config_version=None,
    path_variables=PATH_VARIABLES_LOG,
    preset_config_path=SYSTEM_CONFIG["system_path"],
    )


STATIC_NAME = "static"
DEFAULT_CONFIG_STATIC = {
    "general": {
        "ip_sensor": "",
        "na_marker": "NA",
        },
    "monitor": {
        "hs_port": 8084,
        "output_path": (brokkr.config.constants.OUTPUT_PATH_DEFAULT
                        / "monitoring").as_posix(),
        "sunsaver_pid_list": [],
        "sleep_interval_s": 0.5,
        "sunsaver_port": "",
        "sunsaver_start_offset": 0,
        "sunsaver_unit": 1,
        },
    }
PATH_VARIABLES_STATIC = [("monitor", "output_path")]
CONFIG_LEVELS_STATIC = ["defaults", "common",
                        brokkr.config.constants.PACKAGE_NAME, "local"]
CONFIG_HANDLER_STATIC = brokkr.config.base.ConfigHandler(
    STATIC_NAME,
    defaults=DEFAULT_CONFIG_STATIC,
    config_levels=CONFIG_LEVELS_STATIC,
    path_variables=DEFAULT_CONFIG_STATIC,
    preset_config_path=SYSTEM_CONFIG["system_path"],
    )


DYNAMIC_NAME = "dynamic"
DEFAULT_CONFIG_DYNAMIC = {
    "monitor": {
        "monitor_interval_s": 60,
        "hs_timeout_s": 2,
        "ping_timeout_s": 1,
        },
    }
CONFIG_LEVELS_DYNAMIC = ["defaults", "common",
                         brokkr.config.constants.PACKAGE_NAME,
                         "remote", "local"]
CONFIG_HANDLER_DYNAMIC = brokkr.config.base.ConfigHandler(
    DYNAMIC_NAME,
    defaults=DEFAULT_CONFIG_DYNAMIC,
    config_levels=CONFIG_LEVELS_DYNAMIC,
    preset_config_path=SYSTEM_CONFIG["system_path"],
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
