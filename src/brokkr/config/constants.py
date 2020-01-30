"""
General shared configuration constants for Brokkr.
"""

from pathlib import Path


PACKAGE_NAME = "brokkr"

# Path for general Brokkr output
OUTPUT_PATH_DEFAULT = Path("~", PACKAGE_NAME)
OUTPUT_PATH_DEFAULT_EXPANDED = OUTPUT_PATH_DEFAULT.expanduser()
