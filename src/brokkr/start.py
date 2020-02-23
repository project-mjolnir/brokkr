#!/usr/bin/env python3
"""
Startup code for running the Brokkr client mainloop as an application.
"""

# Standard library imports
import logging
import logging.config
from pathlib import Path

# Local imports
from brokkr.config.constants import PACKAGE_NAME, LEVEL_NAME_SYSTEM
import brokkr.logger


CONFIG_REQUIRE = ["system", "unit"]


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


def start_brokkr(log_level_file=None, log_level_console=None, **monitor_args):
    from brokkr.config.bootstrap import BOOTSTRAP_CONFIGS, BOOTSTRAP_CONFIG
    from brokkr.config.metadata import METADATA_CONFIGS, METADATA_CONFIG
    from brokkr.config.log import LOG_CONFIGS, LOG_CONFIG
    from brokkr.config.system import SYSTEM_CONFIGS, SYSTEM_CONFIG
    from brokkr.config.unit import UNIT_CONFIGS, UNIT_CONFIG
    import brokkr.logger

    # Setup logging
    log_config = brokkr.logger.setup_full_log_config(
        LOG_CONFIG,
        log_level_file=log_level_file,
        log_level_console=log_level_console,
        output_path=BOOTSTRAP_CONFIG["output_path_client"],
        system_name=METADATA_CONFIG["name"],
        system_prefix=BOOTSTRAP_CONFIG["system_prefix"],
        unit_number=UNIT_CONFIG["number"],
        )
    logger = logging.getLogger(__name__)

    # Print startup message and warn on some problem states
    logger.info("Starting %s...", generate_version_message())
    warn_on_startup_issues()

    # Print config information
    if any((log_level_file, log_level_console)):
        logger.info("Using manual log levels: %s (file), %s (console)",
                    log_level_file, log_level_console)
    for config_name, config_data in {
            "System path": (SYSTEM_CONFIG, SYSTEM_CONFIGS),
            "Metadata": (METADATA_CONFIG, METADATA_CONFIGS),
            "Bootstrap": (BOOTSTRAP_CONFIG, BOOTSTRAP_CONFIGS),
            "Unit": (UNIT_CONFIG, UNIT_CONFIGS),
            "Log": (log_config, LOG_CONFIGS),
            }.items():
        logger.info("%s config: %s", config_name, config_data[0])
        logger.debug("%s config hierarchy: %s", config_name, config_data[1])

    # Start monitoring system
    import brokkr.monitoring.monitor
    brokkr.monitoring.monitor.start_monitoring(**monitor_args)


if __name__ == "__main__":
    start_brokkr()
