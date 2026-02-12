from dataclasses import dataclass


@dataclass
class MdnsService:
    serial_number: str
    service_type: str
    ip: str
    port: int
