import logging
import subprocess
from time import sleep, time
from typing import Dict, Optional

from device_manager.connection.adb_connection_discovery import (
    AdbConnectionDiscovery,
)
from device_manager.connection.adb_pairing import AdbPairing
from device_manager.connection.utils.connection_status import (
    ConnectionInfoStatus,
)
from device_manager.connection.utils.service_info import ServiceInfo

logger = logging.getLogger(__name__)


class ConnectionManager:
    # Connection Manager has been developed based in to code available on
    # https://github.com/openatx/adbutils/issues/111#issuecomment-2094694894

    __start_discovery = True

    def __init__(
        self,
        subprocess_check_flag: bool = False,
    ) -> None:
        self.__subprocess_check_flag = subprocess_check_flag
        if self.__start_discovery:
            subprocess.run(
                ["adb", "kill-server"],
                check=self.__subprocess_check_flag,
            )
            self.__discovery = AdbConnectionDiscovery()
            subprocess.run(
                ["adb", "start-server"],
                check=self.__subprocess_check_flag,
            )
            self.__discovery.start()
            sleep(2)
        self.__start_discovery = False

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

    def available_devices(self) -> Dict[str, ServiceInfo]:
        """Get the list of devices that are currently online.
        The dict is indexed by the serial number of the devices.

        Returns:
            Dict[str, ServiceInfo]: A dictionary of devices that are online.
        """
        return self.__discovery.online_devices()

    @staticmethod
    def device_pairing(timeout_s: float) -> bool:
        """Pairs a device via ADB using the QRCode method.
        :warning: The user must close the QRCode window shown by the
        method `qrcode_cv_window_show` to continue the execution of the
        script.

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
        adb_pairing.start()
        adb_pairing._qrcode.qrcode_cv_window_show()
        start_time = time()
        while (
            not adb_pairing.has_device_to_pairing()
            and (time() - start_time) <= timeout_s
        ):
            sleep(0.1)
        result = adb_pairing.pair_devices()
        adb_pairing.stop_pair_listener()
        return result

    def device_connect(self, serial_num: str) -> Optional[ServiceInfo]:
        """Connects to a device using the serial number.

        Args:
            serial_num (str): The serial number of the device.

        Returns:
            Optional[ServiceInfo]: The service information of the device.
        """
        info = self.__discovery.get_service_info_for(serial_num)
        if info is None:
            logger.warning("Device service not online or located")
        else:
            comm_uri = f"{info.ip}:{info.port}"
            result = subprocess.run(
                ["adb", "connect", comm_uri],
                capture_output=True,
                text=True,
                check=self.__subprocess_check_flag,
            )
            if f"failed to connect to {comm_uri}" in result.stdout:
                logger.warning("Failed to connect device")
        return info

    def check_wireless_adb_service_for(
        self,
        info: ServiceInfo,
    ) -> ConnectionInfoStatus:
        """Check the connection status of a device.

        Args:
            info (ServiceInfo): The service information of the device.

        Returns:
            ConnectionInfoStatus: The connection status of the device.
        """
        return self.__discovery.connection_status_for_device(info)

    def validate_and_reconnect_device(
        self,
        info: ServiceInfo,
    ) -> Optional[ServiceInfo]:
        """Validate the connection status of a device and reconnect if
        necessary.

        Args:
            info (ServiceInfo): The service information of the device.

        Returns:
            Optional[ServiceInfo]: The service information of the device.
        """
        comm_uri = f"{info.ip}:{info.port}"
        if self.check_devices_adb_connection(comm_uri):
            return info
        return self.device_connect(info.serial_number)

    def close_discovery(self) -> None:
        """Close the discovery listener."""
        self.__discovery.stop_discovery_listener()


class ConnectionManagerSingleton(ConnectionManager):
    """Singleton class to manage the ConnectionManager instance."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ConnectionManagerSingleton, cls).__new__(cls)
        return cls._instance
