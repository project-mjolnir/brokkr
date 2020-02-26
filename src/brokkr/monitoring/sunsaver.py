"""
Functions to read data from a Sunsaver MPPT-15L charge controller.
"""

# Standard library imports
import logging
import os
from pathlib import Path
import struct
import time

# Third party imports
import pymodbus.client.sync
import pymodbus.pdu
import serial.tools.list_ports

# Local imports
from brokkr.config.static import CONFIG
import brokkr.decode
import brokkr.logger


REGISTER_TYPE = "H"
USBDEVFS_RESET = 21780

SERIAL_PARAMS_MPPT15L = {
    "method": "rtu",
    "stopbits": 2,
    "bytesize": 8,
    "parity": "N",
    "baudrate": 9600,
    "strict": False,
    "timeout": 2,
    }

VARIABLE_PARAMS_MPPT15L = [
    {"name": "adc_vb_f", "output_type": "xV"},
    {"name": "adc_va_f", "output_type": "xV"},
    {"name": "adc_vl_f", "output_type": "xV"},
    {"name": "adc_ic_f", "output_type": "xA"},
    {"name": "adc_il_f", "output_type": "xA"},
    {"name": "t_hs", "raw_type": "h"},
    {"name": "t_batt", "raw_type": "h"},
    {"name": "t_amb", "raw_type": "h"},
    {"name": "t_rts", "raw_type": "h"},
    {"name": "charge_state"},
    {"name": "array_fault", "output_type": "B"},
    {"name": "vb_f", "output_type": "xV"},
    {"name": "vb_ref", "output_type": "xVr"},
    {"name": "ahc_r", "raw_type": "I", "output_type": "xAh"},
    {"name": "ahc_t", "raw_type": "I", "output_type": "xAh"},
    {"name": "kwhc", "output_type": "xAh"},
    {"name": "load_state", "output_type": "I"},
    {"name": "load_fault", "output_type": "B"},
    {"name": "v_lvd", "output_type": "xV"},
    {"name": "ahl_r", "raw_type": "I", "output_type": "xAh"},
    {"name": "ahl_t", "raw_type": "I", "output_type": "xAh"},
    {"name": "hourmeter", "raw_type": "I"},
    {"name": "alarm", "raw_type": "I", "output_type": "B"},
    {"name": "dip_switch", "output_type": "B"},
    {"name": "led_state"},
    {"name": "power_out", "output_type": "xW"},
    {"name": "sweep_vmp", "output_type": "xV"},
    {"name": "sweep_pmax", "output_type": "xW"},
    {"name": "sweep_voc", "output_type": "xV"},
    {"name": "vb_min_daily", "output_type": "xV"},
    {"name": "vb_max_daily", "output_type": "xV"},
    {"name": "ahc_daily", "output_type": "xAh"},
    {"name": "ahl_daily", "output_type": "xAh"},
    {"name": "array_fault_daily", "output_type": "B"},
    {"name": "load_fault_daily", "output_type": "B"},
    {"name": "alarm_daily", "raw_type": "I", "output_type": "B"},
    {"name": "vb_min", "output_type": "xV"},
    {"name": "vb_max", "output_type": "xV"},
    ]

CONVERSION_FUNCTIONS_MPTT15L = {
    "xV": lambda val: round(val * 100 * 2 ** -15, 3),
    "xVr": lambda val: round(val * 96.667 * 2 ** -15, 3),
    "xA": lambda val: round(val * 79.16 * 2 ** -15, 3),
    "xAh": lambda val: round(val * 0.1, 1),
    "xW": lambda val: round(val * 989.5 * 2 ** -16, 3),
    }

LOGGER = logging.getLogger(__name__)


def get_serial_port(port=None, pids=None):
    # Automatically detect serial port to use
    port_list = serial.tools.list_ports.comports()
    # Ignore built-in ARM serial port
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
                brokkr.logger.log_details(LOGGER, port=port_object)
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
        brokkr.logger.log_details(LOGGER, port=port_object)
    else:
        # If successful, wait to allow the reset to take effect
        LOGGER.debug("Reset successful; sleeping for 5 s...")
        for __ in range(5):
            time.sleep(1)
        reset_success = True

    return reset_success


def read_raw_sunsaver_data(
        start_offset=CONFIG["monitor"]["sunsaver_start_offset"],
        port=CONFIG["monitor"]["sunsaver_port"],
        pids=CONFIG["monitor"]["sunsaver_pid_list"],
        unit=CONFIG["monitor"]["sunsaver_unit"],
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
    port_object = get_serial_port(port=port, pids=pids)
    if not port_object:
        return None

    # Read charge controller data over serial Modbus
    serial_params = {**SERIAL_PARAMS_MPPT15L, **serial_params}
    mppt_client = pymodbus.client.sync.ModbusSerialClient(
        port=port_object.device, **serial_params)
    brokkr.logger.log_details(LOGGER.debug, error=False, client=mppt_client)
    try:
        try:
            connect_successful = mppt_client.connect()
        # If connecting to the device fails due to an OS-level problem
        # e.g. being disconnected previously, attempt to reset it
        except OSError as e:
            LOGGER.warning("%s connecting to charge controller device %s; "
                           "attempting USB reset...",
                           type(e).__name__, port_object)

            reset_success = reset_usb_port(port_object)
            if not reset_success:
                raise
            connect_successful = mppt_client.connect()
            LOGGER.warning("Successfully reset charge controller device %s; "
                           "original error %s: %s",
                           port_object, type(e).__name__, e)
            brokkr.logger.log_details(
                LOGGER, client=mppt_client, port=port_object)
        if connect_successful:
            try:
                data_decoder = brokkr.decode.DataDecoder(
                    VARIABLE_PARAMS_MPPT15L)
                register_count = (data_decoder.packet_size
                                  // struct.calcsize("!" + REGISTER_TYPE))
                register_data = mppt_client.read_holding_registers(
                    start_offset, register_count, unit=unit)
                # If register data is an exception, log it and return None
                if isinstance(register_data, BaseException):
                    raise register_data
                if isinstance(register_data, pymodbus.pdu.ExceptionResponse):
                    LOGGER.error("Error reading register data for %s",
                                 port_object)
                    brokkr.logger.log_details(
                        LOGGER, error=register_data,
                        client=mppt_client, port=port_object)
                    return None
            # Catch and log errors reading register data
            except Exception as e:
                LOGGER.error("%s reading register data for %s: %s",
                             type(e).__name__, port_object, e)
                brokkr.logger.log_details(
                    LOGGER, client=mppt_client, port=port_object)
                return None
            finally:
                LOGGER.debug("Closing MPPT client connection")
                try:
                    mppt_client.close()
                # Catch and log any errors closing the modbus connection
                except Exception as e:
                    LOGGER.info("%s closing modbus device at %s: %s",
                                type(e).__name__, port_object, e)
                    brokkr.logger.log_details(
                        LOGGER, client=mppt_client, port=port_object)
        else:
            # Raise an error if connect not successful
            LOGGER.error(
                "Error reading register data: Cannot connect to device %s",
                port_object)
            brokkr.logger.log_details(
                LOGGER, error=False, client=mppt_client, port=port_object)
            return None
        LOGGER.debug("Register data: %r",
                     getattr(register_data, "__dict__", None))
    except Exception as e:
        LOGGER.error("%s connecting to charge controller device %s: %s",
                     type(e).__name__, port_object, e)
        brokkr.logger.log_details(
            LOGGER, client=mppt_client, port=port_object)
        return None
    return register_data


def decode_sunsaver_data(
        raw_data,
        variables=None,
        conversion_functions=None
        ):
    if variables is None:
        variables = VARIABLE_PARAMS_MPPT15L
    if conversion_functions is None:
        conversion_functions = CONVERSION_FUNCTIONS_MPTT15L

    data_decoder = brokkr.decode.DataDecoder(
        variables=variables,
        conversion_functions=conversion_functions)
    LOGGER.debug("Created sunsaver data decoder: %r", data_decoder)

    # Handle raw data not being present
    if not raw_data:
        sunsaver_data = data_decoder.output_na_data()
        LOGGER.debug("No data to decode, returning: %r", sunsaver_data)
        return sunsaver_data

    # Handle both register object and a simple list of register values
    try:
        raw_data.registers[0]
    except AttributeError:
        LOGGER.debug("Register_data passed as list.")
    else:
        raw_data = raw_data.registers
        LOGGER.debug("Register_data passed as object.")

    # Convert uint16s back to packed bytes
    struct_format = "!" + (REGISTER_TYPE * len(raw_data))
    raw_data = struct.pack(struct_format, *raw_data)
    LOGGER.debug("Converted register data to struct of format %r : %r",
                 struct_format, raw_data)

    sunsaver_data = data_decoder.decode_data(raw_data)

    return sunsaver_data


def get_sunsaver_data(**kwargs):
    register_data = read_raw_sunsaver_data(**kwargs)
    sunsaver_data = decode_sunsaver_data(register_data)
    return sunsaver_data
