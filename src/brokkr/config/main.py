"""
Main configuration for Brokkr; loaded after logging starts.
"""

# Standard library imports
import logging
from pathlib import Path

# Local imports
import brokkr.config.base


# General static constants
CONFIG_VERSION = 1
OUTPUT_PATH = Path("~") / "data"
DEFAULT_CONFIG = {
    "general": {
        "ip_sensor": "10.10.10.1",
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
    "site": {
        "name_prefix": "hamma",
        "number": "",
        "description": "Test Sensor (Default)",
        },
    }
PATH_VARIABLES = (("general", "output_path"), ("monitor", "output_path"))
CONFIG_HANDLER = brokkr.config.base.ConfigHandler(
    "main",
    defaults=DEFAULT_CONFIG,
    path_variables=PATH_VARIABLES,
    config_version=CONFIG_VERSION,
    )

logger = logging.getLogger(__name__)


logger.debug("Reading Brokkr config at %s",
             CONFIG_HANDLER.config_dir.as_posix())

# Master config dict; currently static
CONFIGS = CONFIG_HANDLER.read_configs()
logger.debug("Loaded config: %s", CONFIGS)

CONFIG = CONFIG_HANDLER.render_config(CONFIGS)
logger.info("Rendered config: %s", CONFIG)
