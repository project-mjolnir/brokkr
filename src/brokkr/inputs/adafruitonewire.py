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

        super().__init__(sensor_kwargs=sensor_kwargs, **property_input_kwargs)
        self.sensor_object = self.init_sensor_object()

    def read_sensor_data(self, sensor_object=None):
        if sensor_object is None:
            sensor_object = self.sensor_object
        if sensor_object is None:
            self.sensor_object = self.init_sensor_object()

        sensor_data = super().read_sensor_data()
        return sensor_data
