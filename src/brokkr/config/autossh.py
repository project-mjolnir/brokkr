"""
Configuration to run Brokkr as a service for supported platforms (Linux).
"""


AUTOSSH_SERVICE_FILENAME = "autossh-brokkr.service"

AUTOSSH_SERVICE_DEFAULTS = {
    "Unit": {
        "Description": "AutoSSH Tunnel Service",
        "Wants": "network-online.target sshd.service",
        "After": "network-online.target multi-user.target sshd.service",
        "Before": "brokkr.service",
        },
    "Service": {
        "Type": "simple",
        "Environment": "AUTOSSH_GATETIME=0",
        "ExecStart": (
            '/usr/bin/autossh -M 0 -o "StrictHostKeyChecking no" '
            '-o "CheckHostIP no" -o "UserKnownHostsFile /dev/null" '
            '-o "ExitOnForwardFailure yes" -o "TCPKeepAlive yes" '
            '-o "ServerAliveInterval 60" -o "ServerAliveCountMax 2" '
            '-N -T -R 10000:localhost:22 proxy'
            ),
        "Restart": "always",
        "RestartSec": str(60),
        "TimeoutStartSec": str(30),
        "TimeoutStopSec": str(30),
        },
    }

AUTOSSH_SERVICES_ENABLE = ("sshd.service", )
AUTOSSH_SERVICES_DISABLE = ()
