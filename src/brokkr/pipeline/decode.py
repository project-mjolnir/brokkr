"""
Common decode and conversion functionality.
"""

# Standard library imports
import datetime
import logging
import struct

# Local imports
import brokkr.pipeline.datavalue
import brokkr.utils.misc


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
        value, multiplier_to_s=1, divisor_to_s=1, use_local=False):
    if use_local:
        time_zone = None
    else:
        time_zone = datetime.timezone.utc
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
    False: _convert_none,
    True: _convert_pass,
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


class DataDecoder(brokkr.utils.misc.AutoReprMixin):
    conversion_functions = CONVERSION_FUNCTIONS

    def __init__(
            self,
            data_types,
            conversion_functions=None,
                ):
        self.data_types = data_types
        if conversion_functions is None:
            conversion_functions = {}
        conversion_functions = {
            **self.conversion_functions, **conversion_functions}

    def __len__(self):
        return len(self.data_types)

    def output_na_data(self):
        output_data = {
            data_type.name: brokkr.pipeline.datavalue.DataValue(
                data_type.na_marker, data_type=data_type, is_na=True)
            for data_type in self.data_types
            if data_type.conversion}
        return output_data

    def convert_data(self, raw_data):
        if not raw_data:
            output_data = self.output_na_data()
            LOGGER.debug("No data to convert, returning: %r", output_data)
            return output_data

        error_count = 0
        output_data = {}

        for data_type, value in zip(self.data_types, raw_data):
            if not data_type.conversion:
                continue  # If this data value should be dropped, ignore it
            try:
                output_value = (
                    self.conversion_functions[data_type.conversion](
                        value, **data_type.conversion_kwargs))
            # Handle errors decoding specific values
            except Exception as e:
                if error_count < 1:
                    LOGGER.warning(
                        "%s decoding data %r for data_type %r to %s: %s",
                        type(e).__name__, value,
                        data_type.name, data_type.conversion, e)
                    LOGGER.info("Error details:", exc_info=True)
                else:
                    LOGGER.info(
                        "%s decoding data %r for data_type %r to %s: %s",
                        type(e).__name__, value,
                        data_type.name, data_type.conversion, e)
                    LOGGER.debug("Error details:", exc_info=True)

                data_value = brokkr.pipeline.datavalue.DataValue(
                    data_type.na_marker, data_type=data_type, is_na=True)
                output_data[data_type.name] = data_value
                error_count += 1
            else:
                data_value = brokkr.pipeline.datavalue.DataValue(
                    output_value, data_type=data_type, raw_value=value)
                output_data[data_type.name] = data_value

        if error_count > 1:
            LOGGER.warning("%s additioanl decode errors were suppressed.",
                           error_count - 1)

        LOGGER.debug("Converted data: %r", output_data)
        return output_data

    def decode_data(self, data):
        if data is None:
            LOGGER.debug("No data to decode")
            output_data = self.output_na_data()
        else:
            output_data = self.convert_data(data)
        return output_data


class BinaryDataDecoder(DataDecoder):
    def __init__(
            self,
            struct_format=None,
            **data_decoder_kwargs,
                ):
        super().__init__(**data_decoder_kwargs)
        if struct_format is None:
            struct_format = "!" + "".join(
                [data_type.input_type for data_type in self.data_types])
        self.struct_format = struct_format
        self.packet_size = struct.calcsize(self.struct_format)

    def decode_binary(self, binary_data):
        try:
            decoded_vals = struct.unpack(self.struct_format, binary_data)
        # Handle overall decoding errors
        except Exception as e:
            if binary_data is not None:
                LOGGER.error("%s unpacking data: %s", type(e).__name__, e)
                LOGGER.info("Error details:", exc_info=True)
                LOGGER.info("Expected format: %r", self.struct_format)
                LOGGER.info("Binary data: %r", binary_data.hex())
            else:
                LOGGER.debug("No data to decode")
            decoded_vals = None
        else:
            LOGGER.debug("Decoded data values: %r", decoded_vals)

        return decoded_vals

    def decode_data(self, data):
        data = self.decode_binary(binary_data=data)
        output_data = super().decode_data(data=data)
        return output_data
