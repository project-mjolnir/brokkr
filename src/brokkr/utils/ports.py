"""
Utilities for low-level I/O for various interfaces.
"""

# Standard library imports
import logging
import os
from pathlib import Path
import time

# Local import
import brokkr.utils.log


USBDEVFS_RESET = 21780

LOGGER = logging.getLogger(__name__)
LOG_HELPER = brokkr.utils.log.LogHelper(LOGGER)


def get_serial_port(port_list, port=None, pids=None):
    # Automatically detect serial port to use
    if port_list is None:
        port_list = []
    if not port_list:
        LOGGER.error(
            "Error reading Sunsaver data: No serial devices found.")
        return None
    # Match device by PID or port if provided
    if port or pids:
        for port_object in port_list:
            LOGGER.debug("Checking serial device %s against port %r, pid %r",
                         port_object, port, pids)
            LOGGER.debug("Device details: %r", port_object.__dict__)
            try:
                if (port_object.device == port
                        or (pids and port_object.pid in pids)):
                    LOGGER.debug("Matched serial device %s with pid %r",
                                 port_object, port_object.pid)
                    break
            except Exception as e:  # Ignore any problems reading a device
                LOGGER.debug("%s checking serial device %s: %s",
                             type(e).__name__, port_object, e)
                LOG_HELPER.log(port=port_object)
    # If we can't identify a device by pid, just try the first port
    else:
        port_object = port_list[0]
        LOGGER.debug("Can't match device by PID or port; falling back to %s",
                     port_object)
        LOGGER.debug("Device details: %r", port_object.__dict__)

    return port_object


def reset_usb_port(port_object):
    reset_success = False
    try:
        import fcntl  # pylint: disable=import-outside-toplevel
        usb_num_parts = {}
        for usb_num_part in ["busnum", "devnum"]:
            with open(Path(port_object.usb_device_path) / usb_num_part,
                      "r", encoding="utf-8") as num_file:
                num_raw = num_file.readline()
            usb_num_parts[usb_num_part] = num_raw.strip().zfill(3)
        usb_device_path = "/dev/bus/usb/{busnum}/{devnum}".format(
            **usb_num_parts)
        LOGGER.debug("Resetting USB device at %r", usb_device_path)
        with open(usb_device_path, "w", os.O_WRONLY) as device_file:
            fcntl.ioctl(device_file, USBDEVFS_RESET, 0)
    # Ignore error loading fcntl if on Windows as it isn't present
    except ModuleNotFoundError:
        LOGGER.debug("Ignored error loading fcntl, likely not present")
    # Catch and log other exceptions trying to reset serial port
    except Exception as e:
        LOGGER.warning("%s resetting charge controller device %s: %s",
                       type(e).__name__, port_object, e)
        LOG_HELPER.log(port=port_object)
    else:
        # If successful, wait to allow the reset to take effect
        LOGGER.debug("Reset successful; sleeping for 5 s...")
        for __ in range(5):
            time.sleep(1)
        reset_success = True

    return reset_success
