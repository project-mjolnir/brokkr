"""
Common decode and conversion functionality functionality.
"""

# Standard library imports
import datetime
import logging
import struct

# Local imports
from brokkr.config.main import CONFIG
import brokkr.utils.misc


CONVERSION_FUNCTIONS = {
    # pylint: disable=unnecessary-lambda
    None: lambda val: None,
    "": lambda val: val,
    "B": lambda val: int(val),
    "F": lambda val: float(val),
    "I": lambda val: int(val),
    "s": lambda val: str(val),
    "S": lambda val: val.decode(),
    "SS": lambda val: val.decode().strip("\a\b\f\n\r\t\v\x00"),
    "tm": lambda val: datetime.datetime.utcfromtimestamp(val / 1000),
    "ts": lambda val: datetime.datetime.utcfromtimestamp(val),
    }

LOGGER = logging.getLogger(__name__)


class Variable(brokkr.utils.misc.AutoReprMixin):
    def __init__(self, name, raw_type="H", output_type=""):
        self.name = name
        self.raw_type = raw_type
        self.output_type = output_type


class DataDecoder(brokkr.utils.misc.AutoReprMixin):
    conversion_functions = CONVERSION_FUNCTIONS

    def __init__(
            self,
            variables,
            conversion_functions=None,
            struct_format=None,
            na_marker=CONFIG["general"]["na_marker"],
                ):
        self.na_marker = na_marker

        self.variables = []
        for variable in variables:
            try:
                variable.name
            except AttributeError:
                self.variables.append(Variable(**variable))
            else:
                self.variables.append(variable)

        if conversion_functions is None:
            conversion_functions = {}
        self.conversion_functions = {**self.conversion_functions,
                                     **conversion_functions}
        if struct_format is None:
            struct_format = "!" + "".join(
                [variable.raw_type for variable in self.variables])
        self.struct_format = struct_format
        self.packet_size = struct.calcsize(self.struct_format)

    def output_na_data(self):
        output_data = {variable.name: self.na_marker
                       for variable in self.variables
                       if variable.output_type is not None}
        return output_data

    def convert_data(self, raw_data):
        if not raw_data:
            output_data = self.output_na_data()
            LOGGER.debug("No data to convert, returning: %r", output_data)
            return output_data

        error_count = 0
        output_data = {}

        for variable, val in zip(self.variables, raw_data):
            try:
                output_val = (
                    self.conversion_functions[variable.output_type](val))
                if output_val is not None:
                    output_data[variable.name] = output_val
            # Handle errors decoding specific values
            except Exception as e:
                if error_count < 1:
                    LOGGER.warning(
                        "%s decoding data %r for variable %r to %s: %s",
                        type(e).__name__, val,
                        variable.name, variable.output_type, e)
                    LOGGER.info("Error details:", exc_info=True)
                else:
                    LOGGER.info(
                        "%s decoding data %r for variable %r to %s: %s",
                        type(e).__name__, val,
                        variable.name, variable.output_type, e)
                    LOGGER.debug("Error details:", exc_info=True)

                output_data[variable.name] = self.na_marker
                error_count += 1

            if error_count > 1:
                LOGGER.warning("%s additioanl decode errors were suppressed.",
                               error_count - 1)

        LOGGER.debug("Converted data: %r", output_data)
        return output_data

    def decode_data(self, data_packet):
        try:
            decoded_vals = struct.unpack(self.struct_format, data_packet)
        # Handle overall decoding errors
        except Exception as e:
            if data_packet is not None:
                LOGGER.error("%s unpacking data: %s", type(e).__name__, e)
                LOGGER.info("Error details:", exc_info=True)
                LOGGER.info("Expected format: %r", self.struct_format)
                LOGGER.info("Packet data: %r", data_packet.hex())
            else:
                LOGGER.debug("No data to decode")
            output_data = self.output_na_data()
            LOGGER.debug("Returning empty data: %r", output_data)
        else:
            LOGGER.debug("Decoded data values: %r", decoded_vals)
            output_data = self.convert_data(decoded_vals)

        return output_data
