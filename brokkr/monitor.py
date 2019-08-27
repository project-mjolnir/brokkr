#!/usr/bin/env python3

"""
Monitor and log sensor and sunsaver status data.
"""

# Standard library imports
import argparse
import datetime
import os
from pathlib import Path
import signal
import threading
import time

# Local imports
import output
import sensor
import sunsaver


EXIT_EVENT = threading.Event()

DEFAULT_DATA_PATH = Path().home() / "data" / "monitor"


def quit_handler(signo, _frame):
    print(f"{datetime.datetime.utcnow()!s} "
          f"Interrupted by signal {signo}; terminating data logging")
    EXIT_EVENT.set()


def set_quit_signal_handler(handler, signals=("TERM", "HUP", "INT", "BREAK")):
    for signal_type in signals:
        try:
            signal.signal(getattr(signal, "SIG" + signal_type), handler)
        except AttributeError:  # Windows doesn't have SIGHUP
            continue


def get_status_data():
    current_time = datetime.datetime.utcnow()
    ping_succeeded = sensor.ping()
    charge_data = sunsaver.get_sunsaver_data()

    status_data = {
        "time": current_time,
        "ping": ping_succeeded,
        }
    status_data = {**status_data, **charge_data}
    return status_data


def log_status_data(output_path, verbose=False):
    status_data = get_status_data()
    if verbose:
        print(status_data)
    if not output_path.suffix:
        output_path = output.determine_output_filename(output_path)
    output.write_line_csv(status_data, output_path)
    return status_data


def start_logging_status_data(output_path=Path(DEFAULT_DATA_PATH),
                              time_interval=60, verbose=False):
    start_time = time.monotonic()
    if not output_path.suffix:
        os.makedirs(output_path, exist_ok=True)

    while not EXIT_EVENT.is_set():
        try:
            log_status_data(output_path, verbose=verbose)
        except Exception as e:  # Keep logging if an error occurs
            print(f"{datetime.datetime.utcnow()!s} "
                  f"Main-level error occured: {type(e)} {e}")
        end_time = (time.monotonic() + time_interval
                    - (time.monotonic() - start_time) % time_interval)
        while not EXIT_EVENT.is_set() and time.monotonic() < end_time:
            EXIT_EVENT.wait(min([1, end_time - time.monotonic()]))
    EXIT_EVENT.clear()


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(
        description="Log data at regular intervals about the HAMMA2 system.")
    arg_parser.add_argument("output_path", nargs="?", type=Path,
                            default=DEFAULT_DATA_PATH,
                            help="The filename to save the data to.")
    arg_parser.add_argument("--interval", action="store", default=60,
                            type=int, dest="time_interval",
                            help="Interval between status checks, in s.")
    arg_parser.add_argument("-v", "--verbose", action="store_true",
                            help="If passed, will print all data recieved.")
    set_quit_signal_handler(quit_handler)
    parsed_args = arg_parser.parse_args()
    start_logging_status_data(**vars(parsed_args))
