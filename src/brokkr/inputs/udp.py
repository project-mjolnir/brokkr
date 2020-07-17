"""
Read and decode a binary UDP datagram.
"""

# Standard library imports
import socket

# Local imports
from brokkr.constants import Errors
import brokkr.pipeline.baseinput
import brokkr.utils.network


class UDPInput(brokkr.pipeline.baseinput.ValueInputStep):
    def __init__(
            self,
            host,
            port,
            action,
            data_length=None,
            buffer_size=brokkr.utils.network.BUFFER_SIZE_DEFAULT,
            timeout_s=brokkr.utils.network.TIMEOUT_S_DEFAULT,
            **value_input_kwargs):
        super().__init__(binary_decoder=True, **value_input_kwargs)
        self._host = host
        self._port = port
        self._action = action
        self._buffer_size = buffer_size
        self._timeout_s = timeout_s

        self._data_length = (self.decoder.packet_size if data_length is None
                             else data_length)

    def read_raw_data(self, input_data=None):
        self.logger.debug("Reading UDP data")
        raw_data = brokkr.utils.network.read_socket_data(
            host=self._host,
            port=self._port,
            action=self._action,
            socket_type=socket.SOCK_DGRAM,
            timeout_s=self._timeout_s,
            errors=Errors.LOG,
            data_length=self._data_length,
            buffer_size=self._buffer_size,
            )

        if raw_data is None:
            self.logger.debug("No UDP datagram recieved: %r", raw_data)
        elif not raw_data:
            self.logger.warning("Null UDP datagram recieved: %r", raw_data)
            raw_data = None
        else:
            self.logger.debug("Datagram: %s", raw_data.hex())

        return raw_data
