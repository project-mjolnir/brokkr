"""
Generalized input class for an I2C/SMBus device using the SMBus library.
"""

# Standard library imports
import logging
from pathlib import Path

# Third party imports
import smbus2

# Local imports
import brokkr.pipeline.baseinput
import brokkr.utils.misc


MAX_I2C_BUS_N = 6

I2C_BLOCK_READ_FUNCTION = "read_i2c_block_data"
DEFAULT_READ_FUNCTION = I2C_BLOCK_READ_FUNCTION

LOGGER = logging.getLogger(__name__)


class SMBusI2CDevice(brokkr.utils.misc.AutoReprMixin):
    def __init__(self, bus=None, force=None):
        self.force = force

        # Automatically try to find first I2C bus and use that
        if bus is None:
            for n_bus in range(0, MAX_I2C_BUS_N + 1):
                if Path(f"/dev/i2c-{n_bus}").exists():
                    bus = n_bus
                    LOGGER.debug("Found I2C device at bus %s", bus)
                    break
            else:
                raise RuntimeError("Could not find I2C any bus device")

        self.bus = bus

    def read(self, force=None,
             read_function=DEFAULT_READ_FUNCTION, **read_kwargs):
        if force is None:
            force = self.force
        LOGGER.debug("Reading I2C data with function %s at bus %r, kwargs %r",
                     read_function, self.bus, read_kwargs)
        with smbus2.SMBus(self.bus, force=self.force) as i2c_bus:
            buffer = getattr(i2c_bus, read_function)(
                force=force, **read_kwargs)
        LOGGER.debug("Read I2C data %r", buffer)
        return buffer


class SMBusI2CInput(brokkr.pipeline.baseinput.SensorInputStep):
    def __init__(
            self,
            bus=None,
            read_function=DEFAULT_READ_FUNCTION,
            init_kwargs=None,
            read_kwargs=None,
            include_all_data_each=True,
            **sensor_input_kwargs):
        init_kwargs = {} if init_kwargs is None else init_kwargs
        self._read_kwargs = {} if read_kwargs is None else read_kwargs
        self._read_function = read_function
        sensor_kwargs = {"bus": bus, **init_kwargs}

        super().__init__(
            sensor_class=SMBusI2CDevice,
            sensor_kwargs=sensor_kwargs,
            include_all_data_each=include_all_data_each,
            **sensor_input_kwargs)

    def read_sensor_data(self, sensor_object=None):
        sensor_object = self.get_sensor_object(sensor_object=sensor_object)
        if sensor_object is None:
            return None

        try:
            sensor_data = sensor_object.read(
                read_function=self._read_function, **self._read_kwargs)
        except Exception as e:
            self.logger.error(
                "%s reading data from I2C SMBus device with function %s "
                "of %s sensor object %s on step %s: %s",
                type(e).__name__, self._read_function,
                type(self), self.object_class, self.name, e)
            self.logger.info("Error details:", exc_info=True)
            sensor_data = None

        return sensor_data


class SMBusI2CBlockInput(SMBusI2CInput):
    def __init__(
            self,
            i2c_addr,
            register=0,
            length=1,
            force=None,
            **smbus_input_kwargs):
        read_kwargs = {
            "i2c_addr": i2c_addr,
            "register": register,
            "length": length,
            "force": force,
            }

        super().__init__(read_function=I2C_BLOCK_READ_FUNCTION,
                         read_kwargs=read_kwargs, **smbus_input_kwargs)
