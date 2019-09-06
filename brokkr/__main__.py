#!/usr/bin/env python3
"""
Main-level startup code for running the Brokkr package as an application.
"""

# Standard library modules
import argparse
import datetime
from pathlib import Path
import signal
import threading


EXIT_EVENT = threading.Event()


def quit_handler(signo, _frame):
    print(f"{datetime.datetime.utcnow()!s} "
          f"Interrupted by signal {signo}; terminating Brokkr")
    EXIT_EVENT.set()


def set_quit_signal_handler(handler, signals=("TERM", "HUP", "INT", "BREAK")):
    for signal_type in signals:
        try:
            signal.signal(getattr(signal, "SIG" + signal_type), handler)
        except AttributeError:  # Windows doesn't have SIGHUP
            continue


def generate_argparser():
    arg_parser = argparse.ArgumentParser(
        description="Log data at regular intervals about the HAMMA2 system.",
        argument_default=argparse.SUPPRESS)
    arg_parser.add_argument("--output_path", type=Path,
                            help="The filename to save the data to.")
    arg_parser.add_argument("--interval", type=int, dest="time_interval",
                            help="Interval between status checks, in s.")
    arg_parser.add_argument("-v", "--verbose", action="store_true",
                            help="If passed, will print all data recieved.")
    return arg_parser


# --- Begin startup code ---

parsed_args = generate_argparser().parse_args()

print(f"{datetime.datetime.utcnow()!s} "
      "Starting Brokkr...")

# Import top-level modules
import monitor

# Start the mainloop
set_quit_signal_handler(quit_handler)
monitor.start_logging_status_data(exit_event=EXIT_EVENT, **vars(parsed_args))
