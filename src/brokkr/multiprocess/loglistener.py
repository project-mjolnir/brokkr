"""
Log handling for a real-time system in a multiprocess environment.
"""

# Standard library imports
import logging
import logging.config
import logging.handlers
import multiprocessing
import queue
import time

# Local imports
from brokkr.constants import SLEEP_TICK_S
import brokkr.utils.misc


# Value to use to shut down the logging system
LOG_RECORD_SENTINEL = None


# --- Logging setup functions --- #

def setup_worker_logger(log_queue, filter_level=None):
    if filter_level is None:
        filter_level = logging.DEBUG
    root_logger = logging.getLogger()
    root_logger.handlers = []
    root_logger.addHandler(logging.handlers.QueueHandler(log_queue))
    root_logger.setLevel(filter_level)


def setup_listener_logger(log_config=None):
    logging.Formatter.converter = time.gmtime
    if log_config is None:
        logging.basicConfig()
    else:
        logging.config.dictConfig(log_config)


# --- Log listener functions --- #

def shutdown_log_listener(log_queue):
    logger = logging.getLogger(__name__)
    logger.info("Shutting down logging system")

    try:
        while True:
            try:
                log_record = log_queue.get(block=False)
                logger.warning(
                    "Record found in log queue past shutdown: %r",
                    log_record)
            except queue.Empty:
                break  # Break once queue is empty
    except Exception as e:  # Log and pass errors flushing the logging queue
        logger.error("%s cleaning up log queue: %s",
                     type(e).__name__, e)
        logger.info("Error details:", exc_info=True)

    logger.info("Logging system shut down")
    logging.shutdown()


def handle_queued_log_record(log_queue, outer_exit_event=None):
    logger = logging.getLogger(__name__)
    log_record = None

    try:
        log_record = log_queue.get(block=True, timeout=SLEEP_TICK_S)
    except (queue.Empty, InterruptedError):
        pass  # If the queue is empty or interrupted, just try again
    except Exception as e:  # If an error occurs, log and move on
        logger.error("%s getting from queue %s: %s",
                     type(e).__name__, log_queue, e)
        logger.info("Error details:", exc_info=True)
    else:
        if log_record == LOG_RECORD_SENTINEL:
            if outer_exit_event is not None:
                outer_exit_event.set()

            shutdown_log_listener(log_queue=log_queue)

            if outer_exit_event is None:
                raise StopIteration
            return None

        try:
            record_logger = logging.getLogger(log_record.name)
            record_logger.handle(log_record)
        except Exception as e:  # If an error occurs logging, log and move on
            logger.warning("%s logging record %s: %s",
                           type(e).__name__, log_record, e)
            logger.info("Error details:", exc_info=True)
            logger.info("Log record details: %r", log_record)
        return log_record

    return log_record


def run_log_listener(log_queue, log_configurator,
                     configurator_kwargs=None, exit_event=None):
    if configurator_kwargs is None:
        configurator_kwargs = {}
    log_configurator(**configurator_kwargs)
    logger = logging.getLogger(__name__)
    logger.info("Starting logging system")
    outer_exit_event = multiprocessing.Event()

    brokkr.utils.misc.run_periodic(
        handle_queued_log_record, exit_event=exit_event,
        outer_exit_event=outer_exit_event, logger=False)(
            log_queue, outer_exit_event=outer_exit_event)
