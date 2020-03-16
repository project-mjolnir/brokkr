"""
Contains the (temporary) system setup for the Mjolnir system.
"""

# Local imports
from brokkr.config.main import CONFIG


HS_VARIABLES = [
    {"name": "marker_val", "raw_type": "8s", "output_type": "none"},
    {"name": "sequence_count", "raw_type": "I"},
    {"name": "timestamp", "raw_type": "q", "output_type": "time_posix_ms"},
    {"name": "crc_errors", "raw_type": "I"},
    {"name": "valid_packets", "raw_type": "I"},
    {"name": "bytes_read", "raw_type": "Q"},
    {"name": "bytes_written", "raw_type": "Q"},
    {"name": "bytes_remaining", "raw_type": "Q"},
    {"name": "packets_sent", "raw_type": "I"},
    {"name": "packets_dropped", "raw_type": "I"},
    ]

MPPT15L_VARIABLES = [
    {"name": "adc_vb_f", "output_type": "_V"},
    {"name": "adc_va_f", "output_type": "_V"},
    {"name": "adc_vl_f", "output_type": "_V"},
    {"name": "adc_ic_f", "output_type": "_A"},
    {"name": "adc_il_f", "output_type": "_A"},
    {"name": "t_hs", "raw_type": "h"},
    {"name": "t_batt", "raw_type": "h"},
    {"name": "t_amb", "raw_type": "h"},
    {"name": "t_rts", "raw_type": "h"},
    {"name": "charge_state"},
    {"name": "array_fault", "output_type": "bitfield"},
    {"name": "vb_f", "output_type": "_V"},
    {"name": "vb_ref", "output_type": "_V_ref"},
    {"name": "ahc_r", "raw_type": "I", "output_type": "_A_h"},
    {"name": "ahc_t", "raw_type": "I", "output_type": "_A_h"},
    {"name": "kwhc", "output_type": "_A_h"},
    {"name": "load_state"},
    {"name": "load_fault", "output_type": "bitfield"},
    {"name": "v_lvd", "output_type": "_V"},
    {"name": "ahl_r", "raw_type": "I", "output_type": "_A_h"},
    {"name": "ahl_t", "raw_type": "I", "output_type": "_A_h"},
    {"name": "hourmeter", "raw_type": "I"},
    {"name": "alarm", "raw_type": "I", "output_type": "bitfield"},
    {"name": "dip_switch", "output_type": "bitfield"},
    {"name": "led_state"},
    {"name": "power_out", "output_type": "_W"},
    {"name": "sweep_vmp", "output_type": "_V"},
    {"name": "sweep_pmax", "output_type": "_W"},
    {"name": "sweep_voc", "output_type": "_V"},
    {"name": "vb_min_daily", "output_type": "_V"},
    {"name": "vb_max_daily", "output_type": "_V"},
    {"name": "ahc_daily", "output_type": "_A_h"},
    {"name": "ahl_daily", "output_type": "_A_h"},
    {"name": "array_fault_daily", "output_type": "bitfield"},
    {"name": "load_fault_daily", "output_type": "bitfield"},
    {"name": "alarm_daily", "raw_type": "I", "output_type": "bitfield"},
    {"name": "vb_min", "output_type": "_V"},
    {"name": "vb_max", "output_type": "_V"},
    ]

MPPT15L_CUSTOM_TYPES = {
    "_V": {"output_type": "custom", "scale": 100, "power": -15, "digits": 3},
    "_V_ref": {
        "output_type": "custom", "scale": 96.667, "power": -15, "digits": 3},
    "_A": {"output_type": "custom", "scale": 79.16, "power": -15, "digits": 3},
    "_A_h": {"output_type": "custom", "scale": 0.1, "digits": 1},
    "_W": {"output_type": "custom", "scale": 989.5, "power": -16, "digits": 3},
    }


MONITOR_INPUT_STEPS = [
    {
        "_module_path": "brokkr.inputs.currenttime",
        "_class_name": "CurrentTimeInput",
        },
    {
        "_module_path": "brokkr.inputs.runtime",
        "_class_name": "RunTimeInput",
        "precision": 3,
        },
    {
        "_module_path": "brokkr.inputs.modbus",
        "_class_name": "ModbusSerialInput",
        "name": "Sunsaver MPPT-15L Charge Controller",
        "unit": CONFIG["monitor"]["sunsaver_unit"],
        "start_address": (
            CONFIG["monitor"]["sunsaver_start_offset"]),
        "serial_port": CONFIG["monitor"]["sunsaver_port"],
        "serial_pids": CONFIG["monitor"]["sunsaver_pid_list"],
        "try_usb_reset": True,
        "modbus_kwargs": {
            "baudrate": 9600,
            "parity": "N",
            "stopbits": 2,
            "strict": False,
            },
        "variables": MPPT15L_VARIABLES,
        "custom_types": MPPT15L_CUSTOM_TYPES,
        },
    {
        "_module_path": "brokkr.inputs.ping",
        "_class_name": "PingInput",
        "name": "Sensor Ping",
        "host": CONFIG["general"]["ip_sensor"],
        "timeout_s": CONFIG["monitor"]["ping_timeout_s"],
        },
    {
        "_module_path": "brokkr.inputs.udp",
        "_class_name": "UDPInput",
        "name": "Sensor Health & Status",
        "host": CONFIG["general"]["ip_local"],
        "port": CONFIG["monitor"]["hs_port"],
        "timeout_s": CONFIG["monitor"]["hs_timeout_s"],
        "variables": HS_VARIABLES,
        },
    ]

MONITOR_OUTPUT_STEPS = [
    {
        "_module_path": "brokkr.outputs.csvfile",
        "_class_name": "CSVFileOutput",
        "name": "Monitoring Data CSV Output",
        "output_path": CONFIG["monitor"]["output_path_client"],
        "filename_template": CONFIG["general"]["output_filename_client"],
        "filename_kwargs": CONFIG["monitor"]["filename_kwargs"],
        },
    ]
