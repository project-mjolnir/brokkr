"""
Input steps for Adafruit digital I2C devices (e.g. SHT31, HTU21, BMP280, etc).
"""

# Standard library imports
import importlib

# Third party imports
import board
import busio

# Local imports
import brokkr.pipeline.baseinput


DEFAULT_ADC_CHANNEL = 0
DEFAULT_ADC_MODULE = "adafruit_ads1x15.ads1115"
DEFAULT_ADC_CLASS = "ADS1115"
DEFAULT_ANALOG_MODULE = "adafruit_ads1x15.analog_in"
DEFAULT_ANALOG_CLASS = "AnalogIn"


class AdafruitADCInput(brokkr.pipeline.baseinput.PropertyInputStep):
    def __init__(
            self,
            sensor_module,
            sensor_class,
            adc_channel=None,
            adc_kwargs=None,
            analog_module=DEFAULT_ANALOG_MODULE,
            analog_class=DEFAULT_ANALOG_CLASS,
            i2c_kwargs=None,
            **property_input_kwargs):
        super().__init__(
            sensor_module=sensor_module,
            sensor_class=sensor_class,
            cache_sensor_object=False,
            **property_input_kwargs)
        self._i2c_kwargs = {} if i2c_kwargs is None else i2c_kwargs
        self._adc_kwargs = {} if adc_kwargs is None else adc_kwargs

        analog_object = importlib.import_module(analog_module)
        self._analog_class = getattr(analog_object, analog_class)

        if (adc_channel is None
                and self._adc_kwargs.get("positive_pin", None) is None):
            adc_channel = DEFAULT_ADC_CHANNEL
        if adc_channel is not None:
            self._adc_kwargs["positive_pin"] = adc_channel

    def read_sensor_data(self, sensor_object=None):
        with busio.I2C(board.SCL, board.SDA, **self._i2c_kwargs) as i2c:
            sensor_object = self.init_sensor_object(i2c)
            if sensor_object is None:
                return None
            channel_object = self._analog_class(
                sensor_object, **self._adc_kwargs)
            raw_data = super().read_sensor_data(
                sensor_object=channel_object)
        return raw_data
