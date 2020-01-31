"""
Configuration to run Brokkr as a service for supported platforms (Linux).
"""

from brokkr.config.bootstrap import UNIT_CONFIG
from brokkr.config.constants import PACKAGE_NAME
from brokkr.config.static import CONFIG


AUTOSSH_REMOTE_PORT = (
    CONFIG["link"]["tunnel_port_offset"] + UNIT_CONFIG["number"])

AUTOSSH_SERVICE_FILENAME = f"autossh-{PACKAGE_NAME}.service"

AUTOSSH_SERVICE_DEFAULTS = {
    "Unit": {
        "Description": "AutoSSH Tunnel Service",
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

AUTOSSH_SERVICES_ENABLE = ()
AUTOSSH_SERVICES_DISABLE = ()
