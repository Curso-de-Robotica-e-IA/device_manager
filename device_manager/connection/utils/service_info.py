from dataclasses import dataclass


@dataclass
class ServiceInfo:
    serial_number: str
    ip: str
    port: int
