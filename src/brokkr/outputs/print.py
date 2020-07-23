"""
Data output to the console.
"""

# Standard library imports
import logging
import reprlib
import sys

# Local imports
import brokkr.pipeline.base
import brokkr.utils.output


CURSOR_UP_CHAR = '\x1b[1A'
ERASE_LINE_CHAR = '\x1b[2K'

DEFAULT_ITEM_LIMIT = 2**8
DEFAULT_OUTPUT_LIMIT = 2**12


class PrintOutput(brokkr.pipeline.base.OutputStep):
    def __init__(
            self,
            prefix="",
            in_place=False,
            output_limit=DEFAULT_OUTPUT_LIMIT,
            repr_limits=False,
            **pipeline_step_kwargs):
        super().__init__(**pipeline_step_kwargs)
        self.prefix = prefix
        self.in_place = in_place
        self.ran_once = False
        self.output_limit = output_limit

        if repr_limits:
            print_repr = reprlib.Repr()
            for attr_name, attr_value in repr_limits.items():
                setattr(print_repr, attr_name, attr_value)
            self.repr_fn = print_repr.repr
        else:
            self.repr_fn = repr

    def execute(self, input_data=None):
        if isinstance(input_data, str):
            output_data = input_data
        else:
            output_data = self.prefix + self.repr_fn(input_data)
        if self.output_limit:
            output_data = output_data[:self.output_limit]
        if self.in_place:
            output_data = "\r" + output_data
            sys.stdout.write(output_data)
            sys.stdout.flush()
        else:
            print(output_data)
        return output_data


class PrettyPrintOutput(PrintOutput):
    def __init__(
            self,
            in_place=True,
            item_limit=DEFAULT_ITEM_LIMIT,
            fallback=False,
            **print_output_kwargs):
        super().__init__(in_place=in_place, **print_output_kwargs)
        self.item_limit = item_limit
        self.fallback = fallback

    def execute(self, input_data=None):
        try:
            output_data = brokkr.utils.output.format_data(
                input_data, item_limit=self.item_limit) + "\n"
        except AttributeError as e:
            if not self.fallback:
                self.logger.debug(
                    "%s pretty-printing non-dict data of type %s: %s",
                    type(e).__name__, type(input_data), e)
                raise
            self.logger.debug("%s pretty-printing non-dict data of type %s, "
                              "falling back to repr: %s",
                              type(e).__name__, type(input_data), e)
            self.in_place = False

        if self.in_place and self.ran_once:
            output_data = (
                (CURSOR_UP_CHAR + ERASE_LINE_CHAR) * output_data.count("\n")
                + self.prefix + output_data)
        output_data = super().execute(input_data=output_data)
        if self.in_place and not self.ran_once:
            logging.disable(level=logging.CRITICAL)
        self.ran_once = True
        return output_data
