"""
Network-related utility functions.
"""

# Standard library imports
import errno
import logging
import platform
import socket
import subprocess

# Local imports
import brokkr.utils.log


BUFFER_SIZE_DEFAULT = 4096

TIMEOUT_S_DEFAULT = 2
SUBPROCESS_TIMEOUT_EXTRA = 2

PING_COUNT_PARAM = "-n" if platform.system().lower() == "windows" else "-c"

ERROR_CODES_ADDRESS_LINK_DOWN = {
    getattr(errno, "EADDRNOTAVAIL", None),
    getattr(errno, "WSAEADDRNOTAVAIL", None),
    }

LOGGER = logging.getLogger(__name__)
LOG_HELPER = brokkr.utils.log.LogHelper(LOGGER)


def ping(
        host,
        count=1,
        timeout_s=TIMEOUT_S_DEFAULT,
        record_output=False,
        ):
    # Set the correct option for the number of packets based on platform.
    if platform.system().lower() == "windows":
        count_param = "-n"
    else:
        count_param = "-c"

    # Build the command, e.g. ping -c 1 -w 1 10.10.10.1
    command = ["ping", count_param, str(count), "-w", str(timeout_s), host]
    LOGGER.debug("Running ping command %s ...", " ".join(command))
    if record_output:
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

    ping_output = subprocess.run(
        command,
        timeout=timeout_s + SUBPROCESS_TIMEOUT_EXTRA,
        check=False,
        **extra_args,
        )
    return ping_output


def recieve_udp(
        host,
        port,
        buffer_size=BUFFER_SIZE_DEFAULT,
        timeout_s=TIMEOUT_S_DEFAULT,
        ):
    address_tuple = (host, port)

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        try:
            sock.settimeout(timeout_s)
            sock.bind(address_tuple)
            LOGGER.debug("Listening on socket %r", sock)
        except OSError as e:
            if not e.errno or e.errno not in ERROR_CODES_ADDRESS_LINK_DOWN:
                LOGGER.error("%s connecting to UDP socket: %s",
                             type(e).__name__, e)
                LOG_HELPER.log(socket=sock, address=address_tuple)
            else:
                LOGGER.debug("Suppressing address-related %s "
                             "connecting to UDP socket: %s",
                             type(e).__name__, e)
                LOG_HELPER.log("debug", socket=sock, address=address_tuple)
            return None
        except Exception as e:
            LOGGER.error("%s connecting to UDP socket: %s",
                         type(e).__name__, e)
            LOG_HELPER.log(socket=sock, address=address_tuple)
            return None

        try:
            datagram = sock.recv(buffer_size)
            LOGGER.debug("Data recieved: %r", datagram)
        except socket.timeout:
            LOGGER.debug("UDP socket timed out in %s s while waiting for data",
                         timeout_s)
            LOG_HELPER.log("debug", socket=sock, address=address_tuple)
            return None
        except Exception as e:
            LOGGER.error("%s recieving UDP datagram: %s",
                         type(e).__name__, e)
            LOG_HELPER.log(socket=sock, address=address_tuple)
            return None

        return datagram
