"""
Input steps for digital GPIO devices.
"""

# Standard library imports
import collections
import time

# Third party imports
import gpiozero

# Local imports
import brokkr.pipeline.baseinput
import brokkr.utils.misc


class GPIOCounterDevice(brokkr.utils.misc.AutoReprMixin):
    def __init__(self, pin, max_counts=None, gpio_kwargs=None):
        self._gpio_kwargs = {} if gpio_kwargs is None else gpio_kwargs
        self._gpio_kwargs["pin"] = pin

        self._count_times = collections.deque(maxlen=max_counts)
        self._gpio_device = gpiozero.DigitalInputDevice(**gpio_kwargs)
        self._gpio_device.when_activated = self._count

        self.start_time = time.monotonic()

    def _count(self):
        """Count one transition. Used as a callback."""
        self._count_times.append(time.monotonic())

    @property
    def time_elapsed_s(self):
        """The time elapsed, in s, since the start time was last reset."""
        return time.monotonic() - self.start_time

    def get_count(self, period_s=None, mean=False):
        if not period_s:
            count = len(self._count_times)
        else:
            # Tabulate the number of counts over a given period
            count = -1
            for count, count_time in enumerate(reversed(self._count_times)):
                if count_time < (time.monotonic() - period_s):
                    break
            else:
                count += 1

        if mean:
            count = count / max([min([self.time_elapsed_s, period_s]),
                                 time.get_clock_info("time").resolution])

        return count

    def reset(self):
        """
        Reset the count to zero and start time to the current time.

        Returns
        -------
        None.

        """
        self._count_times.clear()
        self.start_time = time.monotonic()


class GPIOCounterInput(brokkr.pipeline.baseinput.ValueInputStep):
    def __init__(
            self,
            pin,
            max_counts=None,
            gpio_kwargs=None,
            reset_after_read=False,
            **value_input_kwargs):
        super().__init__(**value_input_kwargs)
        self._counter_device = GPIOCounterDevice(
            pin=pin, max_counts=max_counts, gpio_kwargs=gpio_kwargs)
        self._reset_after_read = reset_after_read

    def read_raw_data(self, input_data=None):
        raw_data = [
            self._counter_device.get_count(
                period_s=getattr(data_type, "period_s", None),
                mean=getattr(data_type, "mean", False),
                ) for data_type in self.data_types]
        if self._reset_after_read:
            self._counter_device.reset()
        return raw_data
