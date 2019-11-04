"""
Functions to read data from a Sunsaver MPPT-15L charge controller.
"""

# Standard library imports
import logging

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
    ("t_hs", "F"),
    ("t_batt", "F"),
    ("t_amb", "F"),
    ("t_rts", "F"),
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
    if not port:
        port_list = serial.tools.list_ports.comports()
        if not port_list:
            logger.error(
                "Error reading Sunsaver data: No serial devices found.")
            return None
        # Match device by PID if provided
        if pids:
            for port_object in port_list:
                logger.debug("Checking serial port %s against pids %s...",
                             port_object, pids)
                try:
                    if port_object.pid in pids:
                        port = port_object.device
                        logger.debug("Matched serial port %s with pid %s",
                                     port_object.device, port_object.pid)
                        break
                except Exception as e:  # Ignore any problems reading a device
                    logger.info("%s checking serial port %s: %s",
                                type(e).__name__, port_object, e)
                    logger.debug("Details:", exc_info=1)
        # If we can't identify a device by pid, just try the first port
        if not port:
            port = port_list[0].device
            logger.debug("Cannot match device by PID; falling back to %s.",
                         port_list[0])

    # Read charge controller data over serial Modbus
    serial_params = {**SERIAL_PARAMS_SUNSAVERMPPT15L, **serial_params}
    mppt_client = pymodbus.client.sync.ModbusSerialClient(
        port=port, **serial_params)
    logger.debug("Connecting to client %s", mppt_client)
    if mppt_client.connect():
        try:
            register_data = mppt_client.read_holding_registers(
                start_offset, len(REGISTER_VARIABLES), unit=unit)
            if isinstance(register_data, BaseException):
                raise register_data
        # Catch and log errors reading register data
        except Exception as e:
            logger.error("%s reading register data for %s: %s",
                         type(e).__name__, port, e)
            logger.info("Details: %s", mppt_client, exc_info=1)
            return None
        finally:
            logger.debug("Closing MPPT client connection")
            mppt_client.close()
    else:
        logger.error(
            "Error reading register data: Cannot connect to device %s", port)
        logger.info("Device info: %s", mppt_client)
        return None
    logger.debug("Register data: %s", register_data)
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
