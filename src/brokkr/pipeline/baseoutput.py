"""
Base classes for pipeline output steps.
"""

# Standard library imports
import abc
import os
from pathlib import Path

# Local imports
import brokkr.pipeline.base
import brokkr.utils.output


class FileOutputStep(brokkr.pipeline.base.OutputStep, metaclass=abc.ABCMeta):
    def __init__(
            self,
            key_name=None,
            output_path=Path(),
            filename_template=None,
            extension=None,
            filename_kwargs=None,
            drive_kwargs=None,
            **pipeline_step_kwargs):
        super().__init__(**pipeline_step_kwargs)

        self.key_name = key_name
        self.output_path = output_path
        self.filename_template = filename_template
        self.extension = extension
        self.filename_kwargs = (
            {} if filename_kwargs is None else filename_kwargs)
        self.drive_kwargs = {} if drive_kwargs is None else drive_kwargs

    @abc.abstractmethod
    def write_file(self, input_data, output_file_path):
        pass

    def execute(self, input_data=None):
        try:
            output_file_path = brokkr.utils.output.render_output_filename(
                output_path=self.output_path,
                filename_template=self.filename_template,
                extension=self.extension,
                drive_kwargs=self.drive_kwargs,
                **self.filename_kwargs,
                )
        except Exception as e:
            self.logger.error(
                "%s finding output directory %r: %s",
                type(e).__name__, self.output_path, e)
            self.logger.info("Error details:", exc_info=True)
            return input_data
        self.logger.debug("Ensuring output directory at %r",
                          output_file_path.parent.as_posix())
        os.makedirs(output_file_path.parent, exist_ok=True)
        self.logger.debug("Writing data to file at %r",
                          output_file_path.as_posix())
        if self.key_name:
            input_data_values = brokkr.pipeline.utils.get_data_value(
                input_data=input_data, key_name=self.key_name)
        else:
            input_data_values = input_data

        try:
            self.write_file(
                input_data_values, output_file_path=output_file_path)
            self.logger.debug("Data successfully written to file at %r",
                              output_file_path.as_posix())
            return input_data
        except Exception as e:
            self.logger.error(
                "%s writing output data to file at %r: %s",
                type(e).__name__, output_file_path.as_posix(), e)
            data_repr = repr(input_data)
            if len(data_repr) > 1000:
                data_repr = data_repr[:1000] + " <snipped at 1000 chars>"
            self.log_helper.log(data=data_repr)
            return input_data
