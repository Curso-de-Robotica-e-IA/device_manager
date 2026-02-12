import logging
from typing import Optional

from time import sleep

from device_manager.connection.utils.mdns_context import (
    MDnsContext,
)
from device_manager.connection.utils.mdns_listener import (
    MDnsListener,
)
from device_manager.connection.utils.mdns_service import MdnsService

logger = logging.getLogger(__name__)


import subprocess

from device_manager.connection.utils.mdns_context import MDnsContext
from device_manager.connection.utils.mdns_listener import MDnsListener


class AdbConnectionDiscovery:
    """Restarts ADB and discovers Wi-Fi devices via mDNS.
        This class is responsible for restarting the ADB server and discovering
        devices that are available for connection over Wi-Fi using mDNS. It uses
        the `MDnsListener` to scan for services and updates the `MDnsContext`
        with the discovered devices.
        The discovery process involves killing the ADB server, waiting for a
        short period to ensure it has stopped, starting the ADB server again,
        and then waiting for it to initialize before scanning for devices.
        The discovered devices are categorized into online and pairing services
        based on their service type.
        
        Attributes:
            _context (MDnsContext): The context that holds the discovered services.
            _listener (MDnsListener): The listener that scans for mDNS services.

        Methods:
            discover: Restarts the ADB server and discovers devices via mDNS.
            get_online_devices: Retrieves the online devices from the context.
            get_pairing_devices: Retrieves the pairing devices from the context.
            get_service_info_for: Retrieves the service information for a given
                serial number.
    """

    def __init__(self) -> None:
        self._context = MDnsContext()
        self._listener = MDnsListener(self._context)

    def discover(self) -> MDnsContext:
        subprocess.run(["adb", "kill-server"], check=False)
        sleep(10)
        subprocess.run(["adb", "start-server"], check=False)
        sleep(50)
        self._listener.scan()

        return self._context
    
    def get_online_devices(self) -> MDnsContext:
        """Get the online devices from the class Context.

        Returns:
            Dict[str, ServiceInfo]: The online devices. The key is the serial
                number and the value is the service information.
        """
        return self._context.online_services
    
    def get_pairing_devices(self) -> MDnsContext:
        """Get the pairing devices from the class Context.

        Returns:
            Dict[str, ServiceInfo]: The pairing devices. The key is the serial
                number and the value is the service information.
        """
        return self._context.pairing_services

    def get_service_info_for(self, serial_num: str) -> Optional[MdnsService]:
        """Get the service information for a given serial number. If the
        serial number is not in the online list, it will return None.

        Args:
            serial_num (str): The serial number of the device.

        Returns:
            Optional[ServiceInfo]: The service information of the device or
                None if the device is not online.
        """
        return self._context.get_by_serial(serial_num)


if __name__ == "__main__":
    discovery = AdbConnectionDiscovery()
    services = discovery.discover()
    online_devices = discovery.get_online_devices()
    paring = discovery.get_pairing_devices()
    print("All devices:", services.services)
    print("Online devices:", online_devices)
    print("Paring devices:", paring)
