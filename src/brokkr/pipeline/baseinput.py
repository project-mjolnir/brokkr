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
            **pipeline_step_kwargs):
        super().__init__(**pipeline_step_kwargs)
        if datatype_default_kwargs is None:
            datatype_default_kwargs = {}

        self.data_types = []
        for data_type in data_types:
            try:
                data_type.name
            except AttributeError:  # If data_type isn't already an object
                try:
                    data_type["name"]
                except TypeError:
                    data_type_dict = data_types[data_type]
                    data_type_dict["name"] = data_type
                    data_type = data_type_dict

                data_type = brokkr.pipeline.datavalue.DataType(
                    **{**datatype_default_kwargs, **data_type})
            self.data_types.append(data_type)

        if binary_decoder:
            decoder_class = brokkr.pipeline.decode.BinaryDataDecoder
        else:
            decoder_class = brokkr.pipeline.decode.DataDecoder

        self.decoder = decoder_class(
            data_types=self.data_types,
            conversion_functions=conversion_functions,
            na_marker=na_marker,
            )

    @abc.abstractmethod
    def read_raw_data(self, input_data=None):
        pass

    def decode_data(self, raw_data):
        self.logger.debug("Created data decoder: %r", self.decoder)
        decoded_data = self.decoder.decode_data(raw_data)
        return decoded_data

    def execute(self, input_data=None):
        input_data = super().execute(input_data=input_data)
        raw_data = self.read_raw_data(input_data=input_data)
        output_data = self.decode_data(raw_data)
        return output_data


class PropertyInputStep(ValueInputStep):
    def __init__(
            self,
            sensor_module,
            sensor_class,
            sensor_args=None,
            sensor_kwargs=None,
            **value_input_kwargs):
        super().__init__(binary_decoder=False, **value_input_kwargs)
        self.sensor_args = () if sensor_args is None else sensor_args
        self.sensor_kwargs = {} if sensor_kwargs is None else sensor_kwargs
        self.sensor_object = None

        module_object = importlib.import_module(sensor_module)
        self.object_class = getattr(module_object, sensor_class)

    def init_sensor_object(self, *sensor_args, **sensor_kwargs):
        if not sensor_args:
            sensor_args = self.sensor_args
        if not sensor_kwargs:
            sensor_kwargs = self.sensor_kwargs

        try:
            sensor_object = self.object_class(
                *sensor_args, **sensor_kwargs)
        except Exception as e:
            self.logger.error(
                "%s initializing %s sensor object %s on step %s: %s",
                type(e).__name__, type(self), type(self.object_class),
                self.name, e)
            self.logger.info("Error details:", exc_info=True)
            return None
        else:
            return sensor_object

    def read_properties(self, sensor_object=None):
        if sensor_object is None:
            sensor_object = self.sensor_object

        if sensor_object is None:
            sensor_object = self.init_sensor_object()
            if sensor_object is None:
                return None

        raw_data = []
        for data_type in self.data_types:
            try:
                data_value = getattr(sensor_object, data_type.property_name)
            except Exception as e:
                self.logger.error(
                    "%s getting attribute %s from %s sensor object %s "
                    "on step %s: %s",
                    type(e).__name__, data_type.property_name, type(self),
                    type(self.object_class), self.name, e)
                self.logger.info("Error details:", exc_info=True)
                data_value = None
            raw_data.append(data_value)
        return raw_data

    def read_raw_data(self, input_data=None):
        raw_data = self.read_properties()
        return raw_data
