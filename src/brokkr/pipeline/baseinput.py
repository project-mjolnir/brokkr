"""
Base classes for pipeline input steps.
"""

# Standard library imports
import abc
import importlib

# Local imports
import brokkr.pipeline.base
import brokkr.pipeline.decode
import brokkr.pipeline.datavalue


# --- Core base classes --- #

class ValueInputStep(brokkr.pipeline.base.InputStep, metaclass=abc.ABCMeta):
    def __init__(
            self,
            data_types,
            binary_decoder=False,
            datatype_default_kwargs=None,
            conversion_functions=None,
            na_marker=None,
            include_all_data_each=False,
            name_suffix="",
            ignore_na_on_start=False,
            **pipeline_step_kwargs):
        super().__init__(**pipeline_step_kwargs)
        self.ignore_na_on_start = ignore_na_on_start
        if datatype_default_kwargs is None:
            datatype_default_kwargs = {}

        self.data_types = []
        for data_type in data_types:
            try:
                data_type.name
            except AttributeError:  # If data_type isn't already an object
                try:
                    data_type["name"]
                except TypeError:  # If data_types is a dict, not a list
                    data_type_dict = data_types[data_type]
                    data_type_dict["name"] = data_type
                    data_type = data_type_dict

                data_type = brokkr.pipeline.datavalue.DataType(
                    **{**datatype_default_kwargs, **data_type})
            data_type.name += name_suffix
            self.data_types.append(data_type)

        if binary_decoder:
            decoder_class = brokkr.pipeline.decode.BinaryDataDecoder
        else:
            decoder_class = brokkr.pipeline.decode.DataDecoder

        self.decoder = decoder_class(
            data_types=self.data_types,
            conversion_functions=conversion_functions,
            na_marker=na_marker,
            include_all_data_each=include_all_data_each,
            )

    @abc.abstractmethod
    def read_raw_data(self, input_data=None):
        pass

    def decode_data(self, raw_data):
        # self.logger.debug("Created data decoder: %r", self.decoder)
        decoded_data = self.decoder.decode_data(raw_data)
        return decoded_data

    def execute(self, input_data=None):
        input_data = super().execute(input_data=input_data)
        # Handle when the pipeline signals an NA data block should be sent
        if (isinstance(input_data, brokkr.pipeline.base.NASentinel)
                and not self.ignore_na_on_start):
            return self.decode_data(raw_data=None)
        raw_data = self.read_raw_data(input_data=input_data)
        output_data = self.decode_data(raw_data)
        return output_data


class SensorInputStep(ValueInputStep, metaclass=abc.ABCMeta):
    def __init__(
            self,
            sensor_class,
            sensor_module=None,
            sensor_args=None,
            sensor_kwargs=None,
            cache_sensor_object=False,
            binary_decoder=False,
            **value_input_kwargs):
        super().__init__(binary_decoder=binary_decoder, **value_input_kwargs)
        self.sensor_args = () if sensor_args is None else sensor_args
        self.sensor_kwargs = {} if sensor_kwargs is None else sensor_kwargs
        self.sensor_object = None
        self.cache_sensor_object = cache_sensor_object

        if sensor_module is not None:
            module_object = importlib.import_module(sensor_module)
            sensor_class = getattr(module_object, sensor_class)
        self.object_class = sensor_class

    def init_sensor_object(self, *sensor_args, **sensor_kwargs):
        if not sensor_args:
            sensor_args = self.sensor_args
        if not sensor_kwargs:
            sensor_kwargs = self.sensor_kwargs

        self.logger.debug(
            "Initializing sensor object %s with args %r, kwargs %s",
            self.object_class, sensor_args, sensor_kwargs)
        try:
            sensor_object = self.object_class(
                *sensor_args, **sensor_kwargs)
        except Exception as e:
            self.logger.error(
                "%s initializing %s sensor object %s on step %s: %s",
                type(e).__name__, type(self), self.object_class,
                self.name, e)
            self.logger.info("Error details:", exc_info=True)
            self.logger.info("Sensor args: %r | Sensor kwargs: %r:",
                             sensor_args, sensor_kwargs)
            sensor_object = None
        self.logger.debug(
            "Initialized sensor object %s to %r",
            self.object_class, sensor_object)

        if self.cache_sensor_object:
            self.sensor_object = sensor_object
            self.logger.debug("Cached sensor object %s", self.object_class)
        return sensor_object

    def get_sensor_object(self, sensor_object=None):
        if sensor_object is not None:
            return sensor_object
        if self.sensor_object is not None:
            return self.sensor_object

        sensor_object = self.init_sensor_object()
        return sensor_object

    @abc.abstractmethod
    def read_sensor_data(self, sensor_object=None):
        pass

    def read_raw_data(self, input_data=None):
        raw_data = self.read_sensor_data()
        return raw_data


class AttributeInputStep(SensorInputStep, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def read_sensor_value(self, sensor_object, data_type):
        pass

    def read_sensor_data(self, sensor_object=None):
        sensor_object = self.get_sensor_object(sensor_object=sensor_object)
        if sensor_object is None:
            return None

        sensor_data = []
        for data_type in self.data_types:
            try:
                data_value = self.read_sensor_value(
                    sensor_object=sensor_object, data_type=data_type)
            except Exception as e:
                self.logger.error(
                    "%s on attribute %s from %s sensor object %s "
                    "on step %s: %s",
                    type(e).__name__, data_type.attribute_name, type(self),
                    self.object_class, self.name, e)
                self.logger.info("Error details:", exc_info=True)
                data_value = None
            else:
                self.logger.debug(
                    "Read value %r from attribute %s of sensor %s",
                    data_value, data_type.attribute_name, self.object_class)
            sensor_data.append(data_value)
        return sensor_data


class PropertyInputStep(AttributeInputStep):
    def read_sensor_value(self, sensor_object, data_type):
        if sensor_object is None:
            sensor_object = self.sensor_object
        data_value = getattr(sensor_object, data_type.attribute_name)
        return data_value


class MethodInputStep(AttributeInputStep):
    def read_sensor_value(self, sensor_object, data_type):
        if sensor_object is None:
            sensor_object = self.sensor_object
        function_kwargs = getattr(data_type, "function_kwargs", {})
        data_value = getattr(sensor_object, data_type.attribute_name)(
            **function_kwargs)
        return data_value
