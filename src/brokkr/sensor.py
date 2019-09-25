"""
Functions to get status information from a HAMMA2 sensor over Ethernet.
"""

# Standard library imports
import datetime
import logging
import platform
import socket
import struct
import subprocess

# Local imports
from brokkr.config.main import CONFIG


HS_PACKET_SIZE = 60
HS_BUFFER_SIZE = 128

HS_STRUCT = "!8siqiiqqqii"
HS_VARIABLES = (
    ("marker_val", None),
    ("sequence_count", "I"),
    ("timestamp", "T"),
    ("crc_errors", "I"),
    ("valid_packets", "I"),
    ("bytes_read", "B"),
    ("bytes_written", "B"),
    ("bytes_remaining", "B"),
    ("packets_sent", "I"),
    ("packets_dropped", "I"),
    )
HS_CONVERSION_FUNCTIONS = {
    None: lambda val: None,
    "I": lambda val: int(val),
    "B": lambda val: int(val),
    "S": lambda val: val.decode().rstrip("\x00"),
    "T": lambda val: datetime.datetime.utcfromtimestamp(val / 1000),
    }

logger = logging.getLogger(__name__)


def ping(host=CONFIG["general"]["ip_sensor"],
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


def read_hs_packet(
        timeout=CONFIG["monitor"]["sensor"]["hs_timeout_s"],
        host_address="",
        port=CONFIG["monitor"]["sensor"]["hs_port"],
        packet_size=HS_PACKET_SIZE,
        buffer_size=HS_BUFFER_SIZE,
        ):
    logger.debug("Reading H&S data...")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        try:
            sock.settimeout(timeout)
            sock.bind((host_address, port))
            logger.debug("Listening on socket %s", sock)
        except Exception as e:
            logger.error("%s connecting to H&S port %s: %s",
                         type(e).__name__, port, e)
            logger.info("Details: %s", sock, exc_info=1)
            return None
        try:
            packet = sock.recv(buffer_size)
            logger.debug("Data recieved: %s", packet)
        except socket.timeout:
            logger.debug("Socket timed out in %s s while waiting for data",
                         timeout)
            return None
        except Exception as e:
            logger.error("%s recieving H&S data on port %s: %s",
                         type(e).__name__, port, e)
            logger.info("Details: %s", sock, exc_info=1)
            return None
    if packet:
        packet = packet[:packet_size]
        logger.debug("Packet: %s", packet.hex())
    else:
        logger.info("Null H&S data responce returned: %s", packet)
        packet = None
    return packet


def decode_hs_packet(
        packet,
        na_marker=CONFIG["monitor"]["na_marker"],
        struct_str=HS_STRUCT,
        hs_variables=HS_VARIABLES,
        conversion_functions=HS_CONVERSION_FUNCTIONS,
        ):
    hs_dict = {}
    try:
        decoded_vals = struct.unpack(struct_str, packet)
        for var_name, var_type, val in zip(*zip(*hs_variables), decoded_vals):
            try:
                output_val = conversion_functions[var_type](val)
                if output_val is not None:
                    hs_dict[var_name] = output_val
            # Handle errors decoding specific values
            except Exception as e:
                logger.warning("%s decoding %s H&S data %s to %s: %s",
                               type(e).__name__, val, var_name, var_type, e)
                logger.debug("Details:", exc_info=1)
                hs_dict[var_name] = na_marker
    # Handle overall decoding errors
    except Exception as e:
        if packet is not None:
            logger.error("%s decoding H&S data %s: %s",
                         type(e).__name__, packet, e)
            logger.info("Details:", exc_info=1)
        hs_dict = {var_name: na_marker
                   for var_name, var_type in hs_variables if var_type}
    return hs_dict


def get_hs_data(na_marker=CONFIG["monitor"]["na_marker"], **kwargs):
    packet = read_hs_packet(**kwargs)
    hs_data = decode_hs_packet(packet, na_marker=na_marker)
    return hs_data
