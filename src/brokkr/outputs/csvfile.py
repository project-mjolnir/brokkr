"""
Data output to a CSV file.
"""

# Standard library imports
import csv

# Local imports
import brokkr.pipeline.baseoutput
import brokkr.utils.output


CSV_KWARGS_DEFAULT = {
    "extrasaction": "ignore",
    "dialect": "unix",
    "delimiter": ",",
    "quoting": csv.QUOTE_MINIMAL,
    "strict": False,
    }


class CSVFileOutput(brokkr.pipeline.baseoutput.FileOutputStep):
    def __init__(
            self, csv_kwargs=None, extension="csv", **file_kwargs):
        super().__init__(extension=extension, **file_kwargs)

        if csv_kwargs is None:
            csv_kwargs = {}
        self.csv_kwargs = {**CSV_KWARGS_DEFAULT, **csv_kwargs}

    def write_file(self, input_data, output_file_path):
        with open(output_file_path, mode="a",
                  encoding="utf-8", newline="") as output_file:
            self.logger.debug("Writing output as CSV")
            csv_writer = csv.DictWriter(
                output_file, fieldnames=input_data.keys(), **self.csv_kwargs)
            if not output_file.tell():
                self.logger.debug("Writing file header")
                csv_writer.writeheader()
            csv_writer.writerow(input_data)
