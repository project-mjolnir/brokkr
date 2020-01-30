"""
Configuration to run Brokkr as a service for supported platforms (Linux).
"""

# Standard library imports
import sys

# Local imports
from brokkr.config.constants import PACKAGE_NAME


SERVICE_FILENAME = PACKAGE_NAME + ".service"

SERVICE_DEFAULTS = {
    "Unit": {
        "Description": PACKAGE_NAME.title() + " Remote Client Service",
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

SERVICES_ENABLE = ("systemd-timesyncd.service", )
SERVICES_DISABLE = ("chronyd.service", "ntpd.service")
