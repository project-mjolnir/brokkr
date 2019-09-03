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
from config import CONFIG
import output
import sensor
import sunsaver


START_TIME = time.monotonic_ns()
EXIT_EVENT = threading.Event()


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
    run_time = round((time.monotonic_ns() - START_TIME) / 1e9, 1)
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
        verbose=CONFIG["verbose"]):
    if not output_path.suffix:
        os.makedirs(output_path, exist_ok=True)

    while not EXIT_EVENT.is_set():
        try:
            log_status_data(output_path, verbose=verbose)
        except Exception as e:  # Keep logging if an error occurs
            print(f"{datetime.datetime.utcnow()!s} "
                  f"Main-level error occured: {type(e)} {e}")
        next_time = (time.monotonic_ns() + time_interval * 1e9
                     - (time.monotonic_ns() - START_TIME)
                     % (time_interval * 1e9))
        while not EXIT_EVENT.is_set() and time.monotonic_ns() < next_time:
            EXIT_EVENT.wait(min([1, (next_time - time.monotonic_ns()) / 1e9]))
    EXIT_EVENT.clear()


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(
        description="Log data at regular intervals about the HAMMA2 system.")
    arg_parser.add_argument("output_path", nargs="?", type=Path,
                            default=CONFIG["monitor"]["output_path"],
                            help="The filename to save the data to.")
    arg_parser.add_argument("--interval", action="store",
                            default=CONFIG["monitor"]["interval_s"],
                            type=int, dest="time_interval",
                            help="Interval between status checks, in s.")
    arg_parser.add_argument("-v", "--verbose", action="store_true",
                            help="If passed, will print all data recieved.")
    set_quit_signal_handler(quit_handler)
    parsed_args = arg_parser.parse_args()
    start_logging_status_data(**vars(parsed_args))
