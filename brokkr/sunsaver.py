"""Routines to read data from a Sunsaver MPPT-15L charge controller."""

import datetime

import pymodbus.client.sync
import serial.tools.list_ports


USB_SERIAL_ADAPTER_PIDS = (24597,)


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


def read_raw_sunsaver_data(start_offset=0x0008, port=None,
                           pids=USB_SERIAL_ADAPTER_PIDS, unit=0x01):
    """
    Read all useful register data from an attached SunSaver MPPT-15-L device.

    Parameters
    ----------
    start_offset : hex, optional
       Register start offset (PDU address). The default is 0x0008.
    port : str or None, optional
        Serial port device to use. The default is None, which uses the first
        serial device matching the correct PID(s), or else the first detected.
    pids : iterable of int, optional
        If serial port device not specified, collection of PIDs (per USB spec)
        to look for to find the expected USB to serial adapter.
        By default, uses the values in `USB_SERIAL_ADAPTER_PIDS`.
    unit : int, optional
        Unit ID to request data from. The default is ``0x01``.

    Returns
    -------
    register_data : pymodbbus.register_read_message.ReadHoldingRegisterResponce
        Pymodbus data object reprisenting the read register data, or None if
        no data could be read and an exception was logged.

    """
    # Automatically detect serial port to use
    if port is None:
        port_list = serial.tools.list_ports.comports()
        if not port_list:
            print(f"{datetime.datetime.utcnow()!s} "
                  "Error reading sunsaver data: No serial devices found.")
            return None
        # Match device by PID if provided
        if pids:
            for port_object in port_list:
                try:
                    if port_object.pid in USB_SERIAL_ADAPTER_PIDS:
                        port = port_object.device
                        break
                except Exception:  # Ignore any problems reading a device
                    continue
        # If we can't identify a device by pid, just try the first port
        if not port:
            port = port_list[0].device

    # Read charge controller data over serial Modbus
    mppt_client = pymodbus.client.sync.ModbusSerialClient(
        method="rtu", port=port, stopbits=2, bytesize=8, parity="N",
        baudrate=9600, strict=False)
    if mppt_client.connect():
        try:
            register_data = mppt_client.read_holding_registers(
                start_offset, 45, unit=unit)
            if isinstance(register_data, BaseException):
                raise register_data
        # Catch and log errors reading register data
        except Exception as e:
            print(f"{datetime.datetime.utcnow()!s} "
                  f"Error reading sunsaver registers: {type(e)} {e}")
            return None
        finally:
            mppt_client.close()
    else:
        print(f"{datetime.datetime.utcnow()!s} "
              f"Error reading sunsaver data: Cannot connect to device {port}")
        return None
    return register_data


def decode_sunsaver_data(register_data):
    # Handle both register object and a simple list of register values
    try:
        register_data.registers[0]
    except AttributeError:
        pass
    else:
        register_data = register_data.registers

    sunsaver_data = {}
    last_hi = None
    try:
        for register_val, (var_name, var_type) in zip(
                register_data, REGISTER_VARIABLES):
            try:
                if last_hi is None:
                    output_val = (
                        CONVERSION_FUNCTIONS[var_type](register_val))
                else:
                    output_val = (
                        CONVERSION_FUNCTIONS[var_type](last_hi, register_val))

                if var_type == "HI":
                    last_hi = register_val
                else:
                    last_hi = None

                if output_val is not None:
                    var_name = var_name.replace("_lo", "").replace("_lo_", "_")
                    sunsaver_data[var_name] = output_val
            # Catch any conversion errors and return NA
            except Exception as e:
                print(f"{datetime.datetime.utcnow()!s} "
                      f"Error decoding sunsaver data: {type(e)} {e} | "
                      f"Data: {var_name} {register_val}")
                sunsaver_data[var_name] = "NA"
                last_hi = None
    # Catch overall errrors, e.g. modbus exceptions
    except Exception as e:
        if register_data is not None:
            print(f"{datetime.datetime.utcnow()!s} "
                  f"Error handling sunsaver data: {type(e)} {e} | "
                  f"Data: {register_data}")
        sunsaver_data = {var_name[0]: "NA" for var_name in REGISTER_VARIABLES}

    return sunsaver_data


def get_sunsaver_data(**kwargs):
    register_data = read_raw_sunsaver_data(**kwargs)
    sunsaver_data = decode_sunsaver_data(register_data)
    return sunsaver_data
