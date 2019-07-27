"""Routines to read data from a Sunsaver MPPT-15L charge controller."""

import datetime

import pymodbus.client.sync


REGISTER_VARIABLES = [
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
    ]

CONVERSION_FUNCTIONS = {
    None: lambda val: None,
    "HI": lambda val: None,
    "S": lambda val: str(val),
    "I": lambda val: int(val),
    "F": lambda val: float(val),
    "B": lambda val: format(val, "b").zfill(16),
    "BL": lambda hi, lo: format(hi << 16 | lo, "b").zfill(32),
    "V": lambda val: val * 100 * 2 ** -15,
    "A": lambda val: val * 79.16 * 2 ** -15,
    "Ah": lambda val: val * 0.1,
    "AhL": lambda hi, lo: ((hi << 16) | lo) * 0.1,
    "hL": lambda hi, lo: (hi << 16) | lo,
    "W": lambda val: val * 989.5 * 2 ** -16,
    }


def read_raw_sunsaver_data(start_offset=0x0008, port="/dev/ttyUSB0", unit=1):
    """
    Read all useful register data from an attached SunSaver MPPT-15-L device.

    Parameters
    ----------
    start_offset : hex, optional
       Register start offset (PDU address). The default is 0x0008.
    port : str, optional
        Serial port device to use. The default is "/dev/ttyUSB0".
    unit : int, optional
        Unit number to request data from. The default is 1.

    Returns
    -------
    register_data : pymodbbus.register_read_message.ReadHoldingRegisterResponce
        Pymodbus data object reprisenting the read register data.

    """
    try:
        mppt_client = pymodbus.client.sync.ModbusSerialClient(
            method="rtu", port=port, stopbits=2, bytesize=8, parity="N",
            baudrate=9600, strict=True)
        mppt_client.connect()
        register_data = mppt_client.read_holding_registers(0x0008, 45, unit=1)
    except Exception as e:  # Logerrors rather than giving up entirely
        print(f"{datetime.datetime.utcnow()!s} "
              f"Error reading sunsaver data: {type(e)} {e}")
        register_data = None
    return register_data


def decode_sunsaver_data(register_data):
    try:
        register_data.registers[0]
    except AttributeError:  # If not a data structure, just a list
        pass
    else:
        register_data = register_data.registers

    sunsaver_data = {}
    last_hi = None
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
                var_name = var_name.replace("_lo", "")
                sunsaver_data[var_name] = output_val
        except Exception as e:
            print(f"{datetime.datetime.utcnow()!s} "
                  f"Error decoding sunsaver data: {type(e)} {e}")
            sunsaver_data[var_name] = "NA"
            last_hi = None

    return sunsaver_data


def get_sunsaver_data(**kwargs):
    register_data = read_raw_sunsaver_data(**kwargs)
    sunsaver_data = decode_sunsaver_data(register_data)
    return sunsaver_data
