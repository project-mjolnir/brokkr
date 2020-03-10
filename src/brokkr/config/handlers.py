"""
Config handler setup for Brokkr's main managed configs.
"""

# Local imports
import brokkr.config.base
from brokkr.constants import (
    CONFIG_NAME_LOG,
    CONFIG_NAME_METADATA,
    CONFIG_NAME_MODE,
    CONFIG_NAME_MAIN,
    CONFIG_NAME_SYSTEMPATH,
    CONFIG_NAME_UNIT,
    CONFIG_PATH_LOCAL,
    CONFIG_VERSION,
    LEVEL_NAME_LOCAL,
    LEVEL_NAME_SYSTEM,
    LEVEL_NAME_SYSTEM_CLIENT,
    OUTPUT_PATH_DEFAULT,
    OUTPUT_SUBPATH_LOG,
    OUTPUT_SUBPATH_MONITOR,
    PACKAGE_NAME,
    SYSTEM_SUBPATH_CONFIG,
    )
from brokkr.config.mode import MODE_CONFIG
from brokkr.config.systempath import SYSTEMPATH_CONFIG
import brokkr.config.systempathhandler
import brokkr.utils.misc


SYSTEM_PATH = brokkr.utils.misc.get_system_path(SYSTEMPATH_CONFIG)
SYSTEM_CONFIG_PATH = SYSTEM_PATH / SYSTEM_SUBPATH_CONFIG

MODE_OVERLAYS = MODE_CONFIG[MODE_CONFIG["mode"]]


CONFIG_HANDLER_FACTORY = brokkr.config.base.ConfigHandlerFactory(
    level_presets=brokkr.config.base.CONFIG_LEVEL_PRESETS,
    overlays=MODE_OVERLAYS,
    local_config_path=CONFIG_PATH_LOCAL,
    preset_config_path=SYSTEM_CONFIG_PATH,
    config_version=CONFIG_VERSION,
    )


DEFAULT_CONFIG_UNIT = {
    "number": 0,
    "network_interface": "wlan0",
    "site_description": "",
    }

CONFIG_HANDLER_UNIT = CONFIG_HANDLER_FACTORY.create_config_handler(
    name=CONFIG_NAME_UNIT,
    config_levels=[
        LEVEL_NAME_SYSTEM,
        LEVEL_NAME_LOCAL,
        ],
    defaults=DEFAULT_CONFIG_UNIT,
    )


EMPTY_VARS_METADATA = [
    "name_full", "author", "description", "homepage", "repo", "version"]
EMPTY_VARS_METADATA_DICT = {key: "" for key in EMPTY_VARS_METADATA}

DEFAULT_CONFIG_METADATA = {
    "name": "mjolnir",
    **EMPTY_VARS_METADATA_DICT,
    "brokkr_version_min": "0.3.0",
    "sindri_version_min": "0.3.0",
    }

CONFIG_HANDLER_METADATA = CONFIG_HANDLER_FACTORY.create_config_handler(
    name=CONFIG_NAME_METADATA,
    config_levels=[
        LEVEL_NAME_SYSTEM,
        ],
    defaults=DEFAULT_CONFIG_METADATA,
    preset_config_path=SYSTEM_PATH,
    )


LOG_FORMAT_DETAILED = ("{asctime}.{msecs:0>3.0f} | {levelname} | {processName}"
                       " | {name} | {message} (T+{relativeCreated:.0f} ms)")
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
                (OUTPUT_SUBPATH_LOG
                 / (PACKAGE_NAME + "_{system_name}_{unit_number:0>4}.log"))
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

CONFIG_HANDLER_LOG = CONFIG_HANDLER_FACTORY.create_config_handler(
    name=CONFIG_NAME_LOG,
    config_levels=[
        LEVEL_NAME_SYSTEM_CLIENT,
        LEVEL_NAME_LOCAL,
        ],
    defaults=DEFAULT_CONFIG_LOG,
    )


DEFAULT_CONFIG_MAIN = {
    "general": {
        "ip_local": "",
        "ip_sensor": "",
        "na_marker": "NA",
        "output_filename_client":
            "{output_type}_{system_name}_{unit_number:0>4}_{utc_date!s}.csv",
        "output_path_client": OUTPUT_PATH_DEFAULT.as_posix(),
        "system_prefix": "",
        "worker_shutdown_wait_s": 10,
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
        "hs_timeout_s": 2,
        "interval_s": 60,
        "output_path_client": OUTPUT_SUBPATH_MONITOR.as_posix(),
        "ping_timeout_s": 1,
        "sunsaver_pid_list": [],
        "sunsaver_port": "",
        "sunsaver_start_offset": 0,
        "sunsaver_unit": 1,
        },
    }

CONFIG_HANDLER_MAIN = CONFIG_HANDLER_FACTORY.create_config_handler(
    name=CONFIG_NAME_MAIN,
    config_levels=[
        LEVEL_NAME_SYSTEM,
        LEVEL_NAME_LOCAL,
        ],
    defaults=DEFAULT_CONFIG_MAIN,
    path_variables=[("general", "output_path_client"),
                    ("monitor", "output_path_client")],
    )


CONFIG_HANDLERS = {
    CONFIG_NAME_METADATA: CONFIG_HANDLER_METADATA,
    CONFIG_NAME_UNIT: CONFIG_HANDLER_UNIT,
    CONFIG_NAME_LOG: CONFIG_HANDLER_LOG,
    CONFIG_NAME_MAIN: CONFIG_HANDLER_MAIN,
    }
CONFIG_LEVEL_NAMES = {
    config_level.name for handler in CONFIG_HANDLERS.values()
    for config_level in handler.config_levels.values()}

ALL_CONFIG_HANDLERS = {
    **{CONFIG_NAME_SYSTEMPATH:
       brokkr.config.systempathhandler.CONFIG_HANDLER_SYSTEMPATH},
    **{CONFIG_NAME_MODE:
       brokkr.config.modehandler.CONFIG_HANDLER_MODE},
    **CONFIG_HANDLERS,
    }
ALL_CONFIG_LEVEL_NAMES = {
    config_level.name for handler in ALL_CONFIG_HANDLERS.values()
    for config_level in handler.config_levels.values()}
