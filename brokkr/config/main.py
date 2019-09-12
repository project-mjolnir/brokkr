"""
Main configuration for Brokkr; loaded after logging starts.
"""

# Standard library imports
import logging
import os
from pathlib import Path

# Local imports
import config.base


# General static constants
OUTPUT_PATH = Path("~") / "data"
DEFAULT_CONFIG = {
    config.base.LOCAL_OVERRIDE: False,
    "general": {
        "name_prefix": "hamma",
        "output_path": str(OUTPUT_PATH).replace(os.sep, "/"),
        "sensor_ip": "10.10.10.1",
        },
    "monitor": {
        "interval_log_s": 60,
        "interval_sleep_s": 1,
        "output_path": str(OUTPUT_PATH / "monitoring").replace(os.sep, "/"),
        "sensor": {
            "timeout_ping_s": 1,
            },
        "sunsaver": {
            "pid_list": [24597, ],
            "port": "",
            "start_offset": 0x0008,
            "unit": 0x01,
            },
        },
    "network": {
        "name": "test",
        "longname": "Test Network (Default)",
        },
    "site": {
        "number": "",
        "description": "Test Sensor (Default)",
        "network": "test",
        },
    }
PATH_VARIABLES = (("general", "output_path"), ("monitor", "output_path"))
CONFIG_HANDLER = config.base.ConfigHandler(
    "main", DEFAULT_CONFIG, path_variables=PATH_VARIABLES, write_sections=True)

logger = logging.getLogger(__name__)


logger.debug("Reading Brokkr configs at %s",
             str(CONFIG_HANDLER.config_dir).replace(os.sep, "/"))

# Master config dict; currently static
CONFIGS = CONFIG_HANDLER.read_configs()
logger.debug("Loaded configs: %s", CONFIGS)

CONFIG = CONFIG_HANDLER.render_config(CONFIGS)
logger.debug("Rendered config: %s", CONFIG)
