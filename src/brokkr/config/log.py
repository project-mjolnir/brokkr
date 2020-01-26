"""
Logging configuration for Brokkr; loaded first before anything else.
"""

# Standard library imports
from pathlib import Path

# Local imports
import brokkr.config.base


# General static constants
LOG_FORMAT_DETAILED = ("{asctime}.{msecs:0>3.0f} | {levelname} | {name} | "
                       "{message} (T+{relativeCreated:.0f} ms)")
DEFAULT_LOG_LEVEL = "INFO"

DEFAULT_CONFIG = {
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
CONFIG_LEVELS = ["default", "override"]
PATH_VARIABLES = (("handlers", "file", "filename"), )

CONFIG_HANDLER = brokkr.config.base.ConfigHandler(
    "log",
    defaults=DEFAULT_CONFIG,
    config_levels=CONFIG_LEVELS,
    path_variables=PATH_VARIABLES,
    )

# Master config dict; currently static
LOG_CONFIGS = CONFIG_HANDLER.read_configs()

LOG_CONFIG = CONFIG_HANDLER.render_config(LOG_CONFIGS, remove_override=True)
