"""
Core classes for the Pipeline-level components of the Pipeline archetecture.
"""

# Standard library imports
import abc
import multiprocessing

# Local imports
import brokkr.pipeline.base
import brokkr.pipeline.utils
import brokkr.utils.misc


# --- Core Pipeline classes --- #

class Pipeline(brokkr.pipeline.base.Executable, metaclass=abc.ABCMeta):
    def __init__(
            self,
            steps,
            period_s=0,
            na_on_start=False,
            wait_on_exit=False,
            **executable_kwargs):
        super().__init__(**executable_kwargs)
        self.steps = steps
        self.period_s = period_s
        self.na_on_start = na_on_start
        self.wait_on_exit = wait_on_exit

        self.outer_exit_event = multiprocessing.Event()

    def shutdown(self):
        self.logger.info(
            "Shutting down %s (%s)", self.name,
            brokkr.utils.misc.get_full_class_name(self))
        self.outer_exit_event.set()

    @abc.abstractmethod
    def execute(self, input_data=None):
        self.logger.debug(
            "Executing %s (%s)", self.name,
            brokkr.utils.misc.get_full_class_name(self))
        if self.exit_event and self.exit_event.is_set():
            if not self.wait_on_exit:
                self.logger.info("Exit event is set in pipeline %s",
                                 self.name)
                self.shutdown()
                return None
            self.logger.debug("Exit event set in pipeline %s, "
                              "awaiting shutdown sentinel", self.name)
        return input_data

    def execute_forever(self, input_data=None, exit_event=None):
        if exit_event is not None:
            self.exit_event = exit_event
        self.logger.info(
            "Beginning execution of %s (%s)", self.name,
            brokkr.utils.misc.get_full_class_name(self))
        if self.na_on_start:
            self.logger.debug("Injecting NA values on start")
            self.execute_(input_data=brokkr.pipeline.utils.NASentinel)
        brokkr.utils.misc.run_periodic(
            type(self).execute_,
            period_s=self.period_s,
            exit_event=self.exit_event,
            outer_exit_event=self.outer_exit_event,
            logger=self.logger,
            )(self, input_data=input_data)


class SequentialPipeline(Pipeline, brokkr.pipeline.base.SequentialMixin):
    def execute(self, input_data=None):
        data = super().execute(input_data=input_data)
        for idx, step in enumerate(self.steps):
            data = self.execute_step(idx, step, input_data=data)
            if data is brokkr.pipeline.utils.ShutdownSentinel:
                self.logger.info(
                    "Recieved shutdown sentinel from step %s - %s"
                    "in pipeline %s", idx + 1, step.name, self.name)
                self.shutdown()
                break
            if data is None:
                self.logger.debug(
                    "Data is none on step %s - %s in pipeline %s, restarting",
                    idx + 1, getattr(step, "name", None), self.name)
                break
        return data
