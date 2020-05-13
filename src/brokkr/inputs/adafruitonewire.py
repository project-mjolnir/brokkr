"""
Input steps for Adafruit Onewire devices (e.g. DHT11, DHT22).
"""

# Local imports
import brokkr.pipeline.baseinput


class AdafruitOnewireInput(brokkr.pipeline.baseinput.PropertyInputStep):
    def __init__(self, pin, sensor_kwargs=None, **property_input_kwargs):
        if sensor_kwargs is None:
            sensor_kwargs = {}
        sensor_kwargs["pin"] = pin

        super().__init__(
            sensor_kwargs=sensor_kwargs,
            cache_sensor_object=True,
            **property_input_kwargs)
