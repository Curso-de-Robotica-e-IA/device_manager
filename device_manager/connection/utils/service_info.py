from dataclasses import dataclass
from device_manager.connection.utils.connection_type import ConnectionType


@dataclass
class ServiceInfo:
    serial_number: str
    ip: str
    port: int
    connection: ConnectionType
