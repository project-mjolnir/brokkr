#!/usr/bin/env python3
"""
Main-level startup code for running the Brokkr package as an application.
"""

# Standard library modules
import argparse
import copy
import logging
import logging.config
from pathlib import Path
import signal
import threading
import time

# Local imports
from brokkr.config.log import LOG_CONFIG

EXIT_EVENT = threading.Event()

SIGNALS_SET = ("SIG" + signame for signame in ("TERM", "HUP", "INT", "BREAK"))


def quit_handler(signo, _frame):
    logger = logging.getLogger(__name__)
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
                            help="Level of messages to log to disk.")
    arg_parser.add_argument("--log-level-console", type=str,
                            help="Level of messages to log to the console.")
    arg_parser.add_argument("-v", "--verbose", action="store_true",
                            help="If passed, will also print the data logged.")
    arg_parser.add_argument("--version", action="store_true",
                            help="If passed, will print the version and exit.")
    return arg_parser


def setup_log_levels(parsed_args, log_config=None):
    if log_config is None:
        log_config = copy.deepcopy(LOG_CONFIG)
    file_level, console_level = (
        getattr(parsed_args, "log_level_file", "").upper(),
        getattr(parsed_args, "log_level_console", "").upper())
    for level_type, level in [("file", file_level),
                              ("console", console_level)]:
        if level:
            log_config["handlers"][level_type]["level"] = level
            if level_type not in log_config["root"]["handlers"]:
                log_config["root"]["handlers"].append(level_type)
    if any((file_level, console_level)):
        levels_tocheck = (level for level in (
            file_level, console_level, log_config["root"]["level"]
            ) if (level == 0 or level))
        level_min = min((int(getattr(logging, str(level_name), level_name))
                         for level_name in levels_tocheck))
        log_config["root"]["level"] = level_min
    return log_config


# --- Begin startup code ---

def main():
    parsed_args = generate_argparser().parse_args()

    if getattr(parsed_args, "version", None):
        import brokkr
        print("Brokkr version " + str(brokkr.__version__))
        return

    # Setup log levels
    logging.Formatter.converter = time.gmtime
    log_config = setup_log_levels(parsed_args)

    logging.config.dictConfig(log_config)
    logger = logging.getLogger(__name__)

    logger.info("Starting Brokkr...")
    logger.debug("Arguments: %s", parsed_args)

    # Clean up log level args not needed by monitoring function
    for arg_name in ["log_level_file", "log_level_console", "version"]:
        try:
            delattr(parsed_args, arg_name)
        except Exception:  # Ignore any problem deleting the args
            pass

    # Import top-level modules
    import brokkr.monitor

    # Start the mainloop
    set_quit_signal_handler(quit_handler)
    logger.debug("Entering mainloop...")
    brokkr.monitor.start_monitoring(exit_event=EXIT_EVENT,
                                    **vars(parsed_args))


if __name__ == "__main__":
    main()
