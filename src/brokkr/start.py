#!/usr/bin/env python3
"""
Startup code for running the Brokkr client mainloop as an application.
"""

# Standard library imports
import copy
import logging
import logging.config
import signal
import threading
import time


EXIT_EVENT = threading.Event()

SIGNALS_SET = ("SIG" + signame for signame in ("TERM", "HUP", "INT", "BREAK"))


def quit_handler(signo, _frame):
    logger = logging.getLogger(__name__)
    logger.warning("Interrupted by signal %s; terminating Brokkr", signo)
    logging.shutdown()
    EXIT_EVENT.set()


def set_quit_signal_handler(signal_handler, signals=SIGNALS_SET):
    for signal_type in signals:
        try:
            signal.signal(getattr(signal, signal_type), signal_handler)
        except AttributeError:  # Windows doesn't have SIGHUP
            continue


def setup_log_levels(log_config, file_level=None, console_level=None):
    file_level = (file_level.upper()
                  if isinstance(file_level, str) else file_level)
    console_level = (console_level.upper()
                     if isinstance(console_level, str) else console_level)
    for handler, level in (("file", file_level), ("console", console_level)):
        if level:
            log_config["handlers"][handler]["level"] = level
            if handler not in log_config["root"]["handlers"]:
                log_config["root"]["handlers"].append(handler)
    levels_tocheck = (level for level in (
        file_level, console_level, log_config["root"]["level"]
        ) if (level == 0 or level))
    level_min = min((int(getattr(logging, str(level_name), level_name))
                     for level_name in levels_tocheck))
    log_config["root"]["level"] = level_min
    return log_config


def setup_basic_log_config(verbose=False):
    # Setup logging config
    log_args = {"format": "{levelname} | {name} | {message}",
                "style": "{"}
    if verbose and verbose == 1:
        log_level = logging.INFO
    elif verbose and verbose >= 2:
        log_level = logging.DEBUG
        if verbose >= 3:
            log_args["level"] = logging.DEBUG
    else:
        log_level = logging.WARNING

    # Initialize logging
    logging.basicConfig(**log_args)
    if verbose <= 2:
        package_logger = logging.getLogger("brokkr")
        package_logger.setLevel(log_level)
    return log_level


def setup_full_log_config(log_level_file=None, log_level_console=None):
    # Load and set logging config
    logging.Formatter.converter = time.gmtime
    from brokkr.config.log import LOG_CONFIG
    log_config = copy.deepcopy(LOG_CONFIG)
    if any((log_level_file, log_level_console)):
        log_config = setup_log_levels(
            log_config, log_level_file, log_level_console)
    logging.config.dictConfig(log_config)
    return log_config


def start_monitoring(verbose=None, **monitor_args):
    # Drop output_path arg if true to use default path in function signature
    if monitor_args.get("output_path", None) is True:
        monitor_args.pop("output_path", None)

    # Setup logging if not already configured
    if verbose is not None:
        setup_basic_log_config(verbose)
    logger = logging.getLogger(__name__)

    # Print logging information
    logger.info("Starting monitoring system...")
    logger.info("Monitor arguments: %s", monitor_args)

    # Start the mainloop
    import brokkr.monitoring.monitor
    set_quit_signal_handler(quit_handler)
    logger.debug("Entering monitoring mainloop...")
    brokkr.monitoring.monitor.start_monitoring(
        exit_event=EXIT_EVENT, **monitor_args)


def start_brokkr(log_level_file=None, log_level_console=None, **monitor_args):
    # Avoid users trying to start Brokkr without setting up the unit config
    import brokkr.config.unit
    if len(brokkr.config.unit.CONFIGS["local"]) <= 1:
        raise RuntimeError("No unit config file found, exiting.")

    # Setup logging
    log_config = setup_full_log_config(
        log_level_file=log_level_file, log_level_console=log_level_console)
    logger = logging.getLogger(__name__)

    # Print logging information
    import brokkr
    logger.info("Starting Brokkr version %s...", brokkr.__version__)
    if any((log_level_file, log_level_console)):
        logger.info("Using manual log levels: %s (file), %s (console)",
                    log_level_file, log_level_console)
    logger.debug("Logging config: %s", log_config)

    # Start monitoring system
    start_monitoring(verbose=None, **monitor_args)


if __name__ == "__main__":
    start_brokkr()
