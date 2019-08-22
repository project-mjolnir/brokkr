"""
Routines to get status information from a HAMMA2 sensor over Ethernet.
"""

import platform
import subprocess


def ping(host="10.10.10.1"):
    # Set the correct option for the number of packets based on platform.
    if platform.system().lower() == "windows":
        param = "-n"
    else:
        param = "-c"

    # Build the command, e.g. ``ping -c 1 google.com``
    command = ["ping", param, "1", "-w", "1", host]

    return subprocess.run(command, stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL).returncode == 0
