"""
Simple input that returns the current time.
"""

# Standard library imports
import datetime

# Local imports
import brokkr.pipeline.step


class CurrentTimeInput(brokkr.pipeline.step.InputStep):
    def __init__(
            self,
            time_zone="utc",
            use_local=False,
            **pipeline_step_kwargs):
        super().__init__(**pipeline_step_kwargs)
        if use_local:
            self._time_zone = None
        else:
            self._time_zone = getattr(datetime.timezone, time_zone)

    def execute(self, input_data=None):
        current_time = datetime.datetime.now(tz=self._time_zone)
        output_data = {"time": current_time}
        return output_data
