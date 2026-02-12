import subprocess
from typing import List

from device_manager.connection.utils.mdns_context import MDnsContext
from device_manager.connection.utils.mdns_service import MdnsService


'''service_type -> In summary, this string is used to identify a specific type
of service (ADB TLS pairing) that can be discovered on the local network
using DNS-SD. "_adb-tls-pairing._tcp.local."'''
CONNECT_SERVICE_TYPE = '_adb-tls-connect._tcp'

"""This string is used to identify a specific type of service (ADB TLS pairing)
that can be discovered on the local network using DNS-SD.
"""
PAIRING_SERVICE_TYPE = '_adb-tls-pairing._tcp'


class MDnsListener:
    """Scans ADB mDNS services using `adb mdns services`.
    This class is responsible for scanning the local network for ADB services
    using the `adb mdns services` command. It extracts the relevant information
    from the command output and updates the `MDnsContext` with the discovered
    services. The services are categorized based on their type (connect or
    pairing) and stored in the context for further use.
        Attributes:
            _context (MDnsContext): The context that holds the discovered services.
        Methods:
            scan: Scans for ADB mDNS services and updates the context with the discovered services.
            get_service_info: Executes the `adb mdns services` command and extracts the service information 
                from the output, returning a list of `MdnsService` instances representing the discovered services.
    """

    def __init__(self, context: MDnsContext) -> None:
        self._context = context

    def scan(self) -> None:
        """Scans for ADB mDNS services and updates the context with the discovered services.
        This method executes the `adb mdns services` command to discover ADB
        services on the local network. It then processes the command output to
        extract the relevant information about each service, such as the serial
        number, service type, IP address, and port. The extracted information is
        used to create `MdnsService` instances, which are then stored in the
        `MDnsContext` for further use.
        
        Returns:
            
            None
        """
        services = self.get_service_info()
        self._context.set_services(services)

    @staticmethod
    def get_service_info() -> List[MdnsService]:
        """Executes the `adb mdns services` command and extracts the service information from the output.
            This method runs the `adb mdns services` command to retrieve the list of ADB services available on the local network. 
            It processes the command output to extract details about each service, including the serial number, service type (connect or pairing), IP address
            and port. The extracted information is used to create a list of `MdnsService` instances, which represent the discovered services.
        
        Returns:
            List[MdnsService]: A list of `MdnsService` instances representing the discovered services.
        """
        result = subprocess.run(
            ["adb", "mdns", "services"],
            capture_output=True,
            text=True,
            check=False,
        )

        services = {}
        lines = result.stdout.strip().splitlines()[1:]

        for line in lines:
            parts = line.split()
            if len(parts) < 3:
                continue

            try:
                serial_number = parts[0].split("-" )[1]
                if parts[1] == CONNECT_SERVICE_TYPE:
                    service_type = "ONLINE"
                elif parts[1] == PAIRING_SERVICE_TYPE:
                    service_type = "PAIRING"
                else:
                    continue
                ip, port = parts[2].split(":", 1)
            except Exception:
                continue

            key = (serial_number, service_type, ip, port)

            services[key] = MdnsService(
                serial_number=serial_number,
                service_type=service_type,
                ip=ip,
                port=int(port),
            )

        return list(services.values())
