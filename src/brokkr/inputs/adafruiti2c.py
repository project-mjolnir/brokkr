"""
Input steps for Adafruit digital I2C devices (e.g. SHT31, HTU21, BMP280, etc).
"""

# Third party imports
import board
import busio

# Local imports
import brokkr.pipeline.baseinput


class BaseAdafruitI2CInput(brokkr.pipeline.baseinput.PropertyInputStep):
    def __init__(
            self,
            i2c_kwargs=None,
            **property_input_kwargs):
        super().__init__(**property_input_kwargs)
        self._i2c_kwargs = {} if i2c_kwargs is None else i2c_kwargs


class AdafruitI2CInput(BaseAdafruitI2CInput):
    def read_sensor_data(self, sensor_object=None):
        with busio.I2C(board.SCL, board.SDA, **self._i2c_kwargs) as i2c:
            sensor_object = self.init_sensor_object(i2c)
            if not sensor_object:
                return None
            raw_data = super().read_sensor_data(sensor_object=sensor_object)
        return raw_data


class AdafruitPersistantI2CInput(BaseAdafruitI2CInput):
    def __init__(self, **adafruit_i2c_kwargs):
        super().__init__(**adafruit_i2c_kwargs)
        self.sensor_object = self.init_sensor_object()

    def init_sensor_object(self, *sensor_args, **sensor_kwargs):
        i2c = busio.I2C(board.SCL, board.SDA, **self._i2c_kwargs)
        sensor_object = super().init_sensor_object(
            i2c, *sensor_args, **sensor_kwargs)
        self.sensor_object = sensor_object
        return sensor_object
