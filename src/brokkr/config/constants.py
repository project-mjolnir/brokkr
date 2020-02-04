"""
General shared configuration constants for Brokkr.
"""

from pathlib import Path


PACKAGE_NAME = "brokkr"


# Path for general Brokkr output
OUTPUT_PATH_BASE = Path("~", PACKAGE_NAME)
OUTPUT_PATH_BASE_EXPANDED = OUTPUT_PATH_BASE.expanduser()

# Subpaths of output dir
OUTPUT_SUBPATH_LOG = Path("log")
OUTPUT_SUBPATH_MONITOR = Path("telemetry")

# Mode preset subpaths
OUTPUT_SUBPATH_DEFAULT = Path("data")
OUTPUT_SUBPATH_REALTIME = Path("realtime")
OUTPUT_SUBPATH_TEST = Path("test")

# Subpaths of system dir
SYSTEM_SUBPATH_CONFIG = Path("config")


# Config type names
CONFIG_NAME_SYSTEM = "system"
CONFIG_NAME_MODE = "mode"
CONFIG_NAME_METADATA = "metadata"
CONFIG_NAME_BOOTSTRAP = "bootstrap"
CONFIG_NAME_UNIT = "unit"
CONFIG_NAME_LOG = "log"
CONFIG_NAME_STATIC = "static"
CONFIG_NAME_DYNAMIC = "dynamic"

# Config level names
LEVEL_NAME_SYSTEM = "system"
LEVEL_NAME_SYSTEM_CLIENT = "client"
LEVEL_NAME_REMOTE = "remote"
