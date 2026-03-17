from dataclasses import dataclass
from device_manager.connection.utils.connection_type import ConnectionType
from device_manager.connection.utils.service_type import ServiceType


@dataclass
class ServiceInfo:
    serial_number: str
    ip: str
    port: int
    connection: ConnectionType
    service_type: ServiceType
