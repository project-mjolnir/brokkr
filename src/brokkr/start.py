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
import sys

# Local imports
from brokkr.constants import (
    LEVEL_NAME_SYSTEM,
    PACKAGE_NAME,
    SYSTEM_SUBPATH_PLUGINS,
    )
import brokkr.utils.log


CONFIG_REQUIRE = ["systempath", "unit"]

DEFAULT_PIPELINE = {
    "_builder": "monitor",
    "name": "Default Pipeline",
    "monitor_input_steps": [
        "builtins.inputs.current_time", "builtins.inputs.run_time"],
    "monitor_output_steps": ["builtins.outputs.csv_file"],
    }


# --- Startup helper functions --- #

def warn_on_startup_issues(logger=None):
    import brokkr
    from brokkr.config.confighandlers import CONFIG_HANDLER_UNIT
    from brokkr.config.metadata import METADATA
    from brokkr.config.metadatahandler import CONFIG_HANDLER_METADATA
    from brokkr.config.systempath import SYSTEMPATH_CONFIG
    from brokkr.config.unit import UNIT_CONFIGS
    import brokkr.utils.misc

    if logger is None:
        logger = logging.getLogger(__name__)

    issues_found = False

    # Avoid users trying to start Brokkr without setting up the basic config
    try:
        system_path = brokkr.utils.misc.get_system_path(
            SYSTEMPATH_CONFIG, allow_default=False)
    except RuntimeError as e:
        logger.warning("%s getting system path: %s", type(e).__name__, e)
        logger.debug("Error details:", exc_info=True)
        issues_found = True
    except KeyError as e:
        logger.error("System path %s not found in %r",
                     e, SYSTEMPATH_CONFIG["system_paths"])
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

    # Check that the Brokkr version is compatible with the system
    issues_found = issues_found and brokkr.utils.misc.check_system_version(
        METADATA, logger.warning)

    return issues_found


def log_config_info(log_config=None, logger=None):
    # pylint: disable=too-many-locals, useless-suppression
    from brokkr.config.log import LOG_CONFIG, LOG_CONFIGS
    from brokkr.config.main import CONFIG, CONFIGS
    from brokkr.config.metadata import METADATA, METADATA_CONFIGS
    from brokkr.config.presets import PRESETS, PRESET_CONFIGS
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
            "Presets": (list(PRESETS.keys()), PRESET_CONFIGS),
            }.items():  # pylint: disable=bad-continuation
        if config_data[0] is not None:
            logger.info("%s config: %s", config_name, config_data[0])
        if config_data[1] is not None:
            logger.debug("%s hierarchy: %s", config_name, config_data[1])


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


def handle_startup_error(e, mp_handler, exit_event, logger, message=""):
    if message:
        message = " " + message
    if isinstance(e, SystemExit):
        logger.critical("Error caught%s, exiting", message)
        if exit_event:
            exit_event.set()
        if mp_handler is not None:
            mp_handler.shutdown_logger()
        sys.exit(e.code)
    if isinstance(e, Exception):
        logger.critical("%s%s: %s", type(e).__name__, message, e)
        logger.info("Error details:", exc_info=True)
        if exit_event is not None:
            exit_event.set()
        if mp_handler is not None:
            mp_handler.shutdown_logger()
        sys.exit(1)


def create_build_context(exit_event=None, mp_handler=None):
    from brokkr.config.main import CONFIG
    from brokkr.config.systempath import SYSTEMPATH_CONFIG
    import brokkr.pipeline.builder

    logger = logging.getLogger(__name__)

    # Import presets, and handle any errors doing so
    try:
        from brokkr.config.presets import PRESETS
    except BaseException as e:
        handle_startup_error(
            e, mp_handler, exit_event, logger, message="loading presets")
        raise

    build_context = brokkr.pipeline.builder.BuildContext(
        exit_event=exit_event,
        subobject_lookup=CONFIG["steps"],
        subobject_presets=PRESETS,
        plugin_root_path=(brokkr.utils.misc.get_system_path(SYSTEMPATH_CONFIG)
                          / SYSTEM_SUBPATH_PLUGINS),
        na_marker=CONFIG["general"]["na_marker"],
        preset_fill_mappings=[("data_types", CONFIG.get("data_types", {}))],
        )
    return build_context


def get_monitoring_pipeline(interval_s=1, exit_event=None, logger=None):
    from brokkr.config.main import CONFIG
    import brokkr.pipeline.builder

    if exit_event is None:
        exit_event = multiprocessing.Event()

    pipelines = CONFIG["pipelines"]
    if not pipelines:
        pipelines = {"default": DEFAULT_PIPELINE}

    pipeline_key = CONFIG["general"]["monitoring_pipeline_default"]
    if not pipeline_key:
        pipeline_key = list(pipelines.keys())[0]

    try:
        monitoring_pipeline_kwargs = pipelines[pipeline_key]
    except KeyError as e:
        if logger:
            logger.critical(
                "%s finding default monitoring pipeline %s",
                type(e).__name__, e)
            logger.info("Error details:", exc_info=True)
            logger.error("Valid pipelines: %r", list(pipelines.keys()))
            sys.exit(1)
        raise

    builder = brokkr.pipeline.builder.BUILDERS[
        monitoring_pipeline_kwargs.get("_builder", "")]
    if issubclass(builder, brokkr.pipeline.builder.MonitorBuilder):
        builder_kwargs = {
            "monitor_input_steps": monitoring_pipeline_kwargs[
                "monitor_input_steps"],
            "monitor_interval_s": interval_s,
            }
    else:
        monitoring_pipeline_kwargs.pop("_builder")
        builder_kwargs = monitoring_pipeline_kwargs
    builder_kwargs["na_on_start"] = False

    build_context = create_build_context(exit_event=exit_event)
    built_pipeline = builder(build_context=build_context,
                             **builder_kwargs).setup_and_build()

    return pipeline_key, built_pipeline


# --- Primary commands --- #

@brokkr.utils.log.basic_logging
def print_status():
    logger = logging.getLogger(__name__)
    logger.debug("Getting oneshot status data")
    warn_on_startup_issues()

    pipeline_name, monitoring_pipeline = get_monitoring_pipeline(logger=logger)
    logger.debug("Running monitoring pipeline %s", pipeline_name)

    monitoring_pipeline.execute()


@brokkr.utils.log.basic_logging
def start_monitoring(interval_s=1):
    logger = logging.getLogger(__name__)
    logger.debug("Printing monitoring data")
    warn_on_startup_issues()

    pipeline_name, monitoring_pipeline = get_monitoring_pipeline(
        interval_s=interval_s, logger=logger)
    logger.debug("Running monitoring pipeline %s", pipeline_name)

    monitoring_pipeline.execute_forever()


def start_brokkr(log_level_file=None, log_level_console=None):
    from brokkr.config.log import LOG_CONFIG
    from brokkr.config.main import CONFIG
    from brokkr.config.metadata import METADATA
    from brokkr.config.unit import UNIT_CONFIG
    import brokkr.multiprocess.handler
    import brokkr.pipeline.builder
    import brokkr.utils.log

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
    exit_event = multiprocessing.Event()
    mp_handler = brokkr.multiprocess.handler.MultiprocessHandler(
        log_config=log_config,
        exit_event=exit_event,
        )
    mp_handler.start_logger()

    # Log startup messages
    logger = logging.getLogger(__name__)

    try:
        log_startup_messages(
            log_config=log_config,
            log_level_file=log_level_file,
            log_level_console=log_level_console,
            logger=logger,
            )
    except BaseException as e:
        handle_startup_error(
            e, mp_handler, exit_event, logger,
            message="generating startup messages")
        raise

    # Import and set up system pipeline config
    pipelines = CONFIG["pipelines"]
    if not pipelines:
        logger.info("No pipelines defined; falling back to default")
        pipelines = {"default": DEFAULT_PIPELINE}

    logger.debug("Building pipelines")
    build_context = create_build_context(
        exit_event=exit_event, mp_handler=mp_handler)
    pipeline_builders = brokkr.pipeline.builder.TopLevelBuilder(
        pipelines, build_context=build_context)
    try:
        pipeline_builders.setup()
    except BaseException as e:
        handle_startup_error(
            e, mp_handler, exit_event, logger,
            message="building pipeline list")
        raise

    # Setup worker configs for multiprocess handler
    logger.debug("Setting up working configs")
    worker_configs = [
        brokkr.multiprocess.handler.WorkerConfig(
            executor=pipeline_builder,
            name=getattr(pipeline_builder, "name", "Unnamed") + " Process",
            build_method="setup_and_build",
            run_method="execute_forever",
            )
        for pipeline_builder in pipeline_builders.subbuilders
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
