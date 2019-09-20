"""
Logging configuration for Brokkr; loaded first before anything else.
"""

# Standard library imports
from pathlib import Path

# Local imports
import brokkr.config.base


# General static constants
LOG_FORMAT_DETAILED = ("{asctime}.{msecs:0>3.0f} | {relativeCreated:.0f} | "
                       "{levelname} | {name} | {message}")
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_CONFIG = {
    brokkr.config.base.LOCAL_OVERRIDE: False,
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
            "backupCount": 11,
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
PATH_VARIABLES = (("handlers", "file", "filename"), )
CONFIG_HANDLER = brokkr.config.base.ConfigHandler(
    "log", DEFAULT_CONFIG, path_variables=PATH_VARIABLES, write_sections=False)

# Master config dict; currently static
LOG_CONFIGS = CONFIG_HANDLER.read_configs()

LOG_CONFIG = CONFIG_HANDLER.render_config(LOG_CONFIGS, remove_override=True)
