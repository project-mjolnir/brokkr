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
from brokkr.config.constants import LEVEL_NAME_SYSTEM, PACKAGE_NAME
import brokkr.logger


CONFIG_REQUIRE = ["system", "unit"]


# --- Startup helper functions --- #

def warn_on_startup_issues():
    from brokkr.config.systemhandler import CONFIG_HANDLER_SYSTEM
    from brokkr.config.system import SYSTEM_CONFIG
    from brokkr.config.handlers import (CONFIG_HANDLER_UNIT,
                                        CONFIG_HANDLER_METADATA)
    from brokkr.config.unit import UNIT_CONFIGS

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
        if not (CONFIG_HANDLER_METADATA.config_levels[LEVEL_NAME_SYSTEM]
                .path.exists()):
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


def log_config_info(log_config=None, logger=None):
    # pylint: disable=too-many-locals, useless-suppression
    from brokkr.config.bootstrap import BOOTSTRAP_CONFIG, BOOTSTRAP_CONFIGS
    from brokkr.config.dynamic import DYNAMIC_CONFIG, DYNAMIC_CONFIGS
    from brokkr.config.log import LOG_CONFIG, LOG_CONFIGS
    from brokkr.config.metadata import METADATA_CONFIG, METADATA_CONFIGS
    from brokkr.config.static import CONFIG, CONFIGS
    from brokkr.config.system import SYSTEM_CONFIG, SYSTEM_CONFIGS
    from brokkr.config.unit import UNIT_CONFIG, UNIT_CONFIGS

    if logger is None:
        logger = logging.getLogger(__name__)
    if log_config is None:
        log_config = LOG_CONFIG

    # Print config information
    for config_name, config_data in {
            "System path": (SYSTEM_CONFIG, SYSTEM_CONFIGS),
            "Metadata": (METADATA_CONFIG, METADATA_CONFIGS),
            "Bootstrap": (BOOTSTRAP_CONFIG, BOOTSTRAP_CONFIGS),
            "Unit": (UNIT_CONFIG, UNIT_CONFIGS),
            "Log": (log_config, LOG_CONFIGS),
            "Static": (CONFIG, CONFIGS),
            "Dynamic": (DYNAMIC_CONFIG, DYNAMIC_CONFIGS),
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

@brokkr.logger.basic_logging
def print_status(pretty=True):
    logger = logging.getLogger(__name__)
    logger.debug("Getting oneshot status data...")
    import brokkr.monitoring.monitor
    if pretty:
        print(brokkr.monitoring.monitor.format_status_data())
    else:
        print(brokkr.monitoring.monitor.get_status_data())


def start_monitoring(verbose=None, quiet=None, **monitor_args):
    import brokkr.logger
    # Drop output_path arg if true to use default path in function signature
    if monitor_args.get("output_path_client", None) is True:
        monitor_args.pop("output_path_client", None)

    # Setup logging if not already configured
    if verbose is not None or quiet is not None:
        brokkr.logger.setup_basic_logging(
            verbose=verbose, quiet=quiet, script_mode=False)
    logger = logging.getLogger(__name__)

    # Print logging information
    logger.info("Monitor arguments: %s", monitor_args)

    # Start the mainloop
    import brokkr.monitoring.monitor
    brokkr.monitoring.monitor.start_monitoring(**monitor_args)


def start_brokkr(
        log_level_file=None, log_level_console=None, **monitor_kwargs):
    from brokkr.config.bootstrap import BOOTSTRAP_CONFIG
    from brokkr.config.log import LOG_CONFIG
    from brokkr.config.metadata import METADATA_CONFIG
    from brokkr.config.unit import UNIT_CONFIG
    import brokkr.logger
    import brokkr.multiprocess.handler
    import brokkr.monitoring.monitor

    # Setup logging config
    log_config = brokkr.logger.render_full_log_config(
        LOG_CONFIG,
        log_level_file=log_level_file,
        log_level_console=log_level_console,
        output_path=BOOTSTRAP_CONFIG["output_path_client"],
        system_name=METADATA_CONFIG["name"],
        system_prefix=BOOTSTRAP_CONFIG["system_prefix"],
        unit_number=UNIT_CONFIG["number"],
        )

    # Setup worker configs
    worker_configs = [
        brokkr.multiprocess.handler.WorkerConfig(
            target=brokkr.monitoring.monitor.start_monitoring,
            name="MonitorProcess",
            process_kwargs=monitor_kwargs,
            )
        ]

    # Create multiprocess handler and start logging process
    mp_handler = brokkr.multiprocess.handler.MultiprocessHandler(
        worker_configs=worker_configs,
        worker_shutdown_wait_s=BOOTSTRAP_CONFIG["worker_shutdown_wait_s"],
        log_config=log_config,
        )
    mp_handler.start_logging()

    # Log startup messages
    logger = logging.getLogger(__name__)
    log_startup_messages(log_config=log_config, log_level_file=log_level_file,
                         log_level_console=log_level_console, logger=logger)

    # Start multiprocess manager mainloop
    logger.debug("Starting multiprocess manager mainloop: %r", mp_handler)
    mp_handler.run()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    start_brokkr()
