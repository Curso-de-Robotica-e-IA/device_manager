import logging
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
)

from device_manager.connection.utils.service_info import ServiceInfo

from device_manager.connection.utils.connection_type import ConnectionType
from device_manager.connection.utils.service_type import ServiceType

logger = logging.getLogger(__name__)

r"""re_filter -> This string is used to filter the services found by the mDNS
listener. It is used to extract the serial number from the service name.
"adb\-(\w+)\-\w+\\" is the default value."""
DEFAULT_REGEX_FILTER = r'adb\-(\w+)\-\w+\\?'


'''service_type -> In summary, this string is used to identify a specific type
of service (ADB TLS pairing) that can be discovered on the local network
using DNS-SD. "_adb-tls-pairing._tcp.local."'''
CONNECT_SERVICE_TYPE = '_adb-tls-connect._tcp.local.'

"""This string is used to identify a specific type of service (ADB TLS pairing)
that can be discovered on the local network using DNS-SD.
"""
PAIRING_SERVICE_TYPE = '_adb-tls-pairing._tcp.local.'


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
    ) -> None:
        super().__init__()
        self.__service_context = service_context
        self.__re_filter = re_filter

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Updates the service information in the service context.

        Args:
            zc (Zeroconf): Zeroconf instance.
            type_ (str): The service type.
            name (str): The name of the service.
        """
        info = self._extract_info(zc.get_service_info(type_, name), type_)
        if info:
            self.__service_context.update_service(info.serial_number, info)

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Removes the service information from the service context.

        Args:
            zc (Zeroconf): Zeroconf instance.
            type_ (str): The service type.
            name (str): The name of the service.
        """
        info = self._extract_info(zc.get_service_info(type_, name), type_)
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
            zc.get_service_info(type_, name),type_
        )
        if info:
            self.__service_context.add_service(info.serial_number, info)

    def _extract_info(
        self,
        info: ZeroconfServiceInfo,
        type_: str,
    ) -> Optional[ServiceInfo]:
        """Extracts the service information from the ZeroconfServiceInfo object.
        
        Args:
            info (ZeroconfServiceInfo): The ZeroconfServiceInfo object to extract
                the service information from.
            type_ (str): The service type.
                
        Returns:
            Optional[ServiceInfo]: The extracted service information, or None if
                the service information could not be extracted.
                """        
            
        if info is None:
            return None

        try:
            ip = socket.inet_ntoa(info.addresses[0])
            port = info.port

            if type_ == PAIRING_SERVICE_TYPE:
                service_type = ServiceType.PAIRING
            elif type_ == CONNECT_SERVICE_TYPE:
                service_type = ServiceType.CONNECT
            else:
                logger.warning(f"Unknown service type: {type_}")
                return None

            if self.__re_filter is None:
                serial = info.name.split('.')[0]
            else:
                match_result = re.match(self.__re_filter, info.name)
                if not match_result:
                    logger.warning(f'AdbMDns not match: {info.name}')
                    return None
                serial = match_result.group(1)

            return ServiceInfo(
                serial_number=serial,
                ip=ip,
                port=port,
                connection=ConnectionType.WIFI,
                service_type=service_type,
            )

        except Exception as e:  # pragma: no cover
            logger.error(e)
            raise
