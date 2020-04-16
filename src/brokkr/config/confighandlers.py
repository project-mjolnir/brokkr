"""
Config handler setup for Brokkr's main managed configs.
"""

# Local imports
import brokkr.config.base
import brokkr.config.metadatahandler
from brokkr.config.metadata import METADATA
import brokkr.config.modehandler
from brokkr.config.mode import MODE_CONFIG
import brokkr.config.systempathhandler
from brokkr.config.systempath import SYSTEMPATH_CONFIG
from brokkr.constants import (
    CONFIG_NAME_LOG,
    CONFIG_NAME_MAIN,
    CONFIG_NAME_METADATA,
    CONFIG_NAME_MODE,
    CONFIG_NAME_PRESETS,
    CONFIG_NAME_SYSTEMPATH,
    CONFIG_NAME_UNIT,
    CONFIG_PATH_LOCAL,
    CONFIG_VERSION,
    LEVEL_NAME_LOCAL,
    LEVEL_NAME_SYSTEM,
    LEVEL_NAME_SYSTEM_CLIENT,
    METADATA_VARS,
    OUTPUT_PATH_DEFAULT,
    OUTPUT_SUBPATH_LOG,
    PACKAGE_NAME,
    SYSTEM_SUBPATH_CONFIG,
    SYSTEM_SUBPATH_PRESETS,
    )
import brokkr.utils.misc


SYSTEM_BASE_PATH = brokkr.utils.misc.get_system_path(SYSTEMPATH_CONFIG)


CONFIG_HANDLER_FACTORY = brokkr.config.base.ConfigHandlerFactory(
    overlays=MODE_CONFIG[MODE_CONFIG["mode"]],
    local_config_path=CONFIG_PATH_LOCAL / METADATA["name"],
    preset_config_path=SYSTEM_BASE_PATH / SYSTEM_SUBPATH_CONFIG,
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
            "encoding": "utf-8",
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
        "monitoring_pipeline_default": "",
        "na_marker": "NA",
        "output_filename_client":
            "{output_type}_{system_name}_{unit_number:0>4}_{utc_date!s}.csv",
        "output_path_client": OUTPUT_PATH_DEFAULT.as_posix(),
        "system_prefix": "",
        "worker_shutdown_wait_s": 10,
        },
    "autossh": {
        "local_port": 22,
        "server_hostname": "",
        "server_port": 22,
        "server_username": "",
        "tunnel_port_offset": 10000,
        },
    "steps": {},
    "pipelines": {},
    }

CONFIG_HANDLER_MAIN = CONFIG_HANDLER_FACTORY.create_config_handler(
    name=CONFIG_NAME_MAIN,
    config_levels=[
        LEVEL_NAME_SYSTEM,
        LEVEL_NAME_LOCAL,
        ],
    defaults=DEFAULT_CONFIG_MAIN,
    path_variables=[("general", "output_path_client")],
    )


DEFAULT_CONFIG_PRESETS = {
    "builtins": {
        "config_version": CONFIG_VERSION,
        "name": "builtins",
        "type": "builtin",
        "_dependencies": [],
        "inputs": {
            "current_time": {
                "_module_path": "brokkr.inputs.currenttime",
                "_class_name": "CurrentTimeInput",
                },
            "run_time": {
                "_module_path": "brokkr.inputs.runtime",
                "_class_name": "RunTimeInput",
                },
            },
        "outputs": {
            "csv_file": {
                "_module_path": "brokkr.outputs.csvfile",
                "_class_name": "CSVFileOutput",
                "output_path": "data",
                },
            "pretty_print": {
                "_module_path": "brokkr.outputs.print",
                "_class_name": "PrettyPrintOutput",
                },
            "print": {
                "_module_path": "brokkr.outputs.print",
                "_class_name": "PrintOutput",
                },
            },
        },
    }

CONFIG_PRESET_TEMPLATE = {
    "config_version": CONFIG_VERSION,
    "type": "device",
    "_dependencies": [],
    "metadata": {**{key: "" for key in METADATA_VARS},
                 "brokkr_version_min": "0.3.0", "brokkr_version_max": ""},
    "custom_types": {},
    "variables": {},
    "inputs": {},
    "outputs": {},
    "commands": {},
    }


CONFIG_HANDLER_PRESETS = CONFIG_HANDLER_FACTORY.create_config_handler(
    name=CONFIG_NAME_PRESETS,
    config_levels=[
        {brokkr.config.base.LEVEL_CLASS: brokkr.config.base.PresetsConfigLevel,
         brokkr.config.base.LEVEL_ARGS: {
             "filename_glob": "**/*.preset.toml",
             "key_name": "name",
             "path": (SYSTEM_BASE_PATH / SYSTEM_SUBPATH_PRESETS).as_posix(),
             "template": CONFIG_PRESET_TEMPLATE,
             "insert_items": [
                 ("inputs", "_dependencies"),
                 ("outputs", "_dependencies"),
                 ("commands", "_dependencies"),
                 ("data_types", "type_presets"),
                 ("inputs", "data_types"),
                 ],
             "logger": True,
             }},
        ],
    defaults=DEFAULT_CONFIG_PRESETS,

    )


ALL_CONFIG_HANDLERS = {
    CONFIG_NAME_SYSTEMPATH:
        brokkr.config.systempathhandler.CONFIG_HANDLER_SYSTEMPATH,
    CONFIG_NAME_MODE:
        brokkr.config.modehandler.CONFIG_HANDLER_MODE,
    CONFIG_NAME_METADATA:
        brokkr.config.metadatahandler.CONFIG_HANDLER_METADATA,
    CONFIG_NAME_UNIT: CONFIG_HANDLER_UNIT,
    CONFIG_NAME_LOG: CONFIG_HANDLER_LOG,
    CONFIG_NAME_MAIN: CONFIG_HANDLER_MAIN,
    CONFIG_NAME_PRESETS: CONFIG_HANDLER_PRESETS,
    }

ALL_CONFIG_LEVEL_NAMES = {
    config_level.name for handler in ALL_CONFIG_HANDLERS.values()
    for config_level in handler.config_levels.values()}
