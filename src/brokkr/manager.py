"""
Manager for Brokkr running in a multiprocess archetecture.
"""

# Standard library imports
import logging
import logging.handlers
import multiprocessing
import time

# Local imports
from brokkr.config.constants import LOG_RECORD_SENTINEL, SLEEP_TICK_S
from brokkr.config.static import CONFIG
import brokkr.logger
import brokkr.monitoring.monitor
import brokkr.utils.misc


LOGGING_SHUTDOWN_WAIT_S = 5

LOGGER = logging.getLogger(__name__)


class Manager(brokkr.utils.misc.AutoReprMixin):
    def __init__(
            self,
            log_queue,
            log_listener,
            log_filter_level=logging.DEBUG,
            exit_event=None,
            monitor_kwargs=None,
                ):
        self.log_queue = log_queue
        self.log_listener = log_listener
        if exit_event is None:
            self.exit_event = multiprocessing.Event()
        else:
            self.exit_event = exit_event
        monitor_kwargs = {} if monitor_kwargs is None else monitor_kwargs

        self.processes = []
        monitor_process = multiprocessing.Process(
            target=brokkr.monitoring.monitor.start_monitoring_process,
            name="MonitorProcess",
            kwargs={
                "log_configurator": brokkr.logger.setup_worker_config,
                "configurator_kwargs": {
                    "log_queue": self.log_queue,
                    "filter_level": log_filter_level,
                    },
                "exit_event": self.exit_event,
                "monitor_kwargs": monitor_kwargs,
                },
            )
        self.processes.append(monitor_process)

    def startup(self):
        LOGGER.debug("Starting up processes: %r", self.processes)
        for process in self.processes:
            LOGGER.info("Starting process %s...", process)
            process.start()
            LOGGER.info("Started process %s", process)

    def manage(self):  # pylint: disable=no-self-use
        time.sleep(SLEEP_TICK_S)

    def manage_loop(self):
        LOGGER.info("Starting manager")
        while not self.exit_event.is_set():
            brokkr.utils.misc.run_periodic(
                self.manage, period_s=0,
                exit_event=self.exit_event, logger=LOGGER)()
        LOGGER.info("Exiting manager")

    def shutdown_processes(
            self,
            shutdown_wait_s=CONFIG["multiprocess"]["shutdown_wait_s"]):
        LOGGER.info("Beginning process shutdown...")
        self.exit_event.set()
        shutdown_start_time = time.monotonic()

        # Join processies gracefully as they end, up to the timeout
        shutdown_wait_time = shutdown_start_time + shutdown_wait_s
        for process in self.processes:
            LOGGER.info("Attempting to shut down process %s...", process)
            join_timeout = max(0, shutdown_wait_time - time.monotonic())
            process.join(join_timeout)
            LOGGER.info("Process %s shut down", process)

        # Check process status and forcefully terminate any remaining
        n_terminated = 0
        n_failed = 0
        while self.processes:
            process = self.processes.pop()
            if process.is_alive():
                LOGGER.error("Forcefully terminating process %s", process)
                LOGGER.info("Process info %r", process)
                process.terminate()
                LOGGER.info("Terminated process %s", process)
                n_terminated += 1
            else:
                if process.exitcode:
                    LOGGER.error("Process %s failed with exitcode %s",
                                 process, process.exitcode)
                    LOGGER.info("Process info %r", process)
                    n_failed += 1
            LOGGER.debug("Process %s shut down successfully", process)
            try:
                process.close()
            except AttributeError:
                LOGGER.debug("Could not call close on process %s; "
                             "presumably running on Python <3.7", process)
            except ValueError:
                LOGGER.error("Process %s still open after shutdown, "
                             "sending kill signal", process)
                LOGGER.info("Process info %r", process)
                process.kill()
                try:
                    process.close()
                except ValueError:
                    LOGGER.error("Process %s still not dead after kill",
                                 process)
                else:
                    LOGGER.info("Process %s killed", process)
        self.exit_event.clear()
        LOGGER.info(
            "Process shutdown finished in %s s with %s terminated, %s failed",
            time.monotonic() - shutdown_start_time, n_terminated, n_failed)
        return n_terminated, n_failed

    def shutdown_logging(self, logging_wait_s=LOGGING_SHUTDOWN_WAIT_S):
        LOGGER.info("Shutting down logging process")
        self.log_queue.put_nowait(LOG_RECORD_SENTINEL)
        logging.shutdown()
        self.log_listener.join(logging_wait_s)
        if self.log_listener.is_alive():
            self.log_listener.terminate()
        try:
            self.log_listener.close()
        except AttributeError:
            pass  # Not availible on <= Python 3.6
        except ValueError:  # If process is still open for some reason
            self.log_listener.kill()
            try:
                self.log_listener.close()
            except ValueError:
                pass  # Give up if the log process still isn't closed

    def shutdown(self):
        self.shutdown_processes()
        self.shutdown_logging()

    def main(self):
        self.startup()
        self.manage_loop()
        self.shutdown()
