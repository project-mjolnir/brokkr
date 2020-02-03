"""
High-level functions to monitor and record sensor and sunsaver status data.
"""

# Standard library imports
import logging
from pathlib import Path
import threading

# Local imports
from brokkr.config.constants import OUTPUT_SUBPATH_TEST
from brokkr.config.dynamic import DYNAMIC_CONFIG
import brokkr.config.monitoring
from brokkr.config.static import CONFIG
import brokkr.output
import brokkr.utils.misc


logger = logging.getLogger(__name__)


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
    logger.debug("Status data: %r", status_data)
    return status_data


def format_status_data(status_data=None):
    status_data = get_status_data() if status_data is None else status_data
    status_data_list = [
        "{key}: {value!s}".format(
            key=key.replace("_", " ").title(), value=value)
        for key, value in status_data.items()]
    status_data_pretty = "\n".join(status_data_list)
    return status_data_pretty


def write_status_data(status_data,
                      output_path=CONFIG["monitor"]["output_path_client"]):
    output_path = Path(output_path)
    if not output_path.suffix:
        output_path = brokkr.output.render_output_filename(
            output_path=output_path, **CONFIG["monitor"]["filename_args"])
    logger.debug("Writing telemetry to file: %r",
                 output_path.as_posix())
    brokkr.output.write_line_csv(status_data, output_path)
    return status_data


def start_monitoring(
        output_path=CONFIG["monitor"]["output_path_client"],
        monitor_interval_s=DYNAMIC_CONFIG["monitor"]["monitor_interval_s"],
        sleep_interval=CONFIG["monitor"]["sleep_interval_s"],
        pretty=False,
        test_mode=False,
        exit_event=None,
        ):
    if exit_event is None:
        exit_event = threading.Event()
    if test_mode:
        output_path = OUTPUT_SUBPATH_TEST / output_path

    while not exit_event.is_set():
        try:
            status_data = get_status_data()
            if output_path is not None:
                write_status_data(status_data, output_path=output_path)
            elif logger.getEffectiveLevel() > logging.DEBUG:
                if pretty:
                    print(format_status_data(status_data))
                else:
                    print(f"Status data: {status_data}")
        except Exception as e:  # Keep recording data if an error occurs
            logger.critical("%s caught at main level: %s",
                            type(e).__name__, e)
            logger.info("Details:", exc_info=1)
        next_time = (brokkr.utils.misc.monotonic_ns()
                     + monitor_interval_s * 1e9
                     - (brokkr.utils.misc.monotonic_ns()
                        - brokkr.utils.misc.START_TIME)
                     % (monitor_interval_s * 1e9))
        while (not exit_event.is_set()
               and brokkr.utils.misc.monotonic_ns() < next_time):
            exit_event.wait(min(
                [sleep_interval,
                 (next_time - brokkr.utils.misc.monotonic_ns()) / 1e9]))
    exit_event.clear()
