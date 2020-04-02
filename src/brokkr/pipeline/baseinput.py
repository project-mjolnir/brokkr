"""
Base classes for pipeline input steps.
"""

# Standard library imports
import abc

# Local imports
import brokkr.pipeline.base
import brokkr.pipeline.decode
import brokkr.pipeline.datavalue


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
