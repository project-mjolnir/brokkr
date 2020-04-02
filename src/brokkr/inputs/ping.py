"""
Ping input class for Brokkr.
"""

# Standard library imports
import subprocess

# Local imports
import brokkr.pipeline.datavalue
import brokkr.pipeline.baseinput
import brokkr.utils.misc
import brokkr.utils.network


class PingInput(brokkr.pipeline.baseinput.ValueInputStep):
    def __init__(
            self,
            host,
            timeout_s=brokkr.utils.network.TIMEOUT_S_DEFAULT,
            data_name="ping",
            full_name="Ping Retcode",
            **value_input_kwargs):
        ping_data_type = brokkr.pipeline.datavalue.DataType(
            name=data_name,
            binary_type="i",
            full_name=full_name,
            unit=False,
            uncertainty=False,
            )
        super().__init__(data_types=[ping_data_type], binary_decoder=False,
                         **value_input_kwargs)

        self._host = host
        self._timeout_s = timeout_s

    def read_raw_data(self, input_data=None):
        try:
            ping_output = brokkr.utils.network.ping(
                host=self._host, count=1, timeout_s=self._timeout_s)
            output_value = ping_output.returncode
            self.logger.debug("Ping command output: %r", ping_output)
        except subprocess.TimeoutExpired:
            self.logger.warning("Process timeout in %s s running ping command",
                                self._timeout_s)
            self.logger.debug("Error details:", exc_info=True)
            output_value = -9
        except Exception as e:
            self.logger.error("%s running ping command: %s",
                              type(e).__name__, e)
            self.logger.info("Error details:", exc_info=True)
            output_value = -99

        raw_data = [output_value]
        return raw_data
