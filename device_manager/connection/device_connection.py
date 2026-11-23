import logging
import subprocess
from types import TracebackType

from device_manager.adb_gateway import AdbGateway, resolve_gateway
from device_manager.components.object_manager import ObjectManager
from device_manager.connection.connection_manager import (
    ConnectionManager,
)
from device_manager.connection.strategies import get_connection_strategy
from device_manager.connection.utils.mdns_context import (
    ServiceInfo,
)
from device_manager.connection.utils.usb_device_scanner import (
    UsbDeviceScanner,
)
from device_manager.exceptions.errors import (
    DeviceDisconnectedError,
    DeviceNotFoundError,
)

DEFAULT_FIXED_PORT = 5555
MAX_CONNECTION_RETRIES = 5

logger = logging.getLogger(__name__)


class DeviceConnection:
    """Manages ADB device connections, validation, URI resolution, and server
    lifecycle.
    """

    def __init__(
        self,
        subprocess_check_flag: bool = False,
        fixed_port: int = DEFAULT_FIXED_PORT,
        gateway: AdbGateway | None = None,
    ):
        self.__subprocess_check_flag = subprocess_check_flag
        self._gateway = gateway
        self.connection = ConnectionManager(
            subprocess_check_flag=self.__subprocess_check_flag,
            gateway=self._gateway,
        )
        self.usb_scanner = UsbDeviceScanner(
            subprocess_check_flag=self.__subprocess_check_flag,
            gateway=self._gateway,
        )
        self.connection_info: ObjectManager[ServiceInfo] = ObjectManager()
        self.fixed_port = fixed_port

    def _get_gateway(self) -> AdbGateway:
        return resolve_gateway(self._gateway, subprocess.run)

    def __enter__(self) -> 'DeviceConnection':
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()

    def visible_devices(self) -> list[ServiceInfo]:
        """Returns a list of visible devices in the network.

        Returns:
            List[ServiceInfo]: A list of visible devices in the network.
        """
        available_devices = self.connection.available_devices()
        wifi_devices = list(available_devices.values())
        usb_devices = self.usb_scanner.list_connected_devices()
        return wifi_devices + usb_devices

    def close(self):
        """
         This method terminates any ongoing device discovery process managed by
        the `connection_manager`. It ensures that resources related to device
        discovery are released properly.
        """

        self.connection.close_discovery()

    def is_connected(
        self,
        serial_number: str,
        devices_connected: str | None = None,
    ) -> bool:
        """Check if the device is connected to the host.

        Args:
            serial_number (str): The serial number of the device to check.

        Returns:
            bool: True if the device is connected, False otherwise.
        """
        result = False
        if devices_connected is None:
            devices_connected = self._adb_devices_output()

        device = self.connection_info.get(serial_number)
        if device is None:
            return False

        strategy = get_connection_strategy(device.connection)
        substr = strategy.format_adb_device_entry(device)

        if substr in devices_connected:
            result = True
        return result

    def check_connections(self) -> bool:
        """
        This method checks the status of the current connections and returns
        True if all devices are connected and updated. If any device is not
        connected or updated, the method returns False.

        Returns:
            bool: True if all devices are connected and updated, False
                otherwise.
        """

        devices_connected = self._adb_devices_output()
        logger.debug('Connected ADB devices:\n%s', devices_connected)
        serial_numbers = self.connection_info.keys()
        if len(serial_numbers) == 0:
            return False
        all_connected = [False] * len(serial_numbers)
        for idx, serial_number in enumerate(serial_numbers):
            result = self.is_connected(
                serial_number=serial_number,
                devices_connected=devices_connected,
            )
            all_connected[idx] = result
        return all(all_connected)

    def build_comm_uri(self, serial_number: str) -> str:
        """
        This method constructs a communication URI for the specified device
        using the IP address and port number stored in the `connection_info`
        attribute.

        Args:
            serial_number (str): The serial number of the device to connect to.

        Returns:
            str: The communication URI in the format `ip:port` or serial number.
        """

        device = self.connection_info.get(serial_number)
        if device is None:
            raise DeviceNotFoundError('device was not found')
        strategy = get_connection_strategy(device.connection)
        return strategy.build_comm_uri(device)

    def establish_first_connection(
        self,
        device_serial_number: str,
        max_retries: int = MAX_CONNECTION_RETRIES,
    ) -> bool:
        """Attempts to establish an ADB connection with the specified device.

        Args:
            device_serial_number (str): The serial number of the device to
                connect to.
            max_retries (int, optional): The maximum number of connection
                attempts. Defaults to 5.

        Returns:
            bool: True if the connection is successfully established, False
                otherwise.
        """
        success = False
        connection = None
        for attempt in range(1, max_retries + 1):
            if not success:
                logger.info(
                    'Trying to connect to %s (attempt %d/%d)...',
                    device_serial_number,
                    attempt,
                    max_retries,
                )
                connection = self.connection.device_connect(
                    device_serial_number,
                )

            if connection is not None:
                success = True
            else:
                logger.warning(
                    'ADB connection attempt failed: serial=%s attempt=%d/%d',
                    device_serial_number,
                    attempt,
                    max_retries,
                )

        if connection is not None:
            if self.connection_info.get(device_serial_number) is not None:
                self.connection_info.remove(device_serial_number)
            self.connection_info.add(connection.serial_number, connection)
            connection_port = self.connection_info.get(connection.serial_number)
            if (
                connection_port is not None and connection_port.port != self.fixed_port
            ):
                self.__fix_adb_port(connection.serial_number)
            return True
        return False

    def validate_connection(
        self,
        serial_number: str,
        force_reconnect: bool = False,
        raise_on_error: bool = False,
    ) -> bool:
        """Validates the current connection with the specified device.

        If `force_reconnect=True` and the connection is invalid, attempts to
        reconnect. If `raise_on_error=True` and validation fails, raises
        `DeviceDisconnectedError`.
        """
        device = self.connection_info.get(serial_number)
        if device is None:
            logger.debug('No devices currently connected for %s', serial_number)
            if raise_on_error:
                raise DeviceDisconnectedError(
                    f'No devices currently connected for {serial_number}'
                )
            return False

        strategy = get_connection_strategy(device.connection)
        is_valid = strategy.validate(
            self,
            device,
            force_reconnect=force_reconnect,
        )
        if not is_valid and raise_on_error:
            raise DeviceDisconnectedError(
                f'Failed to validate connection for device {serial_number}'
            )
        return is_valid

    def connect_all_devices(self) -> None:
        """Connects to all devices in the `connection_info` attribute.
        This method expects that all the devices added to the `connection_info`
        attribute are available and with the correct port set."""
        serial_numbers = self.connection_info.keys()
        for serial_number in serial_numbers:
            self.__connect_with_fix_port(serial_number)

    def start_connection(self, selected_devices: list[str]) -> list[str]:
        """Starts the connection process for the selected devices.
        This method establishes a first connection with the selected devices,
        changing the ADB port the `fixed_port` if necessary. After that, it
        disconnects the current connection, and then reconnects to all devices
        in the `connection_info` attribute.

        Args:
            selected_devices (List[str]): A list of serial numbers of the
                devices to connect to.

        Returns:
            List[str]: A list of serial numbers of the devices that were
                successfully connected and updated.
        """
        connecteds: list[str] = []
        for selected_serial_num in selected_devices:
            self.establish_first_connection(selected_serial_num)
        self.disconnect()
        self.connect_all_devices()
        for selected_serial_num in selected_devices:
            if self.is_connected(selected_serial_num):
                connecteds.append(selected_serial_num)

        return connecteds

    def stop_connection(self, selected_devices: list[str]) -> bool:
        """Disconnects the selected devices from the host.
        This method runs the ADB command to disconnect the selected devices
        from the host. It checks if the devices are selected and raises a
        ValueError if no devices are selected. It returns True if all devices
        are disconnected successfully, and False otherwise.

        Args:
            selected_devices (List[str]): A list of serial numbers of the
                devices to disconnect from the host.

        Raises:
            ValueError: If no devices are selected to disconnect.

        Returns:
            bool: True if all devices are disconnected successfully, False
                otherwise.
        """
        if len(selected_devices) == 0:
            raise ValueError('No devices selected to disconnect')
        all_ops: list[bool] = [False] * len(selected_devices)
        for idx, serial_num in enumerate(selected_devices):
            selected_uri = self.build_comm_uri(serial_num)
            result = self._get_gateway().run(
                ['adb', 'disconnect', selected_uri],
                check=self.__subprocess_check_flag,
                capture_output=True,
                text=True,
            )
            if result.stdout == f'disconnected {selected_uri}\n':
                all_ops[idx] = True
                self.connection_info.remove(serial_num)

        if all(all_ops):
            return True
        return False

    def __fix_adb_port(self, serial_number: str) -> None:
        """Fix the ADB port by setting it to the `fixed_port` attribute value.

        This method validates the current connection and if valid, runs the
        ADB command to set the device's port to `fixed_port`.
        """

        if self.validate_connection(serial_number):
            comm_uri = self.build_comm_uri(serial_number)
            self._get_gateway().run(
                ['adb', '-s', comm_uri, 'tcpip', f'{self.fixed_port}'],
                check=self.__subprocess_check_flag,
            )
            device = self.connection_info.get(serial_number)
            if device is None:
                raise ValueError("device not found")
            device.port = self.fixed_port

    def __connect_with_fix_port(self, serial_number: str) -> None:
        """Reconnect using the fixed ADB port.

        This method establishes a new ADB connection using the fixed port
        attribute.
        """
        device = self.connection_info.get(serial_number)
        if device is None:
            raise ValueError("device was not found")
        self._get_gateway().run(
            ['adb', 'connect', f'{device.ip}:{self.fixed_port}'],
            check=self.__subprocess_check_flag,
        )

    @staticmethod
    def disconnect(
        subprocess_check_flag: bool = False,
    ) -> None:
        """
        This method executes an ADB command to kill the ADB server, effectively
        disconnecting the current session with all devices.

        Args:
            subprocess_check_flag (bool, optional): A flag to check if the
                subprocess execution was successful, passed to the subprocess
                `check` argument. Defaults to False.
                Check the subprocess documentation for more information.
        """
        subprocess.run(
            ['adb', 'kill-server'],
            check=subprocess_check_flag,
        )
    
    def _adb_devices_output(self) -> str:
        """This method executes the ADB command to list connected devices and
        returns the output as a string.
        
         Returns:
             str: The output of the ADB command listing connected devices.
         """
        return self._get_gateway().run(
            ['adb', 'devices'],
            capture_output=True,
            text=True,
            check=self.__subprocess_check_flag,
        ).stdout
