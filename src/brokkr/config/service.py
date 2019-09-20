"""
Configuration to run Brokkr as a service for supported platforms (Linux).
"""

# Standard library imports
import collections
import configparser
import getpass
import logging
from pathlib import Path
import os
import subprocess
import sys


def get_actual_username():
    try:
        username = os.environ["SUDO_USER"]
        if username:
            return username
    except KeyError:
        pass
    return getpass.getuser()


PlatformConfig = collections.namedtuple(
    "PlatformConfig",
    ("full_name", "install_path", "configparser_options", "default_contents"))

INSTALL_PATH_SYSTEMD = Path("/etc") / "systemd" / "system" / "brokkr.service"

CONFIGPARSER_OPTIONS_SYSTEMD = {
    "delimiters": ("=", ),
    "comment_prefixes": ("#", ),
    "empty_lines_in_values": False,
    }

DEFAULT_CONTENTS_SYSTEMD = {
    "Unit": {
        "Description": "Brokkr Remote Client Service",
        "Wants": ("network-online.target systemd-time-wait-sync.service "
                  "systemd-timesyncd.service" "sshd.service"),
        "After": (
            "time-sync.target network-online.target multi-user.target "
            "sshd.service systemd-time-wait-sync.service "
            "systemd-timesyncd.service"
            ),
        },
    "Service": {
        "Type": "simple",
        "ExecStart": f"{sys.executable} -m brokkr start",
        "Restart": "on-failure",
        "RestartSec": str(15),
        "TimeoutStartSec": str(30),
        "TimeoutStopSec": str(30),
        "User": get_actual_username(),
        "Group": get_actual_username(),
        },
    "Install": {
        "WantedBy": "multi-user.target",
        },
    }

SUPPORTED_PLATFORMS = {
    "linux": PlatformConfig(
        "Linux", INSTALL_PATH_SYSTEMD,
        CONFIGPARSER_OPTIONS_SYSTEMD, DEFAULT_CONTENTS_SYSTEMD),
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


def generate_service_config(platform=None):
    platform_config = get_platform_config(platform)
    service_config = configparser.ConfigParser(
        **platform_config.configparser_options)
    # Make configparser case sensitive
    service_config.optionxform = str
    service_config.read_dict(platform_config.default_contents)

    return service_config


def write_service_config(service_config, platform=None, output_path=None):
    platform_config = get_platform_config(platform)
    if output_path is None:
        output_path = platform_config.install_path
    os.makedirs(Path(output_path).parent, mode=0o755, exist_ok=True)
    with open(output_path, mode="w", encoding="utf-8") as service_file:
        service_config.write(service_file)
    os.chmod(output_path, 0o644)
    os.chown(output_path, 0, 0)

    return output_path


def install_service_config(platform=None, output_path=None, verbose=False):
    logging.basicConfig(stream=sys.stdout,
                        level="DEBUG" if verbose else "INFO")
    logging.debug("Installing Brokkr service...")
    platform_config = get_platform_config(platform)
    logging.debug("Using platform config settings: %s", platform_config)
    logging.debug("Generating service configuration file...")
    service_config = generate_service_config(platform)
    logging.debug("Writing service configuration file to %s",
                  output_path if output_path else platform_config.install_path)
    output_path = write_service_config(service_config, platform, output_path)
    logging.debug("Reloading systemd daemon...")
    subprocess.run(("systemctl", "daemon-reload"), timeout=5, check=True)
    logging.debug("Disabling chrony (if present)...")
    subprocess.run(("systemctl", "disable", "chronyd"), timeout=5, check=False)
    logging.debug("Disabling ntpd (if present)...")
    subprocess.run(("systemctl", "disable", "ntpd"), timeout=5, check=False)
    logging.debug("Enabling systemd-timesyncd...")
    subprocess.run(("systemctl", "enable", "systemd-timesyncd"),
                   timeout=5, check=True)
    logging.debug("Enabling sshd...")
    subprocess.run(("systemctl", "enable", "sshd"), timeout=5, check=True)
    logging.debug("Enabling Brokkr service...")
    subprocess.run(("systemctl", "enable", "brokkr"), timeout=5, check=True)
    logging.info("Successfully installed Brokkr service to %s", output_path)
    return service_config
