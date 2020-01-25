"""
Functions to read data from a Sunsaver MPPT-15L charge controller.
"""

# Standard library imports
import logging
import os
from pathlib import Path
import time

# Third party imports
import pymodbus.client.sync
import serial.tools.list_ports

# Local imports
from brokkr.config.main import CONFIG


SERIAL_PARAMS_SUNSAVERMPPT15L = {
    "method": "rtu",
    "stopbits": 2,
    "bytesize": 8,
    "parity": "N",
    "baudrate": 9600,
    "strict": False,
    }

REGISTER_VARIABLES = (
    ("adc_vb_f", "V"),
    ("adc_va_f", "V"),
    ("adc_vl_f", "V"),
    ("adc_ic_f", "A"),
    ("adc_il_f", "A"),
    ("t_hs", "T"),
    ("t_batt", "T"),
    ("t_amb", "T"),
    ("t_rts", "T"),
    ("charge_state", "S"),
    ("array_fault", "B"),
    ("vb_f", "V"),
    ("vb_ref", "V"),
    ("ahc_r_hi", "HI"),
    ("ahc_r_lo", "AhL"),
    ("ahc_t_hi", "HI"),
    ("ahc_t_lo", "AhL"),
    ("kwhc", "Ah"),
    ("load_state", "S"),
    ("load_fault", "B"),
    ("v_lvd", "V"),
    ("ahl_r_hi", "HI"),
    ("ahl_r_lo", "AhL"),
    ("ahl_t_hi", "HI"),
    ("ahl_t_lo", "AhL"),
    ("hourmeter_hi", "HI"),
    ("hourmeter_lo", "hL"),
    ("alarm_hi", "HI"),
    ("alarm_lo", "BL"),
    ("dip_switch", "B"),
    ("led_state", "S"),
    ("power_out", "W"),
    ("sweep_vmp", "V"),
    ("sweep_pmax", "W"),
    ("sweep_voc", "V"),
    ("vb_min_daily", "V"),
    ("vb_max_daily", "V"),
    ("ahc_daily", "Ah"),
    ("ahl_daily", "Ah"),
    ("array_fault_daily", "B"),
    ("load_fault_daily", "B"),
    ("alarm_hi_daily", "HI"),
    ("alarm_Lo_daily", "BL"),
    ("vb_min", "V"),
    ("vb_max", "V"),
    )

CONVERSION_FUNCTIONS = {
    None: lambda val: None,
    "HI": lambda val: None,
    "S": lambda val: str(val),
    "I": lambda val: int(val),
    "F": lambda val: float(val),
    "T": lambda val: float(val) - 2**16 if val > 2**8 else float(val),
    "B": lambda val: format(val, "b").zfill(16),
    "BL": lambda hi, lo: format(hi << 16 | lo, "b").zfill(32),
    "V": lambda val: round(val * 100 * 2 ** -15, 3),
    "A": lambda val: round(val * 79.16 * 2 ** -15, 3),
    "Ah": lambda val: round(val * 0.1, 1),
    "AhL": lambda hi, lo: round(((hi << 16) | lo) * 0.1, 1),
    "hL": lambda hi, lo: int((hi << 16) | lo),
    "W": lambda val: round(val * 989.5 * 2 ** -16, 3),
    }

logger = logging.getLogger(__name__)


def read_raw_sunsaver_data(
        start_offset=CONFIG["monitor"]["sunsaver"]["start_offset"],
        port=CONFIG["monitor"]["sunsaver"]["port"],
        pids=CONFIG["monitor"]["sunsaver"]["pid_list"],
        unit=CONFIG["monitor"]["sunsaver"]["unit"],
        **serial_params,
        ):
    """
    Read all useful register data from an attached SunSaver MPPT-15-L device.

    Parameters
    ----------
    start_offset : int or hex, optional
       Register start offset (PDU address). The default is 0x0008.
    port : str or None, optional
        Serial port device to use. The default is None, which uses the first
        serial device matching the correct PID(s), or else the first detected.
    pids : iterable of int, optional
        If serial port device not specified, collection of PIDs (per USB spec)
        to look for to find the expected USB to serial adapter.
        By default, uses the values in the config file `pid_list` variable.
    unit : int or hex, optional
        Unit ID to request data from. The default is ``0x01``.
    serial_params
        Custom serial parameters to pass to the ModbusSerialClient.
        By default, uses the recommended values to work with the SS MPPT-15L.

    Returns
    -------
    register_data : pymodbbus.register_read_message.ReadHoldingRegisterResponce
        Pymodbus data object reprisenting the read register data, or None if
        no data could be read and an exception was logged.

    """
    # Automatically detect serial port to use
    port_list = serial.tools.list_ports.comports()
    # Ignore built-in ARM serial port
    port_list = [port_object for port_object in port_list
                 if not port_object.device.startswith("/dev/ttyAMA")]
    if not port_list:
        logger.error(
            "Error reading Sunsaver data: No serial devices found.")
        return None
    # Match device by PID or port if provided
    if port or pids:
        for port_object in port_list:
            logger.debug("Checking serial port %s against port %s, pid %s: %s",
                         port_object.device, port, pids, port_object.__dict__)
            try:
                if (port_object.device == port
                        or (pids and port_object.pid in pids)):
                    if port:
                        logger.debug("Matched serial port %s",
                                     port_object.device)
                    if pids:
                        port = port_object.device
                        logger.debug("Matched serial port %s with pid %s",
                                     port_object.device, port_object.pid)
                    break
                elif port_object.pid in pids:
                    port = port_object.device
                    break
            except Exception as e:  # Ignore any problems reading a device
                logger.debug("%s checking serial port %s: %s",
                             type(e).__name__, port_object.__dict__, e)
                logger.debug("Details:", exc_info=1)

    # If we can't identify a device by pid, just try the first port
    if not port:
        port_object = port_list[0]
        port = port_object.device
        logger.debug("Can't match device by PID or port; falling back to %s",
                     port)
        logger.debug("Selected serial device %s: %s",
                     port, port_object.__dict__)

    # Read charge controller data over serial Modbus
    serial_params = {**SERIAL_PARAMS_SUNSAVERMPPT15L, **serial_params}
    mppt_client = pymodbus.client.sync.ModbusSerialClient(
        port=port, **serial_params)
    logger.debug("Connecting to client %s", mppt_client)
    try:
        try:
            connect_successful = mppt_client.connect()
        # If connecting to the device fails due to an OS-level problem
        # e.g. being disconnected previously, attempt to reset it
        except OSError as e:
            logger.warning("%s connecting to charge controller device %s; "
                           "attempting USB reset...", type(e).__name__, port)
            try:
                import fcntl
                USBDEVFS_RESET = 21780
                usb_num_parts = {}
                for usb_num_part in ["busnum", "devnum"]:
                    with open(Path(port_object.usb_device_path) / usb_num_part,
                              "r", encoding="utf-8") as num_file:
                        num_raw = num_file.readline()
                    usb_num_parts[usb_num_part] = num_raw.strip().zfill(3)
                usb_device_path = "/dev/bus/usb/{busnum}/{devnum}".format(
                    **usb_num_parts)
                logger.debug("Resetting USB device at %s", usb_device_path)
                with open(usb_device_path, "w", os.O_WRONLY) as device_file:
                    fcntl.ioctl(device_file, USBDEVFS_RESET, 0)
            # Ignore error loading fcntl if on Windows as it isn't present
            except ModuleNotFoundError:
                logger.debug("Ignored error laoding fcntl, likely not present")
            # Catch and log other exceptions trying to reset serial port
            except Exception:
                logger.warning("%s resetting charge controller device %s: %s",
                               type(e).__name__, port, e)
                logger.info("Device info: %s",
                            port_object.__dict__, exc_info=1)
            else:
                # If successful, wait to allow the reset to take effect
                logger.debug("Reset successful; sleeping for 5 s...")
                for __ in range(5):
                    time.sleep(1)

            connect_successful = mppt_client.connect()
            logger.warning("Successfully reset charge controller device %s; "
                           "original error %s: %s",
                           port, type(e).__name__, e)
            logger.info("Device info: %s", port_object.__dict__, exc_info=1)
        if connect_successful:
            try:
                register_data = mppt_client.read_holding_registers(
                    start_offset, len(REGISTER_VARIABLES), unit=unit)
                if isinstance(register_data, BaseException):
                    raise register_data
            # Catch and log errors reading register data
            except Exception as e:
                logger.error("%s reading register data for %s: %s",
                             type(e).__name__, port, e)
                logger.info("Device info: %s; Port info: %s",
                            mppt_client, port_object.__dict__, exc_info=1)
                return None
            finally:
                logger.debug("Closing MPPT client connection")
                mppt_client.close()
        else:
            # Raise an error if connect not successful
            logger.error(
                "Error reading register data: Cannot connect to device %s",
                port)
            logger.info("Device info: %s; Port info: %s",
                        mppt_client, port_object.__dict__)
            return None
        logger.debug("Register data: %s", register_data)
    except Exception as e:
        logger.error("%s connecting to charge controller device %s: %s",
                     type(e).__name__, port, e)
        logger.info("Device info: %s; Port info: %s",
                    mppt_client, port_object.__dict__, exc_info=1)
        return None
    return register_data


def decode_sunsaver_data(
        register_data,
        na_marker=CONFIG["monitor"]["na_marker"],
        register_variables=REGISTER_VARIABLES,
        conversion_functions=CONVERSION_FUNCTIONS,
        ):
    # Handle both register object and a simple list of register values
    try:
        register_data.registers[0]
    except AttributeError:
        logger.debug("Register_data passed as list.")
    else:
        register_data = register_data.registers
        logger.debug("Register_data passed as object.")

    sunsaver_data = {}
    last_hi = None
    try:
        for register_val, (var_name, var_type) in zip(
                register_data, register_variables):
            try:
                if last_hi is None:
                    output_val = (
                        conversion_functions[var_type](register_val))
                else:
                    output_val = (
                        conversion_functions[var_type](last_hi, register_val))

                if var_type == "HI":
                    last_hi = register_val
                else:
                    last_hi = None

                if output_val is not None:
                    var_name = (var_name.lower()
                                .replace("_lo", "").replace("_lo_", "_"))
                    sunsaver_data[var_name] = output_val
            # Catch any conversion errors and return NA
            except Exception as e:
                logger.warning("%s decoding %s register data %s to %s: %s",
                               type(e).__name__, var_name,
                               register_val, var_type, e)
                logger.debug("Details:", exc_info=1)
                sunsaver_data[var_name] = na_marker
                last_hi = None
    # Catch overall errrors, e.g. modbus exceptions
    except Exception as e:
        if register_data is not None:
            logger.error("%s decoding register data %s: %s",
                         type(e).__name__, register_data, e)
            logger.info("Details:", exc_info=1)
        sunsaver_data = {
            var_name.lower().replace("_lo", "").replace("_lo_", "_"): na_marker
            for var_name, var_type in register_variables
            if var_type and var_type != "HI"}

    return sunsaver_data


def get_sunsaver_data(na_marker=CONFIG["monitor"]["na_marker"], **kwargs):
    register_data = read_raw_sunsaver_data(**kwargs)
    sunsaver_data = decode_sunsaver_data(register_data, na_marker=na_marker)
    return sunsaver_data
