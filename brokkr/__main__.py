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
LOG_LEVEL_FILE = "INFO"
LOG_LEVEL_CONSOLE = None
LOG_LOCATION = Path.home() / "brokkr.log"

SIGNALS_SET = ("SIG" + signame for signame in ("TERM", "HUP", "INT", "BREAK"))


def quit_handler(signo, _frame):
    logger.info("Interrupted by signal %s; terminating Brokkr", signo)
    logging.shutdown()
    EXIT_EVENT.set()


def set_quit_signal_handler(signal_handler, signals=SIGNALS_SET):
    for signal_type in signals:
        try:
            signal.signal(getattr(signal, signal_type), signal_handler)
        except AttributeError:  # Windows doesn't have SIGHUP
            continue


def generate_argparser():
    arg_parser = argparse.ArgumentParser(
        description="Log data at regular intervals about the HAMMA2 system.",
        argument_default=argparse.SUPPRESS)
    arg_parser.add_argument("--output_path", type=Path,
                            help="The filename to save the data to.")
    arg_parser.add_argument("--interval", type=int, dest="monitor_interval",
                            help="Interval between status checks, in s.")
    arg_parser.add_argument("--log-level-file", type=str,
                            default=LOG_LEVEL_FILE,
                            help="Level of messages to log to disk.")
    arg_parser.add_argument("--log-level-console", type=str,
                            default=LOG_LEVEL_CONSOLE,
                            help="Level of messages to log to the console.")
    arg_parser.add_argument("-v", "--verbose", action="store_true",
                            help="If passed, will also print the data logged.")
    return arg_parser


# --- Begin startup code ---

parsed_args = generate_argparser().parse_args()

logger = logging.getLogger()
file_level, console_level = (parsed_args.log_level_file,
                             parsed_args.log_level_console)
detailed_formatter = logging.Formatter(fmt=LOG_FORMAT_DETAILED,
                                       datefmt="%Y-%m-%d %H:%M:%S",
                                       style="{")
detailed_formatter.converter = time.gmtime
handlers_toadd = []

file_handler = logging.FileHandler(LOG_LOCATION)
file_handler.setLevel(file_level)
file_handler.setFormatter(detailed_formatter)
handlers_toadd.append(file_handler)

# If explictly called, also print log messages to the console
add_console_handler = console_level and console_level.lower() != "none"
if add_console_handler:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(detailed_formatter)
    handlers_toadd.append(console_handler)

logger.setLevel(min((handler.level for handler in handlers_toadd)))
for handler in handlers_toadd:
    logger.addHandler(handler)

logger.info("Starting Brokkr...")
logger.debug("Arguments: %s", parsed_args)

# Clean up log level args not needed by monitoring function
del parsed_args.log_level_file
del parsed_args.log_level_console

# Import top-level modules
import monitor

# Start the mainloop
set_quit_signal_handler(quit_handler)
logger.debug("Entering mainloop...")
monitor.start_monitoring(exit_event=EXIT_EVENT, **vars(parsed_args))
