"""
Routines to get status information from a HAMMA2 sensor over Ethernet.
"""

# Standard library imports
import platform
import subprocess

# Local imports
from config import CONFIG


def ping(host=CONFIG["general"]["sensor_ip"],
         timeout=CONFIG["monitor"]["sensor"]["ping_timeout_s"]):
    # Set the correct option for the number of packets based on platform.
    if platform.system().lower() == "windows":
        param = "-n"
    else:
        param = "-c"

    # Build the command, e.g. ``ping -c 1 google.com``
    command = ["ping", param, "1", "-w", str(timeout), host]

    return subprocess.run(command, stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL).returncode
