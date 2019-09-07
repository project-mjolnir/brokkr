#!/usr/bin/env python3
"""
Main-level startup code for running the Brokkr package as an application.
"""

# Standard library modules
import argparse
import logging
from pathlib import Path
import signal
import threading
import time


EXIT_EVENT = threading.Event()

LOG_FORMAT_DETAILED = ("{asctime}.{msecs:0>3.0f} | {relativeCreated:.0f} | "
                       "{levelname} | {name} | {message}")
LOG_LEVEL_DEFAULT = "INFO"
LOG_LOCATION = Path.home() / "brokkr.log"


def quit_handler(signo, _frame):
    logger.info("Interrupted by signal %s; terminating Brokkr", signo)
    logging.shutdown()
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
    arg_parser.add_argument("--loglevel", type=str, dest="log_level",
                            help="Interval between status checks, in s.")
    arg_parser.add_argument("-v", "--verbose", action="store_true",
                            help="If passed, will print all data recieved.")
    return arg_parser


# --- Begin startup code ---

parsed_args = generate_argparser().parse_args()

# Handle getting and cleaning up log level from args
try:
    log_level = parsed_args.log_level
except AttributeError:
    log_level = LOG_LEVEL_DEFAULT
else:
    del parsed_args.log_level

logger = logging.getLogger()
logger.setLevel(log_level)
detailed_formatter = logging.Formatter(fmt=LOG_FORMAT_DETAILED,
                                       datefmt="%Y-%m-%d %H:%M:%S",
                                       style="{")
detailed_formatter.converter = time.gmtime

file_handler = logging.FileHandler(LOG_LOCATION)
file_handler.setLevel(log_level)
file_handler.setFormatter(detailed_formatter)
logger.addHandler(file_handler)

# In verbose mode, also print log messages to the console
if getattr(parsed_args, "verbose", False):
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(detailed_formatter)
    logger.addHandler(console_handler)

logger.info("Starting Brokkr...")
logger.debug("Log level: %s; Arguments: %s", log_level, parsed_args)

# Import top-level modules
import monitor

# Start the mainloop
set_quit_signal_handler(quit_handler)
logger.debug("Entering mainloop...")
monitor.start_logging_status_data(exit_event=EXIT_EVENT, **vars(parsed_args))
