"""
Functions to get status information from a HAMMA2 sensor over Ethernet.
"""

# Standard library imports
import logging
import platform
import socket
import subprocess

# Local imports
from brokkr.config.dynamic import DYNAMIC_CONFIG
from brokkr.config.static import CONFIG
import brokkr.utils.decode


BUFFER_SIZE_HS = 128

VARIABLE_PARAMS_HS = [
    {"name": "marker_val", "raw_type": "8s", "output_type": None},
    {"name": "sequence_count", "raw_type": "I", "output_type": "I"},
    {"name": "timestamp", "raw_type": "q", "output_type": "tm"},
    {"name": "crc_errors", "raw_type": "I", "output_type": "I"},
    {"name": "valid_packets", "raw_type": "I", "output_type": "I"},
    {"name": "bytes_read", "raw_type": "Q", "output_type": "B"},
    {"name": "bytes_written", "raw_type": "Q", "output_type": "B"},
    {"name": "bytes_remaining", "raw_type": "Q", "output_type": "B"},
    {"name": "packets_sent", "raw_type": "I", "output_type": "I"},
    {"name": "packets_dropped", "raw_type": "I", "output_type": "I"},
    ]

LOGGER = logging.getLogger(__name__)


def ping(host=CONFIG["general"]["ip_sensor"], timeout=None):
    if timeout is None:
        timeout = DYNAMIC_CONFIG["monitor"]["ping_timeout_s"]

    # Set the correct option for the number of packets based on platform.
    if platform.system().lower() == "windows":
        count_param = "-n"
    else:
        count_param = "-c"

    # Build the command, e.g. ping -c 1 -w 1 10.10.10.1
    command = ["ping", count_param, "1", "-w", str(timeout), host]
    LOGGER.debug("Running ping command %s ...", " ".join(command))
    if LOGGER.getEffectiveLevel() <= logging.DEBUG:
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
                                     check=False, **extra_args)
    except subprocess.TimeoutExpired:
        LOGGER.warning("Timeout in %s s running ping command %s",
                       timeout, " ".join(command))
        LOGGER.debug("Error details:", exc_info=1)
        return -1
    except Exception as e:
        LOGGER.error("%s running ping command %s: %s",
                     type(e).__name__, " ".join(command), e)
        LOGGER.info("Error details:", exc_info=1)
        return -9

    LOGGER.debug("Ping command output: %r", ping_output)
    return ping_output.returncode


def read_hs_packet(
        timeout=None,
        host_address=CONFIG["general"]["ip_local"],
        port=CONFIG["monitor"]["hs_port"],
        packet_size=None,
        buffer_size=BUFFER_SIZE_HS,
        ):
    if timeout is None:
        timeout = DYNAMIC_CONFIG["monitor"]["hs_timeout_s"]
    if packet_size is None:
        packet_size = brokkr.utils.decode.DataDecoder(
            VARIABLE_PARAMS_HS).packet_size

    LOGGER.debug("Reading H&S data...")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        try:
            sock.settimeout(timeout)
            sock.bind((host_address, port))
            LOGGER.debug("Listening on socket %r", sock)
        except Exception as e:
            LOGGER.error("%s connecting to H&S port %r: %s",
                         type(e).__name__, port, e)
            LOGGER.info("Error details:", exc_info=1)
            LOGGER.info("Socket details: %r", sock)
            return None
        try:
            packet = sock.recv(buffer_size)
            LOGGER.debug("Data recieved: %r", packet)
        except socket.timeout:
            LOGGER.debug("Socket timed out in %s s while waiting for data",
                         timeout)
            LOGGER.debug("Socket details: %r", sock)
            return None
        except Exception as e:
            LOGGER.error("%s recieving H&S data on port %r: %s",
                         type(e).__name__, port, e)
            LOGGER.info("Error details:", exc_info=1)
            LOGGER.info("Socket details: %r", sock)
            return None
    if packet:
        packet = packet[:packet_size]
        LOGGER.debug("Packet: %s", packet.hex())
    else:
        LOGGER.warning("Null H&S data responce returned: %r", packet)
        packet = None
    return packet


def decode_hs_packet(
        raw_data,
        variables=None,
        conversion_functions=None,
        ):
    if variables is None:
        variables = VARIABLE_PARAMS_HS

    data_decoder = brokkr.utils.decode.DataDecoder(
        variables=variables,
        conversion_functions=conversion_functions)
    LOGGER.debug("Created H&S data decoder: %r", data_decoder)
    hs_data = data_decoder.decode_data(raw_data)

    return hs_data


def get_hs_data(**kwargs):
    packet = read_hs_packet(**kwargs)
    hs_data = decode_hs_packet(packet)
    return hs_data
