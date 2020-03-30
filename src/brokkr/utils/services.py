"""
Configuration to run Brokkr as a service for supported platforms (Linux).
"""

# Standard library imports
import sys

# Local imports
from brokkr.config.main import CONFIG
from brokkr.config.metadata import METADATA
from brokkr.config.systempath import SYSTEMPATH_CONFIG
from brokkr.config.unit import UNIT_CONFIG
from brokkr.constants import PACKAGE_NAME


AUTOSSH_REMOTE_PORT = (
    CONFIG["autossh"]["tunnel_port_offset"] + UNIT_CONFIG["number"])

AUTOSSH_SERVICE_NAME = "autossh-{}.service".format(METADATA["name"])
BROKKR_SERVICE_NAME = "{package_name}-{system_name}.service".format(
    package_name=PACKAGE_NAME, system_name=METADATA["name"])

# Get system fullname
if METADATA["name_full"]:
    SYSTEM_FULLNAME = METADATA["name_full"]
elif METADATA["name_full"]:
    SYSTEM_FULLNAME = METADATA["name"]
else:
    SYSTEM_FULLNAME = "Unknown System"


# Set the system path based on the current system settings
CURRENT_SYSTEM_ALIAS = SYSTEMPATH_CONFIG["default_system"]
SYSTEM_OVERRIDE_PATH = SYSTEMPATH_CONFIG["system_path_override"]

if SYSTEM_OVERRIDE_PATH:
    SYSTEM_PARAMETER = f" --system-path {SYSTEM_OVERRIDE_PATH}"
elif CURRENT_SYSTEM_ALIAS:
    SYSTEM_PARAMETER = f" --system {CURRENT_SYSTEM_ALIAS}"
else:
    SYSTEM_PARAMETER = ""


BROKKR_SERVICE_DEFAULTS = {
    "Unit": {
        "Description": f"Brokkr IoT Sensor Client for {SYSTEM_FULLNAME}",
        "Wants": (
            "systemd-time-wait-sync.service "
            "systemd-timesyncd.service sshd.service"
            ),
        "After": (
            "time-sync.target multi-user.target network.target "
            "sshd.service systemd-time-wait-sync.service "
            f"systemd-timesyncd.service {AUTOSSH_SERVICE_NAME}"
            ),
        },
    "Service": {
        "Type": "simple",
        "ExecStart": f"{sys.executable} -m brokkr{SYSTEM_PARAMETER} start",
        "Restart": "on-failure",
        "RestartSec": str(15),
        "TimeoutStartSec": str(30),
        "TimeoutStopSec": str(30),
        },
    }

BROKKR_SERVICE_KWARGS = {
    "service_filename": BROKKR_SERVICE_NAME,
    "service_settings": BROKKR_SERVICE_DEFAULTS,
    "services_enable": ["systemd-timesyncd.service"],
    "services_disable": ["chronyd.service", "ntpd.service"],
    }


AUTOSSH_SERVICE_DEFAULTS = {
    "Unit": {
        "Description": "Brokkr AutoSSH tunnel for {SYSTEM_FULLNAME}",
        "Wants": "sshd.service",
        "After": "multi-user.target network.target sshd.service",
        "Before": f"{BROKKR_SERVICE_NAME}",
        },
    "Service": {
        "Type": "simple",
        "Environment": "AUTOSSH_GATETIME=0",
        "ExecStart": (
            '/usr/bin/autossh -M 0 -N -T -o "StrictHostKeyChecking no" '
            '-o "CheckHostIP no" -o "UserKnownHostsFile /dev/null" '
            '-o "ExitOnForwardFailure yes" -o "TCPKeepAlive yes" '
            '-o "ServerAliveInterval 60" -o "ServerAliveCountMax 3" '
            f'-p {CONFIG["autossh"]["server_port"]} '
            f'-R {AUTOSSH_REMOTE_PORT}:localhost:'
            f'{CONFIG["autossh"]["local_port"]} '
            f'{CONFIG["autossh"]["server_username"]}'
            f'{"@" if CONFIG["autossh"]["server_username"] else ""}'
            f'{CONFIG["autossh"]["server_hostname"]}'

            ),
        "Restart": "always",
        "RestartSec": str(60),
        "TimeoutStartSec": str(30),
        "TimeoutStopSec": str(30),
        },
    }

AUTOSSH_SERVICE_KWARGS = {
    "service_filename": AUTOSSH_SERVICE_NAME,
    "service_settings": AUTOSSH_SERVICE_DEFAULTS,
    }
