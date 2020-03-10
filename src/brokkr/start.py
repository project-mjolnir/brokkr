#!/usr/bin/env python3
"""
Startup code for running the Brokkr client mainloop as an application.
"""

# pylint: disable=import-outside-toplevel, redefined-outer-name, reimported

# Standard library imports
import logging
import logging.config
import multiprocessing
from pathlib import Path

# Local imports
from brokkr.constants import LEVEL_NAME_SYSTEM, PACKAGE_NAME
import brokkr.utils.log


CONFIG_REQUIRE = ["systempath", "unit"]


# --- Startup helper functions --- #

def warn_on_startup_issues():
    from brokkr.config.systempath import SYSTEMPATH_CONFIG
    from brokkr.config.handlers import (CONFIG_HANDLER_UNIT,
                                        CONFIG_HANDLER_METADATA)
    from brokkr.config.unit import UNIT_CONFIGS
    import brokkr.utils.misc

    logger = logging.getLogger(__name__)

    issues_found = False

    # Avoid users trying to start Brokkr without setting up the basic config
    try:
        system_path = brokkr.utils.misc.get_system_path(
            SYSTEMPATH_CONFIG, errors="raise")
    except RuntimeError as e:
        logger.warning("%s getting system path: %s", type(e).__name__, e)
        logger.debug("Error details:", exc_info=True)
        issues_found = True
    except KeyError as e:
        logger.error("System path %s not found in %r", type(e).__name__, e)
        logger.info("Error details:", exc_info=True)
        issues_found = True
    else:
        issues_found = not brokkr.utils.misc.validate_system_path(
            system_path=system_path,
            metadata_handler=CONFIG_HANDLER_METADATA,
            logger=logger,
            )

    if UNIT_CONFIGS["local"].get("number", None) is None:
        logger.warning(
            "No local unit config found at %r, falling back to defaults",
            CONFIG_HANDLER_UNIT.config_levels["local"].path.as_posix())
        issues_found = True

    return issues_found


def log_config_info(log_config=None, logger=None):
    # pylint: disable=too-many-locals, useless-suppression
    from brokkr.config.log import LOG_CONFIG, LOG_CONFIGS
    from brokkr.config.main import CONFIG, CONFIGS
    from brokkr.config.metadata import METADATA, METADATA_CONFIGS
    from brokkr.config.systempath import SYSTEMPATH_CONFIG, SYSTEMPATH_CONFIGS
    from brokkr.config.unit import UNIT_CONFIG, UNIT_CONFIGS

    if logger is None:
        logger = logging.getLogger(__name__)
    if log_config is None:
        log_config = LOG_CONFIG

    # Print config information
    for config_name, config_data in {
            "Systempath": (SYSTEMPATH_CONFIG, SYSTEMPATH_CONFIGS),
            "Metadata": (METADATA, METADATA_CONFIGS),
            "Unit": (UNIT_CONFIG, UNIT_CONFIGS),
            "Log": (log_config, LOG_CONFIGS),
            "Main": (CONFIG, CONFIGS),
            }.items():  # pylint: disable=bad-continuation
        logger.info("%s config: %s", config_name, config_data[0])
        logger.debug("%s config hierarchy: %s", config_name, config_data[1])


def generate_version_message():
    import brokkr
    client_version_message = (
        f"{PACKAGE_NAME.title()} version {str(brokkr.__version__)}")
    try:
        from brokkr.config.metadata import METADATA_CONFIGS
    except Exception:
        system_version_message = "Error loading system metadata"
    else:
        if not METADATA_CONFIGS[LEVEL_NAME_SYSTEM]:
            system_version_message = "No system metadata found"
        else:
            if METADATA_CONFIGS[LEVEL_NAME_SYSTEM].get("name_full", None):
                system_name = METADATA_CONFIGS[LEVEL_NAME_SYSTEM]["name_full"]
            else:
                system_name = METADATA_CONFIGS[LEVEL_NAME_SYSTEM].get(
                    "name", "System unknown")
            system_version = METADATA_CONFIGS[LEVEL_NAME_SYSTEM].get(
                "version", "unknown")
            system_version_message = f"{system_name} version {system_version}"
    full_message = ", ".join([client_version_message, system_version_message])
    return full_message


def log_startup_messages(log_config=None, log_level_file=None,
                         log_level_console=None, logger=None):
    if logger is None:
        logger = logging.getLogger(__name__)

    # Print startup message, warn on some problem states and log config info
    logger.info("Starting %s...", generate_version_message())
    warn_on_startup_issues()
    if any((log_level_file, log_level_console)):
        logger.info("Using manual log levels: %s (file), %s (console)",
                    log_level_file, log_level_console)
    log_config_info(log_config=log_config, logger=logger)


# --- Primary commands --- #

@brokkr.utils.log.basic_logging
def print_status(pretty=True):
    logger = logging.getLogger(__name__)
    logger.debug("Getting oneshot status data...")
    import brokkr.monitoring.monitor
    if pretty:
        print(brokkr.monitoring.monitor.format_status_data())
    else:
        print(brokkr.monitoring.monitor.get_status_data())


def start_monitoring(verbose=None, quiet=None, **monitor_args):
    import brokkr.utils.log
    # Drop output_path arg if true to use default path in function signature
    if monitor_args.get("output_path_client", None) is True:
        monitor_args.pop("output_path_client", None)

    # Setup logging if not already configured
    if verbose is not None or quiet is not None:
        brokkr.utils.log.setup_basic_logging(
            verbose=verbose, quiet=quiet, script_mode=False)
    logger = logging.getLogger(__name__)

    # Print logging information
    logger.info("Monitor arguments: %s", monitor_args)

    # Start the mainloop
    import brokkr.monitoring.monitor
    brokkr.monitoring.monitor.start_monitoring(**monitor_args)


def start_brokkr(log_level_file=None, log_level_console=None):
    from brokkr.config.log import LOG_CONFIG
    from brokkr.config.main import CONFIG
    from brokkr.config.metadata import METADATA
    from brokkr.config.unit import UNIT_CONFIG
    import brokkr.utils.log
    import brokkr.multiprocess.handler
    import brokkr.monitoring.monitor

    # Setup logging config
    system_prefix = CONFIG["general"]["system_prefix"]
    if not system_prefix:
        system_prefix = METADATA["name"]
    output_path = Path(CONFIG["general"]["output_path_client"].as_posix()
                       .format(system_name=METADATA["name"]))

    log_config = brokkr.utils.log.render_full_log_config(
        LOG_CONFIG,
        log_level_file=log_level_file,
        log_level_console=log_level_console,
        output_path=output_path,
        system_name=METADATA["name"],
        system_prefix=system_prefix,
        unit_number=UNIT_CONFIG["number"],
        )

    # Create multiprocess handler and start logging process
    mp_handler = brokkr.multiprocess.handler.MultiprocessHandler(
        log_config=log_config,
        )
    mp_handler.start_logger()

    # Log startup messages
    logger = logging.getLogger(__name__)
    log_startup_messages(log_config=log_config, log_level_file=log_level_file,
                         log_level_console=log_level_console, logger=logger)

    # Setup worker configs for multiprocess handler
    worker_configs = [
        brokkr.multiprocess.handler.WorkerConfig(
            target=brokkr.monitoring.monitor.start_monitoring,
            name="MonitorProcess",
            )
        ]
    mp_handler.worker_configs = worker_configs
    mp_handler.worker_shutdown_wait_s = (
        CONFIG["general"]["worker_shutdown_wait_s"])

    # Start multiprocess manager mainloop
    logger.debug("Starting multiprocess manager mainloop: %r", mp_handler)
    mp_handler.run()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    start_brokkr()
