"""
Common decode and conversion functionality.
"""

# Standard library imports
import ast
import datetime
import logging
import math
import operator
import struct

# Third party imports
import simpleeval

# Local imports
import brokkr.pipeline.datavalue
import brokkr.utils.misc
import brokkr.utils.output


# --- Module-level constants --- #

NA_MARKER_DEFAULT = "NA"

OUTPUT_CUSTOM = "custom"

LOGGER = logging.getLogger(__name__)

EVAL_OPERATORS_EXTRA = {
    ast.BitAnd: operator.and_,
    ast.BitOr: operator.or_,
    ast.BitXor: operator.xor,
    ast.Invert: operator.invert,
    ast.LShift: operator.lshift,
    ast.RShift: operator.rshift,
    }


# --- Utility functions --- #

def generate_eval_parser(**simpleeval_kwargs):
    value_parser = simpleeval.SimpleEval(**simpleeval_kwargs)
    value_parser.operators = {
        **value_parser.operators, **EVAL_OPERATORS_EXTRA}
    return value_parser


def eval_oneshot(expression, **simpleeval_kwargs):
    value_parser = generate_eval_parser(**simpleeval_kwargs)
    eval_result = value_parser.eval(expression)
    return eval_result


# --- Conversion functions --- #

def _convert_none(value):
    # pylint: disable=unused-argument
    return None


def _convert_pass(value):
    return value


def _convert_bitfield(value):
    return int(value)


def _convert_bool(value):
    return bool(value)


def _convert_byte(value):
    return int(value)


def _convert_bytestr(value):
    return value.decode()


def _convert_bytestr_strip(value, strip_chars="\a\b\f\n\r\t\v\x00"):
    return value.decode().strip(strip_chars)


def _convert_float(value):
    return float(value)


def _convert_int(value, **kwargs):
    return int(value, **kwargs)


def _convert_str(value):
    return str(value)


def _convert_time_posix(
        value, multiplier_to_s=1, divisor_to_s=1,
        use_local=False, strip_tz=False):
    if use_local:
        time_zone = None
    else:
        time_zone = datetime.timezone.utc
    datetime_object = datetime.datetime.fromtimestamp(
        value * multiplier_to_s / divisor_to_s, tz=time_zone)
    if strip_tz:
        datetime_object = datetime_object.replace(tzinfo=None)
    return datetime_object


def _convert_time_posix_ms(value, divisor_to_s=1000, **time_posix_kwargs):
    return _convert_time_posix(
        value, divisor_to_s=divisor_to_s, **time_posix_kwargs)


def _convert_timestamp(value, time_format="%Y-%m-%d %H:%M:%S"):
    try:
        value = value.decode()
    except AttributeError:
        value = str(value)
    return datetime.datetime.strptime(value, time_format)


def _convert_custom(value, base=2, power=0, scale=1, offset=0):
    return value * (base ** power) * scale + offset


def _convert_eval(value, expression):
    return eval_oneshot(names={"value": value}, expression=expression)


CONVERSION_FUNCTIONS = {
    False: _convert_none,
    True: _convert_pass,
    "bitfield": _convert_bitfield,
    "bool": _convert_bool,
    "byte": _convert_byte,
    "bytestr": _convert_bytestr,
    "bytestr_strip": _convert_bytestr_strip,
    "float": _convert_float,
    "int": _convert_int,
    "str": _convert_str,
    "time_posix": _convert_time_posix,
    "time_posix_ms": _convert_time_posix_ms,
    "timestamp": _convert_timestamp,
    "custom": _convert_custom,
    "eval": _convert_eval,
    }


def convert_multistep(
        value,
        before=None,
        before_kwargs=None,
        main=None,
        after=None,
        after_kwargs=None,
        **main_kwargs,
        ):
    if before_kwargs is None:
        before_kwargs = {}
    if after_kwargs is None:
        after_kwargs = {}

    if before is not None:
        value = CONVERSION_FUNCTIONS[before](value, **before_kwargs)
    if main is not None:
        value = CONVERSION_FUNCTIONS[main](value, **main_kwargs)
    if after is not None:
        value = CONVERSION_FUNCTIONS[after](value, **after_kwargs)

    return value


CONVERSION_FUNCTIONS["multistep"] = convert_multistep


# --- Core decoder classes --- #

class DataDecoder(brokkr.utils.misc.AutoReprMixin):
    conversion_functions = CONVERSION_FUNCTIONS

    def __init__(
            self,
            data_types,
            na_marker=None,
            conversion_functions=None,
            include_all_data_each=False,
                ):
        self.data_types = data_types
        self.include_all_data_each = include_all_data_each
        if conversion_functions is None:
            conversion_functions = {}
        conversion_functions = {
            **self.conversion_functions, **conversion_functions}
        self.na_marker = NA_MARKER_DEFAULT if na_marker is None else na_marker

    def __len__(self):
        return len(self.data_types)

    def output_na_value(self, data_type):
        if data_type.na_marker is not None:
            na_marker = data_type.na_marker
        else:
            na_marker = self.na_marker
        data_value = brokkr.pipeline.datavalue.DataValue(
            na_marker, data_type=data_type, is_na=True)
        return data_value

    def output_na_values(self):
        output_data = {data_type.name: self.output_na_value(data_type)
                       for data_type in self.data_types
                       if data_type.conversion}
        return output_data

    def convert_data(self, raw_data):
        error_count = 0
        output_data = {}

        for idx, data_type in enumerate(self.data_types):
            if not data_type.conversion:
                continue  # If this data value should be dropped, ignore it
            value = raw_data
            # Split input into items if each corresponds to one output
            if not self.include_all_data_each:
                value = value[idx]
            if value is None:
                LOGGER.debug("Data value is None decoding data_type %s to %s, "
                             "coercing to NA value %r",
                             data_type.name, data_type.conversion,
                             self.output_na_value(data_type))
                output_data[data_type.name] = self.output_na_value(data_type)
                continue
            try:
                output_value = (
                    self.conversion_functions[data_type.conversion](
                        value, **data_type.conversion_kwargs))
                if data_type.digits is not None:
                    output_value = round(output_value, data_type.digits)
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

                output_data[data_type.name] = self.output_na_value(data_type)
                error_count += 1
            else:
                if data_type.uncertainty is True:
                    uncertainty = abs(
                        self.conversion_functions[data_type.conversion](
                            1, **data_type.conversion_kwargs)
                        - self.conversion_functions[data_type.conversion](
                            0, **data_type.conversion_kwargs))
                    uncertainty = round(
                        uncertainty, -int(math.floor(math.log10(uncertainty))))

                else:
                    uncertainty = data_type.uncertainty
                data_value = brokkr.pipeline.datavalue.DataValue(
                    output_value, data_type=data_type, raw_value=value,
                    uncertainty=uncertainty)
                output_data[data_type.name] = data_value

        if error_count > 1:
            LOGGER.warning("%s additional decode errors were suppressed.",
                           error_count - 1)

        LOGGER.debug("Converted data: {%s}", brokkr.utils.output.format_data(
            data=output_data, seperator=", ", include_raw=True))
        return output_data

    def decode_data(self, data):
        if data is None:
            output_data = self.output_na_values()
            LOGGER.debug(
                "No data to decode, returning NAs: %r",
                brokkr.utils.output.format_data(
                    data=output_data, seperator=", ", include_raw=False))
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
