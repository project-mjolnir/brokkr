"""
Configuration to run Brokkr as a service for supported platforms (Linux).
"""

# Standard library imports
import sys

# Local imports
from brokkr.config.static import CONFIG
from brokkr.config.unit import UNIT_CONFIG
from brokkr.constants import PACKAGE_NAME


AUTOSSH_REMOTE_PORT = (
    CONFIG["link"]["tunnel_port_offset"] + UNIT_CONFIG["number"])


BROKKR_SERVICE_DEFAULTS = {
    "Unit": {
        "Description": f"Brokkr IoT Monitoring, Logging and Control Client",
        "Wants": (
            "network-online.target systemd-time-wait-sync.service "
            "systemd-timesyncd.service sshd.service "
            "autossh-brokkr.service"
            ),
        "After": (
            "time-sync.target network-online.target multi-user.target "
            "sshd.service systemd-time-wait-sync.service "
            "systemd-timesyncd.service autossh-brokkr.service"
            ),
        },
    "Service": {
        "Type": "simple",
        "ExecStart": f"{sys.executable} -m brokkr start",
        "Restart": "on-failure",
        "RestartSec": str(15),
        "TimeoutStartSec": str(30),
        "TimeoutStopSec": str(30),
        },
    }

BROKKR_SERVICE_KWARGS = {
    "service_filename": f"{PACKAGE_NAME}.service",
    "service_settings": BROKKR_SERVICE_DEFAULTS,
    "services_enable": ["systemd-timesyncd.service"],
    "services_disable": ["chronyd.service", "ntpd.service"],
    }


AUTOSSH_SERVICE_DEFAULTS = {
    "Unit": {
        "Description": "AutoSSH tunnel for Brokkr client",
        "Wants": "network-online.target sshd.service",
        "After": "network-online.target multi-user.target sshd.service",
        "Before": f"{PACKAGE_NAME}.service",
        },
    "Service": {
        "Type": "simple",
        "Environment": "AUTOSSH_GATETIME=0",
        "ExecStart": (
            '/usr/bin/autossh -M 0 -N -T -o "StrictHostKeyChecking no" '
            '-o "CheckHostIP no" -o "UserKnownHostsFile /dev/null" '
            '-o "ExitOnForwardFailure yes" -o "TCPKeepAlive yes" '
            '-o "ServerAliveInterval 60" -o "ServerAliveCountMax 3" '
            f'-R {AUTOSSH_REMOTE_PORT}:localhost:'
            f'{CONFIG["link"]["local_port"]} '
            f'{CONFIG["link"]["server_username"]}'
            f'{"@" if CONFIG["link"]["server_username"] else ""}'
            f'{CONFIG["link"]["server_hostname"]}'
            f':{CONFIG["link"]["server_port"]}'
            ),
        "Restart": "always",
        "RestartSec": str(60),
        "TimeoutStartSec": str(30),
        "TimeoutStopSec": str(30),
        },
    }

AUTOSSH_SERVICE_KWARGS = {
    "service_filename": f"autossh-{PACKAGE_NAME}.service",
    "service_settings": AUTOSSH_SERVICE_DEFAULTS,
    }
