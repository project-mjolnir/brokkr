"""
Data output to the console.
"""

# Standard library imports
import logging
import sys

# Local imports
import brokkr.pipeline.base
import brokkr.utils.output


CURSOR_UP_CHAR = '\x1b[1A'
ERASE_LINE_CHAR = '\x1b[2K'


class PrintOutput(brokkr.pipeline.base.OutputStep):
    def __init__(self, prefix="", in_place=False, **pipeline_step_kwargs):
        super().__init__(**pipeline_step_kwargs)
        self.prefix = prefix
        self.in_place = in_place
        self.ran_once = False

    def execute(self, input_data=None):
        if not isinstance(input_data, str):
            output_data = self.prefix + repr(input_data)
        else:
            output_data = input_data
        if self.in_place:
            output_data = "\r" + output_data
            sys.stdout.write(output_data)
            sys.stdout.flush()
        else:
            print(output_data)
        return output_data


class PrettyPrintOutput(PrintOutput):
    def __init__(self, in_place=True, **print_output_kwargs):
        super().__init__(in_place=in_place, **print_output_kwargs)

    def execute(self, input_data=None):
        output_data = brokkr.utils.output.format_data(input_data) + "\n"
        if self.in_place and self.ran_once:
            output_data = (
                (CURSOR_UP_CHAR + ERASE_LINE_CHAR) * output_data.count("\n")
                + self.prefix + output_data)
        output_data = super().execute(input_data=output_data)
        if self.in_place and not self.ran_once:
            logging.disable(level=logging.CRITICAL)
        self.ran_once = True
        return output_data
