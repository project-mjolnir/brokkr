"""
Data output to a binary file.
"""

# Local imports
import brokkr.pipeline.baseoutput
import brokkr.pipeline.utils


class BinaryFileOutput(brokkr.pipeline.baseoutput.FileOutputStep):
    def __init__(
            self, extension="bin", str_encoding="utf-8", **file_kwargs):
        super().__init__(
            extension=extension, **file_kwargs)
        self._str_encoding = str_encoding

    def write_file(self, input_data, output_file_path):
        self.logger.debug("Writing output as binary")
        data_values = brokkr.pipeline.utils.get_data_values(input_data)

        # Convert str-like to bytes if needed
        output_data = []
        for data_value in data_values:
            try:
                output_item = data_value.encode(self._str_encoding)
            except AttributeError:
                output_item = data_value
            output_data.append(output_item)

        with open(output_file_path, mode="ab") as output_file:
            for output_item in output_data:
                output_file.write(output_item)
        return input_data
