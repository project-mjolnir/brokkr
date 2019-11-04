"""
Programmatic configuration for the monitoring routine and its data items.
"""

# Standard library imports
import datetime

# Local imports
import brokkr.monitoring.sensor
import brokkr.monitoring.sunsaver


STATUS_DATA_ITEMS = {
    "time": {
        "function": datetime.datetime.utcnow,
        "unpack": False,
        },
    "runtime": {
        "function": brokkr.utils.misc.start_time_offset,
        "unpack": False,
        },
    "ping": {
        "function": brokkr.monitoring.sensor.ping,
        "unpack": False,
        },
    "sunsaver": {
        "function": brokkr.monitoring.sunsaver.get_sunsaver_data,
        "unpack": True,
        },
    "hs": {
        "function": brokkr.monitoring.sensor.get_hs_data,
        "unpack": True,
        },
    }
