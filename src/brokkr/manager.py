"""
Manager for Brokkr running in a multiprocess archetecture.
"""

# Standard library imports
import logging
import logging.config
import logging.handlers
import multiprocessing
import queue
import threading
import time

# Local imports
from brokkr.config.constants import SLEEP_TICK_S
import brokkr.utils.misc


# Startup and shutdown delays for logging
LOGGING_STARTUP_WAIT_S = 1
LOGGING_SHUTDOWN_WAIT_S = 5
WORKER_SHUTDOWN_WAIT_S = 10

# Value to use to shut down the logging system
LOG_RECORD_SENTINEL = None


# --- General helper functions --- #

def start_worker_process(
        target,
        name="unnamed",
        log_configurator=None,
        configurator_kwargs=None,
        exit_event=None,
        process_args=None,
        process_kwargs=None,
        ):
    if process_args is None:
        process_args = ()
    if process_kwargs is None:
        process_kwargs = {}

    if log_configurator is not None:
        if configurator_kwargs is None:
            configurator_kwargs = {}
        log_configurator(**configurator_kwargs)

    logger = logging.getLogger(__name__)
    logger.info("Started worker process %s", name)
    target(*process_args, exit_event=exit_event, **process_kwargs)


# --- Logging setup and handling functions --- #

def setup_worker_log_config(log_queue, filter_level=None):
    if filter_level is None:
        filter_level = logging.DEBUG
    root_logger = logging.getLogger()
    root_logger.addHandler(logging.handlers.QueueHandler(log_queue))
    root_logger.setLevel(filter_level)


def setup_listener_log_config(log_config=None):
    logging.Formatter.converter = time.gmtime
    if log_config is None:
        logging.basicConfig()
    else:
        logging.config.dictConfig(log_config)


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
        log_queue.close()
        log_queue.join_thread()
    except Exception as e:  # Log and pass errors flushing the logging queue
        logger.error("%s cleaning up log queue: %s",
                     type(e).__name__, e)
        logger.info("Error info:", exc_info=True)

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
        if log_record is LOG_RECORD_SENTINEL:
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
            logger.info("Error info:", exc_info=True)
            logger.info("Log record info: %r", log_record)
        return log_record

    return log_record


def run_log_listener(log_queue, log_configurator,
                     configurator_kwargs=None, exit_event=None):
    if configurator_kwargs is None:
        configurator_kwargs = {}
    log_configurator(**configurator_kwargs)
    logger = logging.getLogger(__name__)
    logger.info("Starting logging system")
    outer_exit_event = threading.Event()

    brokkr.utils.misc.run_periodic(
        handle_queued_log_record, period_s=0, exit_event=exit_event,
        outer_exit_event=outer_exit_event, logger=False)(
            log_queue, outer_exit_event=outer_exit_event)


# --- Helper classes --- #

class WorkerConfig(brokkr.utils.misc.AutoReprMixin):
    def __init__(
            self, target, name=None, process_args=None, process_kwargs=None):
        self.target = target
        self.name = name
        self.process_args = process_args
        self.process_kwargs = process_kwargs


# --- Core manager class --- #

class Manager(brokkr.utils.misc.AutoReprMixin):
    def __init__(
            self,
            worker_configs=None,
            worker_shutdown_wait_s=WORKER_SHUTDOWN_WAIT_S,
            log_config=None,
            logging_startup_wait_s=LOGGING_STARTUP_WAIT_S,
            logging_shutdown_wait_s=LOGGING_SHUTDOWN_WAIT_S,
            exit_event=None,
                ):
        if worker_configs is None:
            worker_configs = []
        self.worker_configs = worker_configs
        self.worker_shutdown_wait_s = worker_shutdown_wait_s
        self.workers = None

        self.log_config = {} if log_config is None else log_config
        self.log_filter_level = log_config.get("root", {}).get("level", None)
        self.log_process = None
        self.log_queue = None
        self.logging_startup_wait_s = logging_startup_wait_s
        self.logging_shutdown_wait_s = logging_shutdown_wait_s
        self.logger = None

        if exit_event is None:
            exit_event = multiprocessing.Event()
        self.exit_event = exit_event

    def start_logging(self, ignore_started=False):
        # If logging already started, don't start another
        if self.logger is not None or self.log_process is not None:
            if ignore_started:
                self.logger.debug("Logging already started, not restarting")
                self.logger.debug("Log process info: %r", self.log_process)
                self.logger.debug("Logger info: %r", self.logger)
                return
            raise RuntimeError("Logging is already started")

        # Setup logging process
        self.log_queue = multiprocessing.Queue()
        self.log_process = multiprocessing.Process(
            target=run_log_listener,
            name="LogProcess",
            kwargs={
                "log_queue": self.log_queue,
                "log_configurator": setup_listener_log_config,
                "configurator_kwargs": {"log_config": self.log_config},
                "exit_event": self.exit_event,
                },
            )

        # Start logging process
        self.log_process.start()
        time.sleep(self.logging_startup_wait_s)  # Ensure logger is ready

        # Setup logging for manager thread
        setup_worker_log_config(
            self.log_queue, filter_level=self.log_filter_level)
        self.logger = logging.getLogger(__name__)
        self.logger.info("Set up logging for manager thread")

    def start_workers(self, ignore_started=False):
        # Check for processes already started
        if self.workers is not None:
            if ignore_started:
                self.logger.debug("Workers already started, not restarting")
                self.logger.debug("Process info: %r", self.workers)
                return
            raise RuntimeError("Workers are already started")

        # Setup processes
        self.workers = []
        for worker_config in self.worker_configs:
            worker = multiprocessing.Process(
                target=start_worker_process,
                name=worker_config.name,
                kwargs={
                    "target": worker_config.target,
                    "name": worker_config.name,
                    "log_configurator": setup_worker_log_config,
                    "configurator_kwargs": {
                        "log_queue": self.log_queue,
                        "filter_level": self.log_filter_level,
                        },
                    "exit_event": self.exit_event,
                    "process_args": worker_config.process_args,
                    "process_kwargs": worker_config.process_kwargs,
                    },
                )
            self.workers.append(worker)

        # Start processes
        self.logger.debug("Starting up processes: %r", self.workers)
        for worker in self.workers:
            self.logger.info("Starting worker process %s...", worker)
            worker.start()
            self.logger.info("Finished starting worker process %s", worker)

    def start(self, ignore_started=False):
        self.start_logging(ignore_started=ignore_started)
        self.start_workers(ignore_started=ignore_started)

    def manage(self):  # pylint: disable=no-self-use
        time.sleep(SLEEP_TICK_S)

    def manage_loop(self):
        self.logger.info("Starting manager")
        while not self.exit_event.is_set():
            brokkr.utils.misc.run_periodic(
                self.manage, period_s=0,
                exit_event=self.exit_event, logger=self.logger)()
        self.logger.info("Exiting manager")

    def shutdown_workers(self):
        self.logger.info("Beginning worker shutdown...")
        self.exit_event.set()
        shutdown_start_time = time.monotonic()

        # Join workers gracefully as they end, up to the timeout
        shutdown_wait_time = shutdown_start_time + self.worker_shutdown_wait_s
        for worker in self.workers:
            self.logger.info("Attempting to shut down worker %s...", worker)
            join_timeout = max(0, shutdown_wait_time - time.monotonic())
            worker.join(join_timeout)
            self.logger.info("Process %s shut down", worker)

        # Check worker status and forcefully terminate any remaining
        n_terminated = 0
        n_failed = 0
        while self.workers:
            worker = self.workers.pop()
            if worker.is_alive():
                self.logger.error("Forcefully terminating worker %s", worker)
                self.logger.info("Process info %r", worker)
                worker.terminate()
                self.logger.info("Terminated worker %s", worker)
                n_terminated += 1
            else:
                if worker.exitcode:
                    self.logger.error("Worker %s failed with exitcode %s",
                                      worker, worker.exitcode)
                    self.logger.info("Process info %r", worker)
                    n_failed += 1
            self.logger.debug("Worker %s shut down successfully", worker)
            try:
                worker.close()
            except AttributeError:
                self.logger.debug("Could not call close on worker %s; "
                                  "presumably running on Python <3.7", worker)
            except ValueError:
                self.logger.error("Worker %s still open after shutdown, "
                                  "sending kill signal", worker)
                self.logger.info("Process info %r", worker)
                worker.kill()
                try:
                    worker.close()
                except ValueError:
                    self.logger.error("Worker %s still not dead after kill",
                                      worker)
                else:
                    self.logger.info("Worker %s killed", worker)

        self.exit_event.clear()
        self.workers = None
        self.logger.info(
            "Worker shutdown finished in %s s with %s terminated, %s failed",
            time.monotonic() - shutdown_start_time, n_terminated, n_failed)
        return n_terminated, n_failed

    def shutdown_logging(self):
        self.logger.info("Shutting down logging process")
        self.logger = None
        self.log_queue.put_nowait(LOG_RECORD_SENTINEL)
        self.log_queue = None
        logging.shutdown()

        self.log_process.join(self.logging_shutdown_wait_s)
        if self.log_process.is_alive():
            self.log_process.terminate()
        try:
            self.log_process.close()
        except AttributeError:
            pass  # Not availible on <= Python 3.6
        except ValueError:  # If process is still open for some reason
            self.log_process.kill()
            try:
                self.log_process.close()
            except ValueError:
                pass  # Give up if the log process still isn't closed
        self.log_process = None

    def shutdown(self):
        self.shutdown_workers()
        self.shutdown_logging()

    def main(self):
        self.start(ignore_started=True)
        self.manage_loop()
        self.shutdown()
