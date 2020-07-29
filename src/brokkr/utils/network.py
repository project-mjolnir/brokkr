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
from brokkr.constants import Errors
import brokkr.utils.log
import brokkr.utils.misc


BUFFER_SIZE_DEFAULT = 4096
MAX_DATA_SIZE = 2**31 - 2

MAX_DATA_PRINT_LENGTH = 4096

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


def handle_socket_error(e, errors=Errors.RAISE, **log_kwargs):
    if errors == Errors.RAISE:
        raise e
    if errors in {Errors.WARN, Errors.LOG}:
        LOGGER.error("%s with socket: %s", type(e).__name__, e)
        LOG_HELPER.log(socket=log_kwargs)
    elif errors == Errors.IGNORE:
        LOGGER.debug("Suppressing %s with socket: %s", type(e).__name__, e)
        LOG_HELPER.log(log_helper_log_level="debug", socket=log_kwargs)
    else:
        error_levels = {"Errors." + errors.name for errors in Errors}
        LOGGER.critical(
            "Error level for %s.handle_socket_error must be one of %r, not %r;"
            " assuming raise", __file__, error_levels, errors)
        LOGGER.info("Stack trace:", stack_info=True)
        raise e


def setup_socket(  # pylint: disable=dangerous-default-value
        sock,
        address_tuple,
        action,
        timeout_s=None,
        errors=Errors.RAISE,
        error_codes_suppress=ERROR_CODES_ADDRESS_LINK_DOWN,
        ):
    valid_actions = {"bind", "connect"}
    if action is not None and action not in valid_actions:
        LOGGER.critical("Action for %s.setup_socket must be one of %r, not %r",
                        __file__, valid_actions, action)
        LOGGER.info("Stack trace:", stack_info=True)
        raise ValueError(
            f"Action must be one of {valid_actions!r}, not {action!r}")

    try:
        sock.settimeout(timeout_s)
        if action is not None:
            getattr(sock, action)(address_tuple)
    except Exception as e:
        if isinstance(e, OSError):
            # pylint: disable=no-member
            if error_codes_suppress and (
                    isinstance(e, socket.timeout)
                    or (e.errno
                        and e.errno in error_codes_suppress)):
                errors = Errors.IGNORE
        handle_socket_error(e, errors=errors, socket=sock,
                            address=address_tuple, action=action)
        return None
    else:
        LOGGER.debug("Listening on socket %r", sock)

    return sock


def recieve_all(
        sock,
        data_length=None,
        timeout_s=None,
        errors=Errors.RAISE,
        buffer_size=BUFFER_SIZE_DEFAULT,
        ):
    start_time_recieve = None
    chunks = []
    bytes_remaining = (
        data_length if data_length else (MAX_DATA_SIZE - buffer_size))
    while (bytes_remaining > 0
           and (not start_time_recieve
                or not timeout_s
                or (brokkr.utils.misc.monotonic_ns()
                    - start_time_recieve * brokkr.utils.misc.NS_IN_S)
                <= (timeout_s * brokkr.utils.misc.NS_IN_S))):
        try:
            chunk = sock.recv(buffer_size)
            if len(chunks) == 0:
                LOGGER.debug("First chunk of network data recieved: %r", chunk)
        except socket.timeout as e:
            LOGGER.debug("Socket timed out in %s s while waiting for data",
                         timeout_s)
            handle_socket_error(
                e, errors=Errors.IGNORE, socket=sock, data_length=data_length,
                n_chunks=len(chunks), bytes_remaining=bytes_remaining)
            break
        except Exception as e:
            handle_socket_error(
                e, errors=errors, socket=sock, data_length=data_length,
                n_chunks=len(chunks), bytes_remaining=bytes_remaining)
            return None
        if start_time_recieve is None:
            start_time_recieve = brokkr.utils.misc.monotonic_ns()
        if not chunk:
            if not data_length:
                errors = Errors.IGNORE
            try:
                raise RuntimeError(
                    f"Null {chunk!r} found in recieved socket data chunk")
            except RuntimeError as e:
                handle_socket_error(
                    e, errors=errors, socket=sock, data_length=data_length,
                    n_chunks=len(chunks), bytes_remaining=bytes_remaining)
            break
        bytes_remaining -= len(chunk)
        buffer_size = min([buffer_size, bytes_remaining])
        chunks.append(chunk)

    LOGGER.debug("%s total chunks of network data recieved", len(chunks))
    if not chunks:
        LOGGER.debug("No network data to return")
        return None

    data = b"".join(chunks)
    if data_length:
        data = data[:data_length]

    if not data:
        LOGGER.debug("Null network data recieved: %r", data)
    else:
        LOGGER.debug("Network data recieved of length %s bytes", len(data))
        LOGGER.debug("First %s bytes: %r",
                     MAX_DATA_PRINT_LENGTH, data[:MAX_DATA_PRINT_LENGTH])

    return data


def read_socket_data(
        host,
        port,
        action,
        socket_family=socket.AF_INET,
        socket_type=socket.SOCK_STREAM,
        timeout_s=TIMEOUT_S_DEFAULT,
        errors=Errors.RAISE,
        **recieve_kwargs,
        ):
    address_tuple = (host, port)
    LOGGER.debug(
        "Creating socket of family %r, type %r with host %r, port %r, "
        "action %r, timeout %r",
        socket_family, socket_type, host, port, action, timeout_s)

    with socket.socket(socket_family, socket_type) as sock:
        LOGGER.debug("Created socket %r", sock)
        setup_sock = setup_socket(
            sock, address_tuple, action, timeout_s=timeout_s, errors=errors)

        if setup_sock is not None:
            sock = setup_sock
            LOGGER.debug(
                "Recieving data from socket %r with kwargs %r",
                sock, recieve_kwargs)
            data = recieve_all(
                sock, timeout_s=timeout_s, errors=errors, **recieve_kwargs)
        else:
            data = None

    return data


def netcat(data_to_send, host, port, recieve_reply=True, timeout_s=1):
    recieved_data = None
    address_tuple = (host, port)
    LOGGER.info(
        "Running netcat with data %r, host %r, port %r, timeout %r",
        data_to_send[:MAX_DATA_PRINT_LENGTH], host, port, timeout_s)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        LOGGER.debug("Created socket %r", sock)
        sock = setup_socket(
            sock, address_tuple, action="connect", timeout_s=timeout_s,
            errors=Errors.RAISE, error_codes_suppress=None)
        LOGGER.debug("Sending data %r to socket %r",
                     data_to_send[:MAX_DATA_PRINT_LENGTH], sock)
        if data_to_send is not None:
            sock.sendall(data_to_send)
        sock.shutdown(socket.SHUT_WR)

        if recieve_reply:
            LOGGER.debug("Recieving data from socket %r", sock)
            recieved_data = recieve_all(
                sock, timeout_s=timeout_s, errors=Errors.RAISE)

        sock.shutdown(socket.SHUT_RD)

    return recieved_data


@brokkr.utils.log.basic_logging
def netcat_main(data_to_send=None, recieve_reply=True, **netcat_args):
    if data_to_send is not None:
        LOGGER.debug("Encoding input data %r to bytes",
                     data_to_send[:MAX_DATA_PRINT_LENGTH])
        data_to_send = data_to_send.encode()
        LOGGER.debug("Encoded data: %r",
                     data_to_send[:MAX_DATA_PRINT_LENGTH].hex())
    recieved_data = netcat(
        data_to_send, recieve_reply=recieve_reply, **netcat_args)
    if recieve_reply:
        try:
            LOGGER.debug("First %s bytes of recieved data: %r",
                         MAX_DATA_PRINT_LENGTH,
                         recieved_data[:MAX_DATA_PRINT_LENGTH].hex())
            recieved_data = recieved_data.decode()
        except Exception:
            pass
        LOGGER.info("Recieved responce:\n")
        print(recieved_data)
    return recieved_data
