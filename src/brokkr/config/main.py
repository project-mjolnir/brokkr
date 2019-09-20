"""
Main configuration for Brokkr; loaded after logging starts.
"""

# Standard library imports
import logging
from pathlib import Path

# Local imports
import brokkr.config.base


# General static constants
VERSION = 1
OUTPUT_PATH = Path("~") / "data"
DEFAULT_CONFIG = {
    "version": VERSION,
    brokkr.config.base.LOCAL_OVERRIDE: False,
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
    "network": {
        "name": "test",
        "longname": "Test Network (Default)",
        },
    "site": {
        "name_prefix": "hamma",
        "number": "",
        "description": "Test Sensor (Default)",
        "network": "test",
        },
    }
PATH_VARIABLES = (("general", "output_path"), ("monitor", "output_path"))
CONFIG_HANDLER = brokkr.config.base.ConfigHandler(
    "main", DEFAULT_CONFIG, path_variables=PATH_VARIABLES, write_sections=True)

logger = logging.getLogger(__name__)


logger.debug("Reading Brokkr configs at %s",
             CONFIG_HANDLER.config_dir.as_posix())

# Master config dict; currently static
CONFIGS = CONFIG_HANDLER.read_configs()
logger.debug("Loaded configs: %s", CONFIGS)

CONFIG = CONFIG_HANDLER.render_config(CONFIGS)
logger.debug("Rendered config: %s", CONFIG)
