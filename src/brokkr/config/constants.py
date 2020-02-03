"""
General shared configuration constants for Brokkr.
"""

from pathlib import Path


PACKAGE_NAME = "brokkr"


# Path for general Brokkr output
OUTPUT_PATH_DEFAULT = Path("~", PACKAGE_NAME)
OUTPUT_PATH_DEFAULT_EXPANDED = OUTPUT_PATH_DEFAULT.expanduser()

# Subpaths of output dir
OUTPUT_SUBPATH_LOG = Path("log")
OUTPUT_SUBPATH_MONITOR = Path("telemetry")
OUTPUT_SUBPATH_TEST = Path("test")

# Subpaths of system dir
SYSTEM_SUBPATH_CONFIG = Path("config")
