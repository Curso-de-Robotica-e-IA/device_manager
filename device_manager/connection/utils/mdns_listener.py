import re
import socket
from typing import Optional

from zeroconf import (
    ServiceInfo as ZeroconfServiceInfo,
)
from zeroconf import (
    ServiceListener,
    Zeroconf,
)

from device_manager.connection.utils.mdns_context import (
    MDnsContext,
    ServiceInfo,
)

r'''re_filter -> This string is used to filter the services found by the mDNS
listener. It is used to extract the serial number from the service name.
"adb\-(\w+)\-\w+\\" is the default value.'''
DEFAULT_REGEX_FILTER = r"adb\-(\w+)\-\w+\\?"


'''service_type -> In summary, this string is used to identify a specific type
of service (ADB TLS pairing) that can be discovered on the local network
using DNS-SD. "_adb-tls-pairing._tcp.local."'''
CONNECT_SERVICE_TYPE = "_adb-tls-connect._tcp.local."

'''This string is used to identify a specific type of service (ADB TLS pairing)
that can be discovered on the local network using DNS-SD.
'''
PAIRING_SERVICE_TYPE = "_adb-tls-pairing._tcp.local."


class MDnsListener(ServiceListener):
    """A listener for mDNS services. This listener is used to update the
    service context with the service information found by the Zeroconf
    instance. This class inherits from the ServiceListener class provided by
    the Zeroconf library.

    Args:
        service_context (MDnsContext): The service context to update with the
            service information found by the Zeroconf instance.
        re_filter (Optional[str], optional): A regular expression filter to
            extract the serial number from the service name. Defaults to None.
        service_type (str, optional): The service type to filter the services
            found by the mDNS listener. Defaults to
            "_adb-tls-pairing._tcp.local.".

    methods:
        update_service: Updates the service information in the service context.
        remove_service: Removes the service information from the service
            context.
        add_service: Adds the service information to the service context.
    """

    def __init__(
        self,
        service_context: MDnsContext,
        re_filter: Optional[str] = None,
        service_type: str = CONNECT_SERVICE_TYPE,
    ) -> None:
        super().__init__()
        self.__service_context = service_context
        self.__re_filter = re_filter
        self.__type_filter = service_type

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Updates the service information in the service context.

        Args:
            zc (Zeroconf): Zeroconf instance.
            type_ (str): The service type.
            name (str): The name of the service.
        """
        info = self._extract_info(zc.get_service_info(type_, name))
        if info:
            self.__service_context.update_service(info.serial_number, info)

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Removes the service information from the service context.

        Args:
            zc (Zeroconf): Zeroconf instance.
            type_ (str): The service type.
            name (str): The name of the service.
        """
        info = self._extract_info(zc.get_service_info(type_, name))
        if info:
            self.__service_context.to_offline_service(info.serial_number, info)

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Adds the service information to the service context.

        Args:
            zc (Zeroconf): Zeroconf instance.
            type_ (str): The service type.
            name (str): The name of the service.
        """
        info = self._extract_info(
            zc.get_service_info(type_, name),
        )
        if info:
            self.__service_context.add_service(info.serial_number, info)

    def _extract_info(
        self,
        info: ZeroconfServiceInfo,
    ) -> Optional[ServiceInfo]:
        """Extracts the serial number, IP address, and port from the service
        information. If the service name does not match the regular expression
        filter, then None is returned.

        Args:
            info (ZeroconfServiceInfo): The service information to extract
                the serial number, IP address, and port from.

        Returns:
            Optional[ServiceInfo]: The extracted service information.
        """
        try:
            ip = f"{socket.inet_ntoa(info.addresses[0])}"
            port = info.port
            if self.__re_filter is None:
                return ServiceInfo(info.name.split(".")[0], ip, port)
            match_result = re.match(
                rf"{self.__re_filter}.{self.__type_filter}", info.name
            )
            if match_result:
                serial_num = match_result.group(1)
                return ServiceInfo(serial_num, ip, port)
            else:
                print(f"AdbMDns not match: {info.name}")
        except Exception as e:  # pragma: no cover
            print(e)
            raise e
