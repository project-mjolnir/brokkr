"""
Input and output queue steps for the pipeline archetecture.
"""

# Standard library imports
import queue

# Local imports
from brokkr.constants import SLEEP_TICK_S
import brokkr.pipeline.base
import brokkr.pipeline.utils


# Module-level constants
SHUTDOWN_TIMEOUT_DEFAULT_S = 3


class QueueInputStep(brokkr.pipeline.base.InputStep):
    def __init__(
            self,
            data_queue,
            queue_timeout_s=SLEEP_TICK_S,
            **pipeline_step_kwargs):
        super().__init__(**pipeline_step_kwargs)
        self.data_queue = data_queue
        self.queue_timeout_s = queue_timeout_s

    def safe_get(self, **get_kwargs):
        try:
            output_data = self.data_queue.get(**get_kwargs)
        except queue.Empty:
            output_data = None  # Do nothing if the queue is empty
        return output_data

    def execute(self, input_data=None):
        try:
            output_data = self.safe_get(
                block=True, timeout=self.queue_timeout_s)
        except InterruptedError:
            self.logger.info("Queue reading interrupted, retrying")
            self.logger.debug("Error details:", exc_info=True)
            output_data = self.safe_get(
                block=True, timeout=self.queue_timeout_s)
        return output_data


class QueueOutputStep(brokkr.pipeline.base.OutputStep):
    def __init__(
            self,
            data_queue,
            shutdown_timeout_s=SHUTDOWN_TIMEOUT_DEFAULT_S,
            **pipeline_step_kwargs):
        super().__init__(**pipeline_step_kwargs)
        self.data_queue = data_queue
        self.shutdown_timeout_s = shutdown_timeout_s

    def safe_put(self, input_data, **put_kwargs):
        try:
            try:
                self.data_queue.put(input_data, **put_kwargs)
            except InterruptedError:  # If interrupted, just try to put again
                self.logger.info("QUeue writing interrupted, retrying")
                self.data_queue.put(input_data, **put_kwargs)
            return True
        except queue.Full:
            try:
                queue_size = self.data_queue.qsize()
            # Ignore errors related to OSes or queues that don't support qsize
            except (NotImplementedError, AttributeError) as e:
                self.logger.debug("%s getting queue size: %s",
                                  type(e).__name__, e)
                queue_size = "unknown"
            self.logger.error(
                "The %s queue is full at size ~%s, dropping data",
                self.name, queue_size)
            self.logger.debug("Queue details: %s", self.data_queue.__dict__)
            return False

    def execute(self, input_data=None):
        try:
            self.safe_put(input_data=input_data, block=False)
        except InterruptedError:
            self.logger.info("Queue writing interrupted, retrying")
            self.logger.debug("Error details:", exc_info=True)
            self.safe_put(input_data=input_data, block=False)
        if self.exit_event.is_set():
            self.logger.info("Exit event set, putting shutdown sentinel "
                             "to queue on step %s (%s)",
                             self.name, type(self))
            self.safe_put(
                input_data=brokkr.pipeline.utils.ShutdownSentinel,
                timeout=self.shutdown_timeout_s)
        return input_data
