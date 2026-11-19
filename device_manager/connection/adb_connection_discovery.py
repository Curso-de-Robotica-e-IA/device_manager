from contextlib import contextmanager
import logging
from typing import Any, Generator

from zeroconf import ServiceBrowser

from device_manager.connection.utils.connection_status import (
    ConnectionInfoStatus,
)
from device_manager.connection.utils.mdns_context import (
    MDnsContext,
    ServiceInfo,
)
from device_manager.connection.utils.mdns_listener import (
    CONNECT_SERVICE_TYPE,
    DEFAULT_REGEX_FILTER,
)
from device_manager.connection.utils.mdns_session import MdnsBrowserSession

logger = logging.getLogger(__name__)


class AdbConnectionDiscovery:
    """Class to discover the devices connected to the ADB server using mDNS.
    It uses the Zeroconf library to listen to the mDNS services, and the
    MDnsListener class to update the service context with the service
    information found by the Zeroconf instance.

    Properties:
        - `service_browser_started` (bool): Check if the ServiceBrowser has
            been started.
        - `browser` (Optional[ServiceBrowser]): The actual ServiceBrowser
            instance.
        - `zeroconf_status` (bool): Check if the Zeroconf instance is active.

    Methods:
        start: Start the ServiceBrowser to listen to the mDNS services.
        start_discovery_listener: Context manager to start the ServiceBrowser
            and stop it after the block is executed.
        online_devices: Get the online devices from the class Context.
        offline_devices: Get the offline devices from the class Context.
        get_service_info_for: Get the service information for a given serial
            number.
        connection_status_for_device: Check the connection status for a given
            service, based on the current context.
        stop_discovery_listener: Stop the ServiceBrowser and close the Zeroconf
            instance.
    """

    def __init__(self) -> None:
        self.__context = MDnsContext()
        self.__session = MdnsBrowserSession(
            context=self.__context,
            service_type=CONNECT_SERVICE_TYPE,
            service_re_filter=DEFAULT_REGEX_FILTER,
        )

    def start(self) -> None:
        """Start the ServiceBrowser to listen to the mDNS services."""
        self.__session.start()

    @contextmanager
    def start_discovery_listener(self) -> Generator[None, Any, None]:
        """Context manager to start the ServiceBrowser and stop it after the
        block is executed. Once the block is executed, the ServiceBrowser is
        stopped.
        """
        try:
            self.start()
            yield
        finally:
            self.stop_discovery_listener()

    @property
    def service_browser_started(self) -> bool:
        """Check if the ServiceBrowser has been started.

        Returns:
            bool: True if the ServiceBrowser has been started, False otherwise.
        """
        return self.__session.started

    @property
    def browser(self) -> ServiceBrowser | None:
        """Returns the actual ServiceBrowser instance, if it exists.

        Returns:
            ServiceBrowser: The ServiceBrowser instance.
        """
        return self.__session.browser

    @property
    def zeroconf_status(self) -> bool:
        """Check if the Zeroconf instance is active.

        Returns:
            bool: True if the Zeroconf instance is active, False otherwise.
        """
        return self.__session.zeroconf_status

    def online_devices(self) -> dict[str, ServiceInfo]:
        """Get the online devices from the class Context.

        Returns:
            Dict[str, ServiceInfo]: The online devices. The key is the serial
                number and the value is the service information.
        """
        return self.__context.get_online_service()

    def offline_devices(self) -> dict[str, ServiceInfo]:
        """Get the offline devices from the class Context.

        Returns:
            Dict[str, ServiceInfo]: The offline devices. The key is the serial
                number and the value is the service information.
        """
        return self.__context.get_offline_service()

    def get_service_info_for(self, serial_num: str) -> ServiceInfo | None:
        """Get the service information for a given serial number. If the
        serial number is not in the online list, it will return None.

        Args:
            serial_num (str): The serial number of the device.

        Returns:
            Optional[ServiceInfo]: The service information of the device or
                None if the device is not online.
        """
        services_data = self.__context.get_online_service()
        if serial_num in services_data:
            return services_data[serial_num]

    def connection_status_for_device(
        self,
        service_info: ServiceInfo,
    ) -> ConnectionInfoStatus:
        """Check the connection status for a given service, based on the
        current context.

        `ConnectionInfoStatus`:
        - `ConnectionInfoStatus.UPDATED`: The service information is up to
            date. Meaning that the service is online and the IP address is the
            same.
        - `ConnectionInfoStatus.CHANGED`: The service information has changed
            and the IP address is different.
        - `ConnectionInfoStatus.DOWN`: The service is offline.
        - `ConnectionInfoStatus.UNKNOWN`: The service is not at the context
                offline list, neither at the online list.

        Args:
            service_info (ServiceInfo): The service information.

        Returns:
            ConnectionInfoStatus: The connection status.
        """
        if service_info.serial_number in self.__context.get_offline_service():
            return ConnectionInfoStatus.DOWN

        if (
            service_info.serial_number
            not in self.__context.get_online_service()
        ):
            return ConnectionInfoStatus.UNKNOWN

        services_data = self.__context.get_online_service()
        service_ref = services_data[service_info.serial_number]

        if service_ref.ip == service_info.ip:
            return ConnectionInfoStatus.UPDATED

        return ConnectionInfoStatus.CHANGED

    def stop_discovery_listener(self) -> None:
        """Stop the ServiceBrowser and close the Zeroconf instance."""
        self.__session.stop()
