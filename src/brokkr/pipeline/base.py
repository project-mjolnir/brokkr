"""
Base classes for the Pipeline archtecture.
"""

# Standard library imports
import abc
import logging
import time

# Local imports
import brokkr.pipeline.utils
import brokkr.utils.log
import brokkr.utils.misc


ERROR_TIMEOUT_S = 1


class Executable(brokkr.utils.misc.AutoReprMixin, metaclass=abc.ABCMeta):
    def __init__(
            self,
            name="Unnamed",
            input_data=None,
            exit_event=None,
            skip_na=False,
                ):
        self.name = name
        self.input_data = input_data
        self.exit_event = exit_event
        self.skip_na = skip_na

        self.logger = logging.getLogger(
            brokkr.utils.misc.get_full_class_name(self))
        self.log_helper = brokkr.utils.log.LogHelper(self.logger)

    @abc.abstractmethod
    def execute(self, input_data=None):
        pass

    def execute_(self, input_data=None):
        if input_data is None:
            input_data = self.input_data

        if self.skip_na and brokkr.pipeline.utils.is_all_na(input_data):
            self.logger.debug("Input data is None/NA, skipping output")
            return input_data

        output_data = self.execute(input_data=input_data)
        return output_data


# --- Common mixin classes --- #

class SequentialMixin:
    def execute_step(self, idx, step, input_data=None):
        self.logger.debug(
            "Executing step %s of %s - %s (%s) in %s (%s)",
            idx + 1, len(self.steps), getattr(step, "name", None),
            brokkr.utils.misc.get_full_class_name(step),
            self.name, brokkr.utils.misc.get_full_class_name(self))
        try:
            output_data = step.execute_(input_data=input_data)
        except Exception as e:
            self.logger.critical(
                "%s caught at main level on step %s of %s - %s (%s) in "
                "%s (%s): %s",
                type(e).__name__, idx + 1, len(self.steps),
                getattr(step, "name", None),
                brokkr.utils.misc.get_full_class_name(step),
                self.name, brokkr.utils.misc.get_full_class_name(self), e)
            self.logger.info("Error details:", exc_info=True)
            self.logger.debug("Pausing execution for %s s", ERROR_TIMEOUT_S)
            time.sleep(ERROR_TIMEOUT_S)
            return None
        else:
            return output_data


# --- Core PipelineStep classes --- #

class PipelineStep(Executable, metaclass=abc.ABCMeta):
    pass


class UnitStep(PipelineStep, metaclass=abc.ABCMeta):
    pass


class InputStep(PipelineStep, metaclass=abc.ABCMeta):
    pass


class TransformStep(PipelineStep, metaclass=abc.ABCMeta):
    pass


class OutputStep(PipelineStep, metaclass=abc.ABCMeta):
    pass
