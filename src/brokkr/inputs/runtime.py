"""
Simple input that returns the length of time Brokkr has been running.
"""

# Standard library imports
import time

# Local imports
import brokkr.pipeline.datavalue
import brokkr.pipeline.baseinput
import brokkr.utils.misc


DEFAULT_PRECISION = 3


class RunTimeInput(brokkr.pipeline.baseinput.ValueInputStep):
    def __init__(
            self,
            data_name="runtime",
            full_name="Runtime",
            precision=DEFAULT_PRECISION,
            **value_input_kwargs):
        runtime_data_type = brokkr.pipeline.datavalue.DataType(
            name=data_name,
            binary_type="d",
            full_name=full_name,
            unit="s",
            uncertainty=max(time.get_clock_info("monotonic").resolution,
                            1 / (10 ** precision))
            )
        super().__init__(data_types=[runtime_data_type], binary_decoder=False,
                         **value_input_kwargs)

        self._precision = precision

    def read_raw_data(self, input_data=None):
        run_time = brokkr.utils.misc.start_time_offset(self._precision)
        raw_data = [run_time]
        return raw_data
