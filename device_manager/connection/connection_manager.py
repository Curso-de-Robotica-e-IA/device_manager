import subprocess
from typing import Dict, List
import logging
from time import time, sleep
from device_manager.connection.adb_connection_discovery import (
    AdbConnectionDiscovery,
)
from device_manager.connection.utils.mdns_service import MdnsService
from device_manager.connection.adb_pairing import AdbPairing

logger = logging.getLogger(__name__)


class ConnectionManager:
    """High-level manager for ADB Wi-Fi connections.
    
    This class provides methods to discover devices, connect to them, and
    check their connection status. It uses the AdbConnectionDiscovery class to
    discover devices via mDNS and the AdbPairing class to handle device pairing.

    Args:
        subprocess_check_flag (bool, optional): Indicates if the subprocess
            must raise an exception if the command fails. Defaults to False.

    Methods:
        discover_devices: Discover devices using mDNS.
        connect: Connect to a device using its service information.
        device_pairing: Pair a device using the ADB pair code method.
        device_connect: Connect to a device using its serial number.
        check_devices_adb_connection: Check if a device is connected to the ADB server.
    """

    def __init__(self, subprocess_check_flag: bool = False) -> None:
        self._discovery = AdbConnectionDiscovery()
        self._subprocess_check_flag = subprocess_check_flag
        self.devices = self.discover_devices()

    def discover_devices(self) -> List[MdnsService]:
        context = self._discovery.discover()
        return context.services

    def connect(self, service: MdnsService) -> None:
        subprocess.run(
            ["adb", "connect", f"{service.ip}:{service.port}"],
            check=True,
        )

    def device_pairing(timeout_s: float) -> bool:
        """Pairs a device using the ADB pair code method. It waits for a device to be available for pairing and then attempts to pair with it.

        Args:
            timeout_s (float): The maximum time to wait for the device to
            be paired.

        Returns:
            bool: True if the device was paired, False otherwise.
        """
        logger.warning(
            msg="This method is being deprecated. Check the documentation on how to pair devices.",  # noqa
        )
        adb_pairing = AdbPairing()
        start_time = time()
        while (
            not adb_pairing.has_device_to_pairing()
            and (time() - start_time) <= timeout_s
        ):
            sleep(0.1)
        result = adb_pairing.pair_devices()
        return result

    def device_connect(self, serial_num: str) -> MdnsService | None:
        """Connects to a device using the serial number.

        Args:
            serial_num (str): The serial number of the device.

        Returns:
            Optional[ServiceInfo]: The service information of the device.
        """
        info = self._discovery.get_service_info_for(serial_num)
        if info is None:
            logger.warning("Device service not online or located")
        else:
            comm_uri = f"{info.ip}:{info.port}"
            result = subprocess.run(
                ["adb", "connect", comm_uri],
                capture_output=True,
                text=True,
                check=self._subprocess_check_flag,
            )
            if f"failed to connect to {comm_uri}" in result.stdout:
                logger.warning("Failed to connect device")
        return info
   
    @staticmethod
    def check_devices_adb_connection(
        comm_uri: str,
        subprocess_check_flag: bool = False,
    ) -> bool:
        """Check if the device is connected to the adb server.
        A device is considered as connected if it does not appear
        as `offline` in the output of the `adb devices` command.

        Args:
            comm_uri (string): The communication URI of the device.
            subprocess_check_flag (bool, optional): A flag to check if the
                subprocess execution was successful, passed to the subprocess
                `check` argument. Defaults to False.
                Check the subprocess documentation for more information.

        Returns:
            bool: True if the device is connected, False otherwise.
        """
        result = subprocess.run(
            ["adb", "devices"],
            capture_output=True,
            text=True,
            check=subprocess_check_flag,
        )
        devices_lines = str(result.stdout).split("\n")
        for info_line in devices_lines:
            if comm_uri in info_line and "offline" not in info_line:
                return True
        return False


class ConnectionManagerSingleton(ConnectionManager):
    """Singleton class to manage the ConnectionManager instance."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ConnectionManagerSingleton, cls).__new__(cls)
        return cls._instance

if __name__ == "__main__":
    manager = ConnectionManager()
    devices = manager.discover_devices()
    print("Discovered devices:")
    for d in devices:
        print(d)