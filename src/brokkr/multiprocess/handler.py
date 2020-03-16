"""
Process handling for a real-time system in a multiprocess environment.
"""

# Standard library imports
import logging
import multiprocessing
import time

# Local imports
from brokkr.constants import SLEEP_TICK_S
import brokkr.multiprocess.loglistener
import brokkr.utils.misc


# Startup and shutdown delays for processes
LOGGING_STARTUP_WAIT_S = 1
LOGGING_SHUTDOWN_WAIT_S = 5
WORKER_SHUTDOWN_WAIT_S = 10


# --- General helper functions --- #

def start_worker_process(
        worker_config,
        log_configurator=None,
        configurator_kwargs=None,
        exit_event=None,
        ):
    if log_configurator is not None:
        if configurator_kwargs is None:
            configurator_kwargs = {}
        log_configurator(**configurator_kwargs)

    logger = logging.getLogger(__name__)
    logger.info("Started worker process %s", worker_config.name)
    if worker_config.call_methods:
        executor = worker_config.executor
        for method_tocall in worker_config.call_methods:
            executor_new = getattr(executor, method_tocall)(
                *worker_config.process_args,
                exit_event=exit_event,
                **worker_config.process_kwargs,
                )
            if executor_new:
                executor = executor_new
    else:
        worker_config.executor(
            *worker_config.process_args,
            exit_event=exit_event,
            **worker_config.process_kwargs,
            )


# --- Helper classes --- #

class WorkerConfig(brokkr.utils.misc.AutoReprMixin):
    def __init__(
            self,
            executor,
            name=None,
            process_args=None,
            process_kwargs=None,
            call_methods=None,
                ):
        self.executor = executor
        self.name = name
        self.process_args = () if process_args is None else process_args
        self.process_kwargs = {} if process_kwargs is None else process_kwargs
        self.call_methods = call_methods


# --- Core process handler class --- #

class MultiprocessHandler(brokkr.utils.misc.AutoReprMixin):
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

    def start_logger(self, ignore_started=False):
        # If logging already started, don't start another
        if self.logger is not None or self.log_process is not None:
            if ignore_started:
                self.logger.debug("Logging already started, not restarting")
                self.logger.debug("Log process details: %r", self.log_process)
                self.logger.debug("Logger details: %r", self.logger)
                return
            raise RuntimeError("Logging is already started")

        # Setup logging process
        self.log_queue = multiprocessing.Queue()
        self.log_process = multiprocessing.Process(
            target=brokkr.multiprocess.loglistener.run_log_listener,
            name="LogProcess",
            kwargs={
                "log_queue": self.log_queue,
                "log_configurator":
                    brokkr.multiprocess.loglistener.setup_listener_logger,
                "configurator_kwargs": {"log_config": self.log_config},
                "exit_event": self.exit_event,
                },
            )

        # Start logging process
        self.log_process.start()
        time.sleep(self.logging_startup_wait_s)  # Ensure logger is ready

        # Setup logging for main thread
        brokkr.multiprocess.loglistener.setup_worker_logger(
            self.log_queue, filter_level=self.log_filter_level)
        self.logger = logging.getLogger(__name__)
        self.logger.info("Set up logging for main thread")

    def start_workers(self, ignore_started=False):
        # Check for processes already started
        if self.workers is not None:
            if ignore_started:
                self.logger.debug("Workers already started, not restarting")
                self.logger.debug("Process details: %r", self.workers)
                return
            raise RuntimeError("Workers are already started")

        # Setup processes
        self.workers = []
        for worker_config in self.worker_configs:
            worker = multiprocessing.Process(
                target=start_worker_process,
                name=worker_config.name,
                kwargs={
                    "worker_config": worker_config,
                    "log_configurator":
                        brokkr.multiprocess.loglistener.setup_worker_logger,
                    "configurator_kwargs": {
                        "log_queue": self.log_queue,
                        "filter_level": self.log_filter_level,
                        },
                    "exit_event": self.exit_event,
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
        self.start_logger(ignore_started=ignore_started)
        self.start_workers(ignore_started=ignore_started)

    def manage(self):  # pylint: disable=no-self-use
        time.sleep(SLEEP_TICK_S)

    def manage_loop(self):
        self.logger.info("Starting manager")
        while not self.exit_event.is_set():
            brokkr.utils.misc.run_periodic(
                self.manage, exit_event=self.exit_event, logger=self.logger)()
        self.logger.info("Exiting manager")

    def shutdown_workers(self):
        self.logger.info("Beginning worker shutdown...")
        shutdown_start_time = time.monotonic()
        self.exit_event.set()

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

        # Final cleanup
        self.exit_event.clear()
        self.workers = None
        self.logger.info(
            "Worker shutdown finished in %s ms with %s terminated, %s failed",
            round((time.monotonic() - shutdown_start_time) * int(1e3), 1),
            n_terminated, n_failed)
        return n_terminated, n_failed

    def shutdown_logger(self):
        # Shut down local logging
        self.logger.info("Shutting down logging process")
        self.logger = None
        logging.shutdown()

        # Command logger and queue to shut down
        self.log_queue.put_nowait(
            brokkr.multiprocess.loglistener.LOG_RECORD_SENTINEL)
        self.log_queue.close()
        self.log_queue.join_thread()
        self.log_queue = None

        # Ensure logger process actually terminates
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
        self.shutdown_logger()

    def run(self):
        self.start(ignore_started=True)
        self.manage_loop()
        self.shutdown()
