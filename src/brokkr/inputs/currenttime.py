"""
Simple input that returns the current time.
"""

# Standard library imports
import datetime
import time

# Local imports
import brokkr.pipeline.datavalue
import brokkr.pipeline.step


class CurrentTimeInput(brokkr.pipeline.step.ValueInputStep):
    def __init__(
            self,
            data_name="time",
            full_name=None,
            use_local=False,
            **value_step_kwargs):
        if full_name is None:
            full_name = f"Time ({'Local' if use_local else 'UTC'})"
        time_data_type = brokkr.pipeline.datavalue.DataType(
            name=data_name,
            conversion="time_posix",
            binary_type="d",
            full_name=full_name,
            unit="s",
            uncertainty=time.get_clock_info("time").resolution,
            use_local=use_local,
            )
        super().__init__(data_types=[time_data_type], binary_decoder=False,
                         **value_step_kwargs)

    def read_raw_data(self, input_data=None):
        current_time = datetime.datetime.now(
            tz=datetime.timezone.utc).timestamp()
        raw_data = [current_time]
        return raw_data
