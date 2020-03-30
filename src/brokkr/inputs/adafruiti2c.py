"""
Input steps for arbitrary Adafruit I2C devices.
"""

# Standard library imports
import importlib

# Third party imports
import board
import busio

# Local imports
import brokkr.pipeline.baseinput


class AdafruitI2CInput(brokkr.pipeline.baseinput.ValueInputStep):
    def __init__(
            self,
            adafruit_module,
            adafruit_class,
            **value_input_kwargs):
        super().__init__(binary_decoder=False, **value_input_kwargs)

        module_object = importlib.import_module(adafruit_module)
        self.obj_class = getattr(module_object, adafruit_class)

    def read_raw_data(self, input_data=None):
        try:
            i2c = busio.I2C(board.SCL, board.SDA)
            adafruit_obj = self.obj_class(i2c)
        except Exception as e:
            self.logger.error(
                "%s initializing Adafruit I2C device %s on step %s: %s",
                type(e).__name__, type(self.obj_class), self.name, e)
            self.logger.info("Error details:", exc_info=True)
            return None

        raw_data = []
        for data_type in self.data_types:
            try:
                data_value = getattr(
                    adafruit_obj, data_type.adafruit_property)
            except Exception as e:
                self.logger.error(
                    "%s getting attirbute %s from Adafruit I2C device %s "
                    "on step %s: %s",
                    type(e).__name__, data_type.adafruit_property,
                    type(self.obj_class), self.name, e)
                self.logger.info("Error details:", exc_info=True)
                data_value = None
            raw_data.append(data_value)

        return raw_data
