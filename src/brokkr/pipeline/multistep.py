"""
Multi pipeline step classes for the pipeline archtecture.
"""

# Standard library imports
import abc

# Local imports
import brokkr.pipeline.base
import brokkr.pipeline.baseinput


class MultiStep(brokkr.pipeline.base.PipelineStep, metaclass=abc.ABCMeta):
    # pylint: disable=abstract-method
    def __init__(self, steps, **pipeline_step_kwargs):
        super().__init__(**pipeline_step_kwargs)
        self.steps = steps


class SequentialMultiStep(MultiStep, brokkr.pipeline.base.SequentialMixin):
    def execute(self, input_data=None):
        input_data = super().execute(input_data=input_data)
        output_data = []
        for idx, step in enumerate(self.steps):
            step_output = self.execute_step(
                idx, step, input_data=input_data)
            if step_output is None and isinstance(
                    step, brokkr.pipeline.baseinput.ValueInputStep):
                try:
                    step_output = step.decoder.output_na_values()
                except Exception as e:
                    self.logger.critical(
                        "%s outputing NA data for InputStep %s (%s): %s",
                        type(e).__name__, step.name,
                        brokkr.utils.misc.get_full_class_name(step), e)
                    self.logger.info("Error details:", exc_info=True)
                else:
                    self.logger.debug(
                        "Replaced output None for InputStep %s (%s) with %r",
                        step.name, brokkr.utils.misc.get_full_class_name(step),
                        step_output)

            if step_output is not None:
                output_data.append(step_output)

        output_data_flat = {}
        for inner_dict in output_data:
            output_data_flat.update(inner_dict)
        return output_data_flat
