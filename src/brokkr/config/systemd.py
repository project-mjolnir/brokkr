"""
Configuration to run Brokkr as a service for supported platforms (Linux).
"""

# Standard library imports
import collections
import copy
import configparser
from pathlib import Path
import os
import sys

# Local imports
import brokkr.utils.misc


PlatformConfig = collections.namedtuple(
    "PlatformConfig",
    ("full_name", "install_path", "configparser_options", "default_contents"))

INSTALL_PATH_SYSTEMD = Path("/etc") / "systemd" / "system"

CONFIGPARSER_OPTIONS_SYSTEMD = {
    "delimiters": ("=", ),
    "comment_prefixes": ("#", ),
    "empty_lines_in_values": False,
    }

DEFAULT_CONTENTS_SYSTEMD = {
    "Unit": {
        "After": "multi-user.target",
        },
    "Service": {
        "Type": "simple",
        "Restart": "on-failure",
        "User": brokkr.utils.misc.get_actual_username(),
        "Group": brokkr.utils.misc.get_actual_username(),
        },
    "Install": {
        "WantedBy": "multi-user.target",
        },
    }

SUPPORTED_PLATFORMS = {
    "linux": PlatformConfig(
        "Linux (systemd)", INSTALL_PATH_SYSTEMD, CONFIGPARSER_OPTIONS_SYSTEMD,
        DEFAULT_CONTENTS_SYSTEMD),
    }


def get_platform_config(platform=None):
    if platform is None:
        platform = sys.platform
    platform_config = None
    for plat in SUPPORTED_PLATFORMS:
        if platform.startswith(plat):
            platform_config = SUPPORTED_PLATFORMS[plat]
            break
    if platform_config is None:
        raise ValueError(
            "Service installation only currently supported on "
            f"{list(SUPPORTED_PLATFORMS.keys())}, not on {platform}.")
    return platform_config


def generate_systemd_config(config_dict, platform=None):
    platform_config = get_platform_config(platform)
    service_config = configparser.ConfigParser(
        **platform_config.configparser_options)
    # Make configparser case sensitive
    service_config.optionxform = str
    config_dict = brokkr.utils.misc.update_dict_recursive(
        copy.deepcopy(platform_config.default_contents), config_dict)
    service_config.read_dict(config_dict)
    return service_config


def write_systemd_config(service_config, filename,
                         platform=None, output_path=None):
    platform_config = get_platform_config(platform)
    if output_path is None:
        output_path = platform_config.install_path
    output_path = Path(output_path)
    os.makedirs(output_path.parent, mode=0o755, exist_ok=True)
    with open(output_path / filename, "w",
              encoding="utf-8", newline="\n") as service_file:
        service_config.write(service_file)
    os.chmod(output_path, 0o644)
    os.chown(output_path, 0, 0)

    return output_path
