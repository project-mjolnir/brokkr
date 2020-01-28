# -*- coding: utf-8 -*-
"""
Config handler setup for Brokkr's main managed configs.
"""

# Standard library imports
from pathlib import Path

# Local imports
import brokkr.config.base


UNIT_NAME = "unit"
DEFAULT_CONFIG_UNIT = {
    "number": 0,
    "network_interface": "wlan0",
    "description": "",
    }
CONFIG_LEVELS_UNIT = ["defaults", "local"]
CONFIG_HANDLER_UNIT = brokkr.config.base.ConfigHandler(
    UNIT_NAME,
    defaults=DEFAULT_CONFIG_UNIT,
    config_levels=CONFIG_LEVELS_UNIT,
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
            "format": LOG_FORMAT_DETAILED,
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "style": "{",
            },
        },
    "handlers": {
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": DEFAULT_LOG_LEVEL,
            "formatter": "detailed",
            "filename": (Path("~") / "brokkr.log").as_posix(),
            "maxBytes": int(1e7),
            "backupCount": 10,
            },
        "console": {
            "class": "logging.StreamHandler",
            "level": DEFAULT_LOG_LEVEL,
            "formatter": "detailed",
            "stream": "ext://sys.stdout",
            },
        },
    "root": {
        "level": DEFAULT_LOG_LEVEL,
        "handlers": ["file", "console"],
        },
    }
CONFIG_LEVELS_LOG = ["defaults", "local"]
PATH_VARIABLES_LOG = (("handlers", "file", "filename"), )
CONFIG_HANDLER_LOG = brokkr.config.base.ConfigHandler(
    LOG_NAME,
    defaults=DEFAULT_CONFIG_LOG,
    config_levels=CONFIG_LEVELS_LOG,
    config_version=None,
    path_variables=PATH_VARIABLES_LOG,
    )


MAIN_NAME = "main"
OUTPUT_PATH = Path("~") / "data"
DEFAULT_CONFIG_MAIN = {
    "general": {
        "ip_sensor": "10.10.10.1",
        "name_prefix": "hamma",
        "output_path": OUTPUT_PATH.as_posix(),
        },
    "monitor": {
        "interval_log_s": 60,
        "interval_sleep_s": 1,
        "na_marker": "NA",
        "output_path": (OUTPUT_PATH / "monitoring").as_posix(),
        "sensor": {
            "hs_port": 8084,
            "hs_timeout_s": 2,
            "ping_timeout_s": 1,
            },
        "sunsaver": {
            "pid_list": [24597, ],
            "port": "",
            "start_offset": 0x0008,
            "unit": 0x01,
            },
        },
    }
CONFIG_LEVELS_MAIN = ["defaults", "remote", "local"]
PATH_VARIABLES_MAIN = (
    ("general", "output_path"),
    ("monitor", "output_path"),
    )
CONFIG_HANDLER_MAIN = brokkr.config.base.ConfigHandler(
    MAIN_NAME,
    defaults=DEFAULT_CONFIG_MAIN,
    config_levels=CONFIG_LEVELS_MAIN,
    path_variables=PATH_VARIABLES_MAIN,
    )


CONFIG_HANDLERS = {
    UNIT_NAME: CONFIG_HANDLER_UNIT,
    LOG_NAME: CONFIG_HANDLER_LOG,
    MAIN_NAME: CONFIG_HANDLER_MAIN,
    }
