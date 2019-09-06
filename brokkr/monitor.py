"""
Monitor and log sensor and sunsaver status data.
"""

# Standard library imports
import datetime
import os
from pathlib import Path
import threading

# Local imports
from config import CONFIG
import output
import sensor
import sunsaver
import utils


START_TIME = utils.monotonic_ns()


def get_status_data():
    current_time = datetime.datetime.utcnow()
    run_time = round((utils.monotonic_ns() - START_TIME) / 1e9, 1)
    ping_succeeded = sensor.ping()
    charge_data = sunsaver.get_sunsaver_data()

    status_data = {
        "time": current_time,
        "runtime": run_time,
        "ping": ping_succeeded,
        }
    status_data = {**status_data, **charge_data}
    return status_data


def log_status_data(output_path=CONFIG["monitor"]["output_path"],
                    verbose=CONFIG["verbose"]):
    status_data = get_status_data()
    if verbose:
        print(status_data)
    if not output_path.suffix:
        output_path = output.determine_output_filename(output_path)
    output.write_line_csv(status_data, output_path)
    return status_data


def start_logging_status_data(
        output_path=CONFIG["monitor"]["output_path"],
        time_interval=CONFIG["monitor"]["interval_s"],
        verbose=CONFIG["verbose"],
        exit_event=threading.Event()):
    if not Path(output_path).suffix:
        os.makedirs(output_path, exist_ok=True)

    while not exit_event.is_set():
        try:
            log_status_data(output_path, verbose=verbose)
        except Exception as e:  # Keep logging if an error occurs
            print(f"{datetime.datetime.utcnow()!s} "
                  f"Main-level error occured: {type(e)} {e}")
        next_time = (utils.monotonic_ns() + time_interval * 1e9
                     - (utils.monotonic_ns() - START_TIME)
                     % (time_interval * 1e9))
        while not exit_event.is_set() and utils.monotonic_ns() < next_time:
            exit_event.wait(min([1, (next_time - utils.monotonic_ns()) / 1e9]))
    exit_event.clear()
