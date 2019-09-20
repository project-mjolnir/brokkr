"""
Startup code for running the Brokkr client mainloop as an application.
"""

# Standard library modules
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
    logger.info("Interrupted by signal %s; terminating Brokkr", signo)
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


def start_brokkr(log_level_file=None, log_level_console=None, **monitor_args):
    logging.Formatter.converter = time.gmtime

    from brokkr.config.log import LOG_CONFIG
    log_config = copy.deepcopy(LOG_CONFIG)
    if any((log_level_file, log_level_console)):
        log_config = setup_log_levels(
            log_config, log_level_file, log_level_console)

    logging.config.dictConfig(log_config)
    logger = logging.getLogger(__name__)

    logger.info("Starting Brokkr...")
    if any((log_level_file, log_level_console)):
        logger.debug("Using manual log levels: %s (file) | %s (console)",
                     log_level_file, log_level_console)
    logger.debug("Logging config: %s", log_config)
    logger.debug("Arguments: %s", monitor_args)

    # Import top-level modules
    import brokkr.monitor

    # Start the mainloop
    set_quit_signal_handler(quit_handler)
    logger.debug("Entering mainloop...")
    brokkr.monitor.start_monitoring(exit_event=EXIT_EVENT, **monitor_args)
