"""
Configuration to run Brokkr as a service for supported platforms (Linux).
"""

# Standard library imports
import sys

# Local imports
from brokkr.config.main import CONFIG
from brokkr.config.metadata import METADATA
from brokkr.config.mode import MODE_CONFIG
from brokkr.config.systempath import SYSTEMPATH_CONFIG
from brokkr.config.unit import UNIT_CONFIG


# Set the system path based on the current system settings
CURRENT_SYSTEM_ALIAS = SYSTEMPATH_CONFIG["default_system"]
SYSTEM_OVERRIDE_PATH = SYSTEMPATH_CONFIG["system_path_override"]

# Get system fullname
SYSTEM_FULLNAME = METADATA["name_full"] or METADATA["name"] or "Unknown System"

# Set system install name and CLI parameter
if SYSTEM_OVERRIDE_PATH:
    SYSTEM_NAME = f'{METADATA["name"] or "unknown"}_override'
    SYSTEM_PARAMETER = f"--system-path {SYSTEM_OVERRIDE_PATH}"
elif CURRENT_SYSTEM_ALIAS:
    SYSTEM_NAME = CURRENT_SYSTEM_ALIAS
    SYSTEM_PARAMETER = f"--system {CURRENT_SYSTEM_ALIAS}"
else:
    SYSTEM_NAME = CURRENT_SYSTEM_ALIAS
    SYSTEM_PARAMETER = ""

# Set mode CLI parameter
MODE_PARAMETER = ""
if MODE_CONFIG["mode"] not in {"", "default"}:
    MODE_PARAMETER = f'--mode {MODE_CONFIG["mode"]}'

SERVICE_NAME_TEMPLATE = "{package_name}-{system_name}-{mode}.service"
AUTOSSH_SERVICE_NAME = SERVICE_NAME_TEMPLATE.format(
    package_name="autossh", system_name=SYSTEM_NAME, mode=MODE_CONFIG["mode"])
BROKKR_SERVICE_NAME = SERVICE_NAME_TEMPLATE.format(
    package_name="brokkr", system_name=SYSTEM_NAME, mode=MODE_CONFIG["mode"])

AUTOSSH_REMOTE_PORT = (
    CONFIG["autossh"]["tunnel_port_offset"] + UNIT_CONFIG["number"])


BROKKR_SERVICE_DEFAULTS = {
    "Unit": {
        "Description": f"Brokkr IoT Sensor Client for {SYSTEM_FULLNAME}",
        "Wants": " ".join([
            "systemd-time-wait-sync.service",
            "systemd-timesyncd.service sshd.service",
            ]),
        "After": " ".join([
            "time-sync.target",
            "multi-user.target",
            "network.target",
            "sshd.service",
            "systemd-time-wait-sync.service",
            "systemd-timesyncd.service",
            AUTOSSH_SERVICE_NAME,
            ]),
        },
    "Service": {
        "Type": "simple",
        "ExecStart": (
            f"{sys.executable} -m brokkr "
            f"{SYSTEM_PARAMETER} {MODE_PARAMETER} start"
            ),
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
        "Description": f"Brokkr AutoSSH tunnel for {SYSTEM_FULLNAME}",
        "Wants": "sshd.service",
        "After": " ".join([
            "multi-user.target"
            "network.target"
            "sshd.service",
            ]),
        "Before": BROKKR_SERVICE_NAME,
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
