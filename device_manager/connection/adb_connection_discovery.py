import weakref
from contextlib import contextmanager
from typing import Dict, Optional

from zeroconf import ServiceBrowser, Zeroconf

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
    MDnsListener,
)


class AdbConnectionDiscovery:
    """Class to discover the devices connected to the ADB server using mDNS.
    It uses the Zeroconf library to listen to the mDNS services, and the
    MDnsListener class to update the service context with the service
    information found by the Zeroconf instance.

    Properties:
        service_browser_started (bool): Check if the ServiceBrowser has been
            started.
        browser (Optional[ServiceBrowser]): The actual ServiceBrowser instance.
        zeroconf_status (bool): Check if the Zeroconf instance is active.

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

    def __init__(self):
        self.__started = False
        self.__service_re_filter = DEFAULT_REGEX_FILTER
        self.__service_type = CONNECT_SERVICE_TYPE
        self.__zeroconf: Optional[Zeroconf] = None
        self.__finalize: Optional[weakref.finalize] = None
        self.__browser: Optional[ServiceBrowser] = None
        self.__context = MDnsContext()

    def start(self) -> None:
        """Start the ServiceBrowser to listen to the mDNS services.
        """
        if not self.__started:
            self.__zeroconf = Zeroconf()
            self.__browser = ServiceBrowser(
                self.__zeroconf,
                self.__service_type,
                MDnsListener(
                    self.__context,
                    self.__service_re_filter,
                    self.__service_type,
                ),
            )

            def atexit() -> None:
                """Callback function to update the __started attribute and
                the __browser attribute, once the Zeroconf service has been
                finalized."""
                print("Zeroconf finalized")
                self.__browser = None
                self.__started = False

            self.__finalize = weakref.finalize(
                self.__zeroconf,
                atexit,
            )
            self.__started = True

    @contextmanager
    def start_discovery_listener(self):
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
        return self.__started

    @property
    def browser(self) -> Optional[ServiceBrowser]:
        """Returns the actual ServiceBrowser instance, if it exists.

        Returns:
            ServiceBrowser: The ServiceBrowser instance.
        """
        return self.__browser

    @property
    def zeroconf_status(self) -> bool:
        """Check if the Zeroconf instance is active.

        Returns:
            bool: True if the Zeroconf instance is active, False otherwise.
        """
        if self.__finalize is None:
            return False
        return self.__finalize.alive

    def online_devices(self) -> Dict[str, ServiceInfo]:
        """Get the online devices from the class Context.

        Returns:
            Dict[str, ServiceInfo]: The online devices. The key is the serial
                number and the value is the service information.
        """
        return self.__context.get_online_service()

    def offline_devices(self) -> Dict[str, ServiceInfo]:
        """Get the offline devices from the class Context.

        Returns:
            Dict[str, ServiceInfo]: The offline devices. The key is the serial
                number and the value is the service information.
        """
        return self.__context.get_offline_service()

    def get_service_info_for(self, serial_num: str) -> Optional[ServiceInfo]:
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

        if service_info.serial_number not in self.__context.get_online_service():  # noqa
            return ConnectionInfoStatus.UNKNOWN

        services_data = self.__context.get_online_service()
        service_ref = services_data[service_info.serial_number]

        if service_ref.ip == service_info.ip:
            return ConnectionInfoStatus.UPDATED

        return ConnectionInfoStatus.CHANGED

    def stop_discovery_listener(self) -> None:
        """Stop the ServiceBrowser and close the Zeroconf instance.
        """
        self.__zeroconf.close()
