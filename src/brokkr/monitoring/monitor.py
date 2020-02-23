"""
High-level functions to monitor and record sensor and sunsaver status data.
"""

# Standard library imports
import logging
from pathlib import Path
import sys

# Local imports
from brokkr.config.dynamic import DYNAMIC_CONFIG
import brokkr.config.monitoring
from brokkr.config.static import CONFIG
import brokkr.output
import brokkr.utils.misc


CURSOR_UP_CHAR = '\x1b[1A'
ERASE_LINE_CHAR = '\x1b[2K'

LOGGER = logging.getLogger(__name__)


def get_status_data(status_data_items=None):
    if status_data_items is None:
        status_data_items = brokkr.config.monitoring.STATUS_DATA_ITEMS

    status_data = {}
    for item_name, item_params in status_data_items.items():
        output_data = item_params["function"]()
        if item_params["unpack"]:
            status_data.update(output_data)
        else:
            status_data[item_name] = output_data
    LOGGER.debug("Status data: %r", status_data)
    return status_data


def format_status_data(status_data=None, seperator="\n"):
    status_data = get_status_data() if status_data is None else status_data
    status_data_list = [
        "{key}: {value!s}".format(
            key=key.replace("_", " ").title(), value=value)
        for key, value in status_data.items()]
    status_data_pretty = seperator.join(status_data_list) + "\n"
    return status_data_pretty


def write_status_data(status_data,
                      output_path=CONFIG["monitor"]["output_path_client"]):
    output_path = Path(output_path)
    if not output_path.suffix:
        output_path = brokkr.output.render_output_filename(
            output_path=output_path, **CONFIG["monitor"]["filename_args"])
    LOGGER.debug("Writing telemetry to file: %r", output_path.as_posix())
    brokkr.output.write_line_csv(status_data, output_path)
    return status_data


def run_monitoring_pass(
        output_path=CONFIG["monitor"]["output_path_client"],
        pretty=False,
        delete_previous=False,
        ):
    try:
        status_data = get_status_data()
        if output_path is not None:
            write_status_data(status_data, output_path=output_path)
        elif LOGGER.getEffectiveLevel() > logging.DEBUG:
            if pretty:
                output_str = format_status_data(status_data)
                if delete_previous:
                    output_str = ((CURSOR_UP_CHAR + ERASE_LINE_CHAR)
                                  * output_str.count("\n") + output_str)
                sys.stdout.write(output_str)
                sys.stdout.flush()
            else:
                print(f"Status data: {status_data}")
    except Exception as e:  # Keep recording data if an error occurs
        LOGGER.critical("%s caught at main level: %s", type(e).__name__, e)
        LOGGER.info("Details:", exc_info=1)
    logging.disable()
    return status_data


def start_monitoring(monitor_interval_s=None, **monitoring_args):
    LOGGER.info("Starting monitoring system...")
    if monitor_interval_s is None:
        monitor_interval_s = DYNAMIC_CONFIG["monitor"]["monitor_interval_s"]
    LOGGER.debug("Entering monitoring mainloop...")
    run_monitoring_pass(**monitoring_args)
    brokkr.utils.misc.run_periodic(
        run_monitoring_pass, period_s=monitor_interval_s)(
            **monitoring_args, delete_previous=True)
