import logging
import subprocess
import warnings
from time import sleep

from device_manager.adb_gateway import AdbGateway, resolve_gateway
from device_manager.cli.qrcode_viewer import show_qr_window
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

    def __init__(
        self,
        subprocess_check_flag: bool = False,
        restart_adb_server: bool = False,
        gateway: AdbGateway | None = None,
    ) -> None:
        self.__subprocess_check_flag = subprocess_check_flag
        self._gateway = gateway
        active_gateway = self._get_gateway()
        if restart_adb_server:
            active_gateway.run(
                ['adb', 'kill-server'],
                check=self.__subprocess_check_flag,
            )
        self.__discovery = AdbConnectionDiscovery()
        active_gateway.run(
            ['adb', 'start-server'],
            check=self.__subprocess_check_flag,
        )
        self.__discovery.start()
        sleep(2)

    def _get_gateway(self) -> AdbGateway:
        return resolve_gateway(self._gateway, subprocess.run)

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
            ['adb', 'devices'],
            capture_output=True,
            text=True,
            check=subprocess_check_flag,
        )
        devices_lines = str(result.stdout).split('\n')
        for info_line in devices_lines:
            if comm_uri in info_line and 'offline' not in info_line:
                return True
        return False

    def available_devices(self) -> dict[str, ServiceInfo]:
        """Get the list of devices that are currently online.
        The dict is indexed by the serial number of the devices.

        Returns:
            Dict[str, ServiceInfo]: A dictionary of devices that are online.
        """
        return self.__discovery.online_devices()

    @staticmethod
    def device_pairing(timeout_s: float) -> bool:
        """Pairs a device via ADB using the QRCode window (`show_qr_window`)."""
        warnings.warn(
            'ConnectionManager.device_pairing is deprecated; use AdbPairing directly.',
            DeprecationWarning,
            stacklevel=2,
        )
        logger.warning(
            'ConnectionManager.device_pairing is deprecated; use AdbPairing directly.',
        )

        adb_pairing = AdbPairing()
        adb_pairing.start()
        show_qr_window(adb_pairing.qrcode_image)
        adb_pairing._context.wait_for_online_service(timeout=timeout_s)  # pyright: ignore[reportPrivateUsage]
        result = adb_pairing.pair_devices()
        adb_pairing.stop_pair_listener()
        return result

    def device_connect(self, serial_num: str) -> ServiceInfo | None:
        """Connects to a device using the serial number.

        Args:
            serial_num (str): The serial number of the device.

        Returns:
            Optional[ServiceInfo]: The service information of the device.
        """
        info = self.__discovery.get_service_info_for(serial_num)
        if info is None:
            logger.warning(
                'Device service not online or located: serial=%s',
                serial_num,
            )
        else:
            comm_uri = f'{info.ip}:{info.port}'
            result = self._get_gateway().run(
                ['adb', 'connect', comm_uri],
                capture_output=True,
                text=True,
                check=self.__subprocess_check_flag,
            )
            if f'failed to connect to {comm_uri}' in result.stdout:
                logger.warning(
                    'Failed to connect device: serial=%s uri=%s output=%s',
                    serial_num,
                    comm_uri,
                    result.stdout.strip(),
                )
            else:
                logger.info(
                    'Connected to device: serial=%s uri=%s',
                    serial_num,
                    comm_uri,
                )
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
    ) -> ServiceInfo | None:
        """Validate the connection status of a device and reconnect if
        necessary.

        Args:
            info (ServiceInfo): The service information of the device.

        Returns:
            Optional[ServiceInfo]: The service information of the device.
        """
        comm_uri = f'{info.ip}:{info.port}'
        if self.check_devices_adb_connection(comm_uri):
            return info
        return self.device_connect(info.serial_number)

    def close_discovery(self) -> None:
        """Close the discovery listener."""
        self.__discovery.stop_discovery_listener()
