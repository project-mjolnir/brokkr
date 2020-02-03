#!/usr/bin/env python3
"""
Startup code for running the Brokkr client mainloop as an application.
"""

# Standard library imports
import copy
import logging
import logging.config
import os
from pathlib import Path
import signal
import threading
import time

# Local imports
from brokkr.config.constants import (
    PACKAGE_NAME,
    OUTPUT_PATH_DEFAULT_EXPANDED,
    OUTPUT_SUBPATH_TEST,
    )
import brokkr.utils.misc


EXIT_EVENT = threading.Event()
SIGNALS_SET = ("SIG" + signame for signame in ("TERM", "HUP", "INT", "BREAK"))

CONFIG_REQUIRE = ["system", "unit"]


def quit_handler(signo, _frame):
    logger = logging.getLogger(__name__)
    logger.warning("Interrupted by signal %s; terminating %s",
                   PACKAGE_NAME.title(), signo)
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


def setup_full_log_config(
        log_level_file=None,
        log_level_console=None,
        test_mode=False,
        ):
    # Load and set logging config
    from brokkr.config.bootstrap import (
        METADATA_CONFIG, UNIT_CONFIG, LOG_CONFIG)
    logging.Formatter.converter = time.gmtime
    log_config = copy.deepcopy(LOG_CONFIG)
    if any((log_level_file, log_level_console)):
        log_config = setup_log_levels(
            log_config, log_level_file, log_level_console)
    for log_handler in log_config["handlers"].values():
        if log_handler.get("filename", None):
            log_handler["filename"] = Path(log_handler["filename"].format(
                system_name=METADATA_CONFIG["name"],
                unit_number=UNIT_CONFIG["number"],
                )).expanduser()
            if test_mode:
                try:
                    relative_filename = log_handler["filename"].relative_to(
                        OUTPUT_PATH_DEFAULT_EXPANDED)
                except ValueError:
                    # If path is not relative to output dir
                    log_handler["filename"] = (
                        log_handler["filename"].parent / OUTPUT_SUBPATH_TEST
                        / log_handler["filename"].name)
                else:
                    log_handler["filename"] = (
                        OUTPUT_PATH_DEFAULT_EXPANDED / OUTPUT_SUBPATH_TEST
                        / relative_filename)
            os.makedirs(log_handler["filename"].parent, exist_ok=True)
    logging.config.dictConfig(log_config)
    return log_config


def warn_on_startup_issues():
    from brokkr.config.systemhandler import CONFIG_HANDLER_SYSTEM
    from brokkr.config.system import SYSTEM_CONFIG
    from brokkr.config.handlers import (CONFIG_HANDLER_UNIT,
                                        CONFIG_HANDLER_METADATA)
    from brokkr.config.bootstrap import UNIT_CONFIGS
    logger = logging.getLogger(__name__)

    # Avoid users trying to start Brokkr without setting up the basic config
    issues_found = False
    system_path = SYSTEM_CONFIG["system_path"]
    if not system_path:
        logger.warning(
            "No system path config found at %r, falling back to defaults",
            CONFIG_HANDLER_SYSTEM.config_levels["local"].path.as_posix())
        issues_found = True
    if not Path(system_path).exists():
        logger.error(
            "No system config directory found at system path %r",
            SYSTEM_CONFIG["system_path"].as_posix())
        issues_found = True
    else:
        if not CONFIG_HANDLER_METADATA.config_levels["system"].path.exists():
            logger.warning(
                "No system config directory found at system path %r",
                SYSTEM_CONFIG["system_path"].as_posix())
            issues_found = True
    if UNIT_CONFIGS["local"].get("number", None) is None:
        logger.warning(
            "No local unit config found at %r, falling back to defaults",
            CONFIG_HANDLER_UNIT.config_levels["local"].path.as_posix())
        issues_found = True

    return issues_found


def generate_version_message():
    import brokkr
    client_version_message = (
        f"{PACKAGE_NAME.title()} version {str(brokkr.__version__)}")
    level_name = brokkr.config.handlers.LEVEL_NAME_SYSTEM
    try:
        from brokkr.config.bootstrap import METADATA_CONFIGS
    except Exception:
        system_version_message = "Error loading system metadata"
    else:
        if not METADATA_CONFIGS[level_name]:
            system_version_message = "No system metadata found"
        else:
            if METADATA_CONFIGS[level_name].get("name_full", None):
                system_name = METADATA_CONFIGS[level_name]["name_full"]
            else:
                system_name = METADATA_CONFIGS[level_name].get(
                    "name", "System unknown")
            system_version = METADATA_CONFIGS[level_name].get(
                "version", "unknown")
            system_version_message = f"{system_name} version {system_version}"
    full_message = ", ".join([client_version_message, system_version_message])
    return full_message


@brokkr.utils.misc.basic_logging
def print_status(pretty=True):
    import brokkr.monitoring.monitor
    logger = logging.getLogger(__name__)
    logger.debug("Getting oneshot status data...")
    if pretty:
        print(brokkr.monitoring.monitor.format_status_data())
    else:
        print(brokkr.monitoring.monitor.get_status_data())


def start_monitoring(verbose=None, quiet=None, **monitor_args):
    import brokkr.utils.misc

    # Drop output_path arg if true to use default path in function signature
    if monitor_args.get("output_path_client", None) is True:
        monitor_args.pop("output_path_client", None)

    # Setup logging if not already configured
    if verbose is not None or quiet is not None:
        brokkr.utils.misc.setup_basic_logging(
            verbose=verbose, quiet=quiet, script_mode=False)
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


def start_brokkr(log_level_file=None, log_level_console=None,
                 test_mode=False, **monitor_args):
    from brokkr.config.system import SYSTEM_CONFIGS, SYSTEM_CONFIG
    from brokkr.config.bootstrap import (
        LOG_CONFIGS,
        UNIT_CONFIGS, UNIT_CONFIG,
        METADATA_CONFIGS, METADATA_CONFIG,
        )

    # Setup logging
    log_config = setup_full_log_config(
        log_level_file=log_level_file,
        log_level_console=log_level_console,
        test_mode=test_mode,
        )
    logger = logging.getLogger(__name__)

    # Print startup message and warn on some problem states
    logger.info("Starting %s...", generate_version_message())
    warn_on_startup_issues()

    # Print config information
    if any((log_level_file, log_level_console)):
        logger.info("Using manual log levels: %s (file), %s (console)",
                    log_level_file, log_level_console)
    logger.debug("Logging config hierarchy: %r", LOG_CONFIGS)
    logger.info("Logging config: %r", log_config)
    logger.debug("System config hierarchy: %r", SYSTEM_CONFIGS)
    logger.info("System config: %r", SYSTEM_CONFIG)
    logger.debug("System metadata hierarchy: %r", METADATA_CONFIGS)
    logger.info("System metadata: %r", METADATA_CONFIG)
    logger.debug("Unit config hierarchy: %r", UNIT_CONFIGS)
    logger.info("Unit config: %r", UNIT_CONFIG)

    # Start monitoring system
    start_monitoring(test_mode=test_mode, **monitor_args)


if __name__ == "__main__":
    start_brokkr()
