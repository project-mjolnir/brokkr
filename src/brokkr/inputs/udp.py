"""
Read and decode a binary UDP datagram.
"""

# Local imports
import brokkr.pipeline.step
import brokkr.utils.network


class UDPInput(brokkr.pipeline.step.DecodeInputStep):
    def __init__(
            self,
            host,
            port,
            packet_size=None,
            buffer_size=brokkr.utils.network.BUFFER_SIZE_DEFAULT,
            timeout_s=brokkr.utils.network.TIMEOUT_S_DEFAULT,
            **decode_input_kwargs):
        super().__init__(**decode_input_kwargs)
        self._host = host
        self._port = port
        self._buffer_size = buffer_size
        self._timeout_s = timeout_s

        if packet_size is None:
            self._packet_size = self.decoder.packet_size
        else:
            self._packet_size = packet_size

    def read_raw_data(self):
        self.logger.debug("Reading UDP data")
        raw_data = brokkr.utils.network.recieve_udp(
            host=self._host,
            port=self._port,
            buffer_size=self._buffer_size,
            timeout_s=self._timeout_s,
            )

        if raw_data:
            raw_data = raw_data[:self._packet_size]
            self.logger.debug("Datagram: %s", raw_data.hex())
        elif raw_data is None:
            self.logger.debug("No UDP datagram recieved: %r", raw_data)
        else:
            self.logger.warning("Null UDP datagram recieved: %r", raw_data)
            raw_data = None

        return raw_data
