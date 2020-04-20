"""
Input steps for Adafruit digital I2C devices (e.g. SHT31, HTU21, BMP280, etc).
"""

# Third party imports
import board
import busio

# Local imports
import brokkr.pipeline.baseinput


class AdafruitI2CInput(brokkr.pipeline.baseinput.PropertyInputStep):
    def __init__(
            self,
            i2c_kwargs=None,
            **property_input_kwargs):
        super().__init__(**property_input_kwargs)
        self._i2c_kwargs = {} if i2c_kwargs is None else i2c_kwargs

    def read_properties(self, sensor_object=None):
        with busio.I2C(board.SCL, board.SDA, **self._i2c_kwargs) as i2c:
            sensor_object = self.object_class(
                i2c_bus=i2c, **self.sensor_kwargs)
            raw_data = super().read_properties(sensor_object=sensor_object)
        return raw_data
