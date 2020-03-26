"""
Base classes for the Pipeline archtecture.
"""

# Standard library imports
import abc
import logging

# Local imports
import brokkr.utils.log
import brokkr.utils.misc


class Executable(brokkr.utils.misc.AutoReprMixin, metaclass=abc.ABCMeta):
    def __init__(self, name="Unnamed", input_data=None, exit_event=None):
        self.name = name
        self.input_data = input_data
        self.exit_event = exit_event
        self.logger = logging.getLogger(
            brokkr.utils.misc.get_full_class_name(self))
        self.log_helper = brokkr.utils.log.LogHelper(self.logger)

    @abc.abstractmethod
    def execute(self, input_data=None):
        if input_data is None:
            input_data = self.input_data
        return input_data


class SequentialMixin:
    def execute_step(self, idx, step, input_data=None):
        self.logger.debug(
            "Executing step %s of %s - %s (%s) in %s (%s)",
            idx + 1, len(self.steps), step.name,
            brokkr.utils.misc.get_full_class_name(step),
            self.name, brokkr.utils.misc.get_full_class_name(self))
        try:
            output_data = step.execute(input_data=input_data)
        except Exception as e:
            self.logger.critical(
                "%s caught at main level on step %s of %s - %s (%s) in "
                "%s (%s): %s",
                type(e).__name__, idx + 1, len(self.steps), step.name,
                brokkr.utils.misc.get_full_class_name(step),
                self.name, brokkr.utils.misc.get_full_class_name(self), e)
            self.logger.info("Error details:", exc_info=True)
            return None
        else:
            return output_data
