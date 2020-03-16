"""
Simple input that returns the length of time Brokkr has been running.
"""

# Local imports
import brokkr.pipeline.step
import brokkr.utils.misc


DEFAULT_PRECISION = 3


class RunTimeInput(brokkr.pipeline.step.InputStep):
    def __init__(
            self,
            precision=DEFAULT_PRECISION,
            **pipeline_step_kwargs):
        super().__init__(**pipeline_step_kwargs)
        self._precision = precision

    def execute(self, input_data=None):
        run_time = brokkr.utils.misc.start_time_offset(self._precision)
        output_data = {"runtime": run_time}
        return output_data
