"""
Functions to get status information from a HAMMA2 sensor over Ethernet.
"""

# Standard library imports
import logging
import platform
import subprocess

# Local imports
from config.main import CONFIG


logger = logging.getLogger(__name__)


def ping(host=CONFIG["general"]["sensor_ip"],
         timeout=CONFIG["monitor"]["sensor"]["ping_timeout_s"]):
    # Set the correct option for the number of packets based on platform.
    if platform.system().lower() == "windows":
        count_param = "-n"
    else:
        count_param = "-c"

    # Build the command, e.g. ping -c 1 -w 1 10.10.10.1
    command = ["ping", count_param, "1", "-w", str(timeout), host]
    logger.debug("Running ping command: %s", " ".join(command))
    if logger.getEffectiveLevel() <= logging.DEBUG:
        extra_args = {
                      "stdout": subprocess.PIPE,
                      "stderr": subprocess.PIPE,
                      "encoding": "utf-8",
                      "errors": "surrogateescape",
                      }
    else:
        extra_args = {
                      "stdout": subprocess.DEVNULL,
                      "stderr": subprocess.DEVNULL,
                      }

    try:
        ping_output = subprocess.run(command, timeout=timeout + 1,
                                     **extra_args)
    except subprocess.TimeoutExpired:
        logger.info("Ping command subprocess timed out in %s s: %s",
                    timeout, " ".join(command))
        logger.debug("Details:", exc_info=1)
        return -1
    except Exception as e:
        logger.warning("%s running ping command %s: %s",
                       type(e).__name__, " ".join(command), e)
        logger.info("Details:", exc_info=1)
        return -9

    logger.debug("Ping command output: %s", ping_output)
    return ping_output.returncode
