"""
Read and decode binary network packets, datagram and more.
"""

# Standard library imports
import socket

# Local imports
from brokkr.constants import Errors
import brokkr.pipeline.baseinput
import brokkr.utils.network


class NetworkInput(brokkr.pipeline.baseinput.ValueInputStep):
    SOCKET_FAMILY_LOOKUP = {
        "IPV4": socket.AF_INET,
        "IPV6": socket.AF_INET6,
        }

    SOCKET_TYPE_LOOKUP = {
        "TCP": socket.SOCK_STREAM,
        "UDP": socket.SOCK_DGRAM,
        }

    def __init__(
            self,
            host,
            port,
            action,
            socket_family="IPV4",
            socket_type="TCP",
            timeout_s=brokkr.utils.network.TIMEOUT_S_DEFAULT,
            network_kwargs=None,
            **value_input_kwargs):
        super().__init__(binary_decoder=True, **value_input_kwargs)
        self._host = host
        self._port = port
        self._action = action
        self._socket_family = socket_family
        self._socket_type = socket_type
        self._timeout_s = timeout_s

        for attr_name, prefix in [("socket_family", "AF_"),
                                  ("socket_type", "SOCK_")]:
            input_value = locals()[attr_name].upper()
            lookup_table = getattr(type(self), f"{attr_name.upper()}_LOOKUP")
            attr_value = lookup_table.get(input_value, None)
            if attr_value is None:
                try:
                    attr_value = getattr(socket, f"{prefix}{input_value}")
                except AttributeError:
                    raise ValueError(
                        f"{attr_name} must be either value in "
                        f"{type(self).__name__}.{attr_name.upper()}_LOOKUP "
                        f"{set(lookup_table.keys())} or in socket.{prefix}*, "
                        f"not {input_value}")
            setattr(self, f"_{attr_name}", attr_value)

        self._network_kwargs = {} if network_kwargs is None else network_kwargs
        if not self._network_kwargs.get("data_length", None):
            self._network_kwargs["data_length"] = self.decoder.packet_size

    def read_raw_data(self, input_data=None):
        self.logger.debug("Reading network data")
        raw_data = brokkr.utils.network.read_socket_data(
            host=self._host,
            port=self._port,
            action=self._action,
            socket_family=self._socket_family,
            socket_type=self._socket_type,
            timeout_s=self._timeout_s,
            errors=Errors.LOG,
            **self._network_kwargs,
            )

        if raw_data is not None and not raw_data:
            self.logger.warning(
                "Null network data recieved, returning None: %r", raw_data)
            return None

        return raw_data
