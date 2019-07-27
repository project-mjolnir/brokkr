#!/usr/bin/env python3

"""
Monitor and log sensor and sunsaver status data.
"""

# Standard library imports
import argparse
import datetime
import signal
import time
import threading

# Local imports
import sunsaver
import sensor
import output


EXIT_EVENT = threading.Event()


def quit_handler(signo, _frame):
    print(f"{datetime.datetime.utcnow()!s} "
          f"Interrupted by signal {signo}; terminating data logging")
    EXIT_EVENT.set()


def get_status_data():
    current_time = datetime.datetime.utcnow()
    ping_succeeded = sensor.ping()

    status_data = {
        "time": current_time,
        "ping": ping_succeeded,
        }

    charge_data = sunsaver.get_sunsaver_data()
    status_data = {**status_data, **charge_data}
    return status_data


def log_status_data(output_filename, verbose=False):
    status_data = get_status_data()
    if verbose:
        print(status_data)
    output.write_line_csv(status_data, output_filename)
    return status_data


def start_logging_status_data(output_filename="data.csv", time_interval=60,
                              verbose=False):
    start_time = time.monotonic()
    while not EXIT_EVENT.is_set():
        try:
            log_status_data(output_filename, verbose=verbose)
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
    arg_parser.add_argument("output_filename", nargs="?", default="data.csv",
                            help="The filename to save the data to.")
    arg_parser.add_argument("--interval", action="store", default=60,
                            type=int, dest="time_interval",
                            help="Interval between status checks, in s.")
    arg_parser.add_argument("-v", "--verbose", action="store_true",
                            help="If passed, will print all data recieved.")
    parsed_args = arg_parser.parse_args()
    for signal_type in ("TERM", "HUP", "INT", "BREAK"):
        try:
            signal.signal(getattr(signal, "SIG" + signal_type), quit_handler)
        except AttributeError:  # Windows doesn't have SIGHUP
            continue
    start_logging_status_data(**vars(parsed_args))
