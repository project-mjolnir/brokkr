"""
Common decode and conversion functionality.
"""

# Standard library imports
import datetime
import logging
import struct

# Local imports
from brokkr.config.main import CONFIG
import brokkr.utils.misc


OUTPUT_NONE = "none"
OUTPUT_CUSTOM = "custom"


def _convert_none(value):
    # pylint: disable=unused-argument
    return None


def _convert_pass(value):
    return value


def _convert_bitfield(value):
    return int(value)


def _convert_byte(value):
    return int(value)


def _convert_bytestr(value):
    return value.decode()


def _convert_bytestr_strip(value, strip_chars="\a\b\f\n\r\t\v\x00"):
    return value.decode().strip(strip_chars)


def _convert_float(value):
    return float(value)


def _convert_int(value):
    return int(value)


def _convert_str(value):
    return str(value)


def _convert_time_posix(
        value, multiplier_to_s=1, divisor_to_s=1, time_zone="utc"):
    time_zone = getattr(datetime.timezone, time_zone)
    return datetime.datetime.fromtimestamp(
        value * multiplier_to_s / divisor_to_s, tz=time_zone)


def _convert_time_posix_ms(value, divisor_to_s=1000, **time_posix_kwargs):
    return _convert_time_posix(
        value, divisor_to_s=divisor_to_s, **time_posix_kwargs)


def _convert_timestamp(value, time_format="%Y-%m-%d %H:%M:%S"):
    try:
        value = value.decode()
    except AttributeError:
        value = str(value)
    return datetime.datetime.strptime(value, time_format)


CONVERSION_FUNCTIONS = {
    OUTPUT_NONE: _convert_none,
    "pass": _convert_pass,
    "bitfield": _convert_bitfield,
    "byte": _convert_byte,
    "bytestr": _convert_bytestr,
    "bytestr_strip": _convert_bytestr_strip,
    "float": _convert_float,
    "int": _convert_int,
    "str": _convert_str,
    "time_posix": _convert_time_posix,
    "time_posix_ms": _convert_time_posix_ms,
    "timestamp": _convert_timestamp,
    }


def convert_custom(
        value, scale=1, offset=0, base=2, power=0, digits=None, after=None,
        **after_kwargs):
    value = value * (base ** power) * scale + offset
    if digits is not None:
        value = round(value, digits)
    if after is not None:
        value = CONVERSION_FUNCTIONS[after](value, **after_kwargs)
    return value


CONVERSION_FUNCTIONS["custom"] = convert_custom


LOGGER = logging.getLogger(__name__)


class Variable(brokkr.utils.misc.AutoReprMixin):
    def __init__(
            self, name, conversion_functions, raw_type="i", output_type="pass",
            **conversion_kwargs):
        self.name = name
        self.raw_type = raw_type
        self.output_type = output_type
        self.conversion_function = conversion_functions[self.output_type]
        self.conversion_kwargs = conversion_kwargs


class DataDecoder(brokkr.utils.misc.AutoReprMixin):
    conversion_functions = CONVERSION_FUNCTIONS

    def __init__(
            self,
            variables,
            conversion_functions=None,
            custom_types=None,
            struct_format=None,
            na_marker=CONFIG["general"]["na_marker"],
            **variable_default_kwargs,
                ):
        self.na_marker = na_marker

        if conversion_functions is None:
            conversion_functions = {}
        conversion_functions = {
            **self.conversion_functions, **conversion_functions}

        custom_types = {} if custom_types is None else custom_types
        self.variables = []
        for variable in variables:
            try:
                variable.name
            except AttributeError:  # If variables isn't already an object
                try:
                    variable["name"]  # If variables a dict instead of a list
                except TypeError:
                    variable_dict = variables[variable]
                    variable_dict["name"] = variable
                    variable = variable_dict

                type_kwargs = custom_types.get(
                    variable.get("output_type", None), {})
                if type_kwargs:
                    del variable["output_type"]
                variable = Variable(
                    conversion_functions=conversion_functions,
                    **{**variable_default_kwargs, **type_kwargs, **variable})
            self.variables.append(variable)

        if struct_format is None:
            struct_format = "!" + "".join(
                [variable.raw_type for variable in self.variables])
        self.struct_format = struct_format
        self.packet_size = struct.calcsize(self.struct_format)

    def output_na_data(self):
        output_data = {variable.name: self.na_marker
                       for variable in self.variables
                       if variable.output_type is not OUTPUT_NONE}
        return output_data

    def convert_data(self, raw_data):
        if not raw_data:
            output_data = self.output_na_data()
            LOGGER.debug("No data to convert, returning: %r", output_data)
            return output_data

        error_count = 0
        output_data = {}

        for variable, value in zip(self.variables, raw_data):
            try:
                output_value = (
                    self.conversion_functions[variable.output_type](
                        value, **variable.conversion_kwargs))
                if output_value is not None:
                    output_data[variable.name] = output_value
            # Handle errors decoding specific values
            except Exception as e:
                if error_count < 1:
                    LOGGER.warning(
                        "%s decoding data %r for variable %r to %s: %s",
                        type(e).__name__, value,
                        variable.name, variable.output_type, e)
                    LOGGER.info("Error details:", exc_info=True)
                else:
                    LOGGER.info(
                        "%s decoding data %r for variable %r to %s: %s",
                        type(e).__name__, value,
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
