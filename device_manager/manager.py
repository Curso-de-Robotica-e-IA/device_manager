import logging
from collections import defaultdict
from subprocess import CompletedProcess
from types import TracebackType
from typing import Iterable, NamedTuple

from device_manager.adb_executor import execute_adb_command
from device_manager.connection.adb_pairing import AdbPairing
from device_manager.connection.device_connection import (
    DEFAULT_FIXED_PORT,
    DeviceConnection,
)
from device_manager.connection.strategies import get_connection_strategy
from device_manager.connection.utils.connection_type import ConnectionType
from device_manager.connection.utils.service_info import ServiceInfo
from device_manager.device_actions import DeviceActions
from device_manager.device_info import DeviceInfo
from device_manager.exceptions.errors import DeviceNotFoundError
from device_manager.ui_hierarchy import (
    NativeResidentUiBackend,
    UiHierarchyBackend,
)
from device_manager.utils.dm_warnings import check_adb_dependencies_version

logger = logging.getLogger(__name__)

DeviceObjects = NamedTuple(
    'DeviceObjects',
    [
        ('serial_number', str),
        ('device_info', DeviceInfo),
        ('device_actions', DeviceActions),
    ],
)


class DeviceManager:
    """Manages multiple ADB device connections and exposes per-device
    `DeviceInfo` and `DeviceActions` aggregates indexed by serial number.
    """

    def __init__(
        self,
        subprocess_check_flag: bool = False,
        fixed_port: int = DEFAULT_FIXED_PORT,
        check_dependencies: bool = True,
        connector: DeviceConnection | None = None,
        ui_backend: UiHierarchyBackend | None = None,
    ):
        if check_dependencies:
            check_adb_dependencies_version()
        self.subprocess_check = subprocess_check_flag
        self._devices_fixed_port = fixed_port
        self._ui_backend: UiHierarchyBackend = (
            ui_backend if ui_backend is not None else NativeResidentUiBackend()
        )
        self.connector = (
            connector
            if connector is not None
            else DeviceConnection(
                subprocess_check_flag=self.subprocess_check,
                fixed_port=self._devices_fixed_port,
            )
        )
        self.adb_pair: AdbPairing | None = None
        self._devices: dict[str, DeviceObjects] = {}
        self._endpoint_serial_cache: dict[str, str] = {}

    def __enter__(self) -> 'DeviceManager':
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        """Release underlying discovery and connection resources."""
        self.connector.close()

    def _register_device(self, serial: str) -> None:
        """Create and register a DeviceObjects aggregate for `serial`."""
        if serial not in self._devices:
            gateway = getattr(self.connector, '_gateway', None)
            dev_info = DeviceInfo(
                self.connector,
                serial,
                subprocess_check_flag=self.subprocess_check,
                gateway=gateway,
                ui_backend=self._ui_backend,
            )
            dev_actions = DeviceActions(
                self.connector,
                serial,
                subprocess_check_flag=self.subprocess_check,
                gateway=gateway,
                ui_backend=self._ui_backend,
            )
            self._devices[serial] = DeviceObjects(
                serial_number=serial,
                device_info=dev_info,
                device_actions=dev_actions,
            )

    def __getitem__(
        self,
        serial_number: str,
    ) -> tuple[DeviceInfo, DeviceActions]:
        """Get the device information and actions associated with a
        serial number.

        Args:
            serial_number (str): The serial number of the device.

        Returns:
            Tuple[DeviceInfo, DeviceActions]: The device information
            and actions associated with the serial number.
        """
        device = self._devices.get(serial_number)
        if device is None:
            raise DeviceNotFoundError(
                f'Device {serial_number!r} was not found'
            )
        return device.device_info, device.device_actions

    def __len__(self) -> int:
        """Returns the number of devices currently managed by this class."""
        return len(self._devices)

    def __iter__(self) -> Iterable[DeviceObjects]:
        """Iterates over the devices being managed by this class.
        Returns an iterator with a tuple containing the device serial number,
        device information and device actions.

        Supports usage of the `for` loop to iterate over the devices."""
        return iter(self._devices.values())

    def __delitem__(self, key: str) -> None:
        """Removes a device from the manager.

        Args:
            key (str): The serial number of the device to remove.
        """
        del self._devices[key]

    def __contains__(self, key: str) -> bool:
        """Checks if a device with the provided serial number is managed.

        Args:
            key (str): The serial number of the device to check.

        Returns:
            bool: True if the device is managed, False otherwise.
        """
        return key in self._devices

    def __repr__(self) -> str:
        """Returns a string representation of the class.

        Returns:
            str: The string representation of the class.
        """
        return f'device_manager.DeviceManager({len(self)} devices: {list(self._devices.keys())})'  # noqa

    def __str__(self) -> str:
        return (
            f'DeviceManager({len(self)} devices: {list(self._devices.keys())})'  # noqa
        )

    @property
    def connected_devices(self) -> list[str]:
        """Returns the list of serial numbers of the devices that are
        currently connected and managed by this instance.
        """
        return list(self._devices.keys())

    def _resolve_endpoint_serial(self, endpoint: str) -> str:
        cached = self._endpoint_serial_cache.get(endpoint)
        if cached is not None:
            return cached
        try:
            res = execute_adb_command(
                command='getprop ro.serialno',
                comm_uris=[endpoint],
                shell=True,
                capture_output=True,
                gateway=getattr(self.connector, '_gateway', None),
            )
            serial = (res.stdout or '').strip() if res.returncode == 0 else ''
            if serial:
                self._endpoint_serial_cache[endpoint] = serial
                return serial
        except Exception:  # noqa: S110
            pass
        return endpoint

    def _endpoint_to_serial_map(
        self,
        adb_states: dict[str, str] | None = None,
    ) -> dict[str, str]:
        mapping: dict[str, str] = dict(self._endpoint_serial_cache)
        for serial in self.connector.connection_info.keys():
            svc = self.connector.connection_info.get(serial)
            if svc is not None and svc.connection == ConnectionType.WIFI:
                mapping[f'{svc.ip}:{svc.port}'] = serial
                mapping[f'{svc.ip}:{self._devices_fixed_port}'] = serial
        for (
            serial,
            svc,
        ) in self.connector.connection.available_devices().items():
            mapping[f'{svc.ip}:{svc.port}'] = serial
            mapping[f'{svc.ip}:{self._devices_fixed_port}'] = serial
        if adb_states:
            for dev_id, state in adb_states.items():
                if (
                    state == 'device'
                    and ':' in dev_id
                    and dev_id not in mapping
                ):
                    mapping[dev_id] = self._resolve_endpoint_serial(dev_id)
        return mapping

    @property
    def available_devices(self) -> list[str]:
        """Returns `connected_devices` plus all authorized devices in `adb devices`
        (both USB and Wi-Fi), resolved to serial numbers and deduplicated.
        """
        states = self.connector.list_adb_device_states()
        endpoint_map = self._endpoint_to_serial_map(states)
        result: dict[str, None] = dict.fromkeys(self._devices.keys())
        for dev_id, state in states.items():
            if state == 'device':
                canonical = endpoint_map.get(dev_id, dev_id)
                result[canonical] = None
        return list(result.keys())

    @property
    def unauthorized_devices(self) -> list[str]:
        """Returns devices reported as `unauthorized` by `adb devices`."""
        states = self.connector.list_adb_device_states()
        endpoint_map = self._endpoint_to_serial_map()
        return [
            endpoint_map.get(dev_id, dev_id)
            for dev_id, state in states.items()
            if state == 'unauthorized'
        ]

    @property
    def visible_devices(self) -> list[str]:
        """Returns `available_devices` union `unauthorized_devices` union
        Wi-Fi devices discovered via mDNS, deduplicated.
        """
        result: dict[str, None] = dict.fromkeys(self.available_devices)
        for dev_id in self.unauthorized_devices:
            result[dev_id] = None
        mdns_devices = self.connector.connection.available_devices()
        for serial in mdns_devices:
            result[serial] = None
        return list(result.keys())

    def connect_devices(self, *serial_numbers: str) -> list[str]:
        """
        Connects to the given devices and creates their objects.
        This method will check the connection type of each device and connect
        accordingly. For USB devices, it will check if they are already
        connected and if not, it will connect them.
        Args:
            *serial_numbers (str): The serial numbers of the devices to connect.

        Returns:
            List of successfully connected serial numbers.
        """

        visibles_devices = self.connector.visible_devices()

        visible_by_serial: dict[str, ServiceInfo] = {}
        for service in visibles_devices:
            existing = visible_by_serial.get(service.serial_number)
            # Prioritize USB over Wi-Fi when the same device is visible on both
            if existing is None or service.connection == ConnectionType.USB:
                visible_by_serial[service.serial_number] = service

        adb_states = self.connector.list_adb_device_states()
        endpoint_map = self._endpoint_to_serial_map(adb_states)
        serial_to_active_tcp: dict[str, str] = {}
        for dev_id, state in adb_states.items():
            if state == 'device' and ':' in dev_id:
                mapped_serial = endpoint_map.get(dev_id, dev_id)
                serial_to_active_tcp[mapped_serial] = dev_id

        serials_by_type: dict[ConnectionType, list[str]] = defaultdict(list)
        connected_serials: list[str] = []

        for raw_serial in serial_numbers:
            serial = endpoint_map.get(raw_serial, raw_serial)
            service = visible_by_serial.get(serial)

            # Priority 1: USB
            if (
                service is not None
                and service.connection == ConnectionType.USB
            ):
                existing_info = self.connector.connection_info.get(serial)
                if existing_info is None:
                    self.connector.connection_info.add(serial, service)
                elif existing_info.connection == ConnectionType.WIFI:
                    self.connector.connection_info.edit(serial, service)
                serials_by_type[ConnectionType.USB].append(serial)
                continue

            # Priority 2: Already-connected Wi-Fi (ip:port in `adb devices`)
            active_endpoint = serial_to_active_tcp.get(serial)
            if active_endpoint is not None:
                host, port_str = active_endpoint.rsplit(':', 1)
                if port_str.isdigit():
                    tcp_svc = ServiceInfo(
                        serial_number=serial,
                        ip=host,
                        port=int(port_str),
                        connection=ConnectionType.WIFI,
                    )
                    if self.connector.connection_info.get(serial) is None:
                        self.connector.connection_info.add(serial, tcp_svc)
                    connected_serials.append(serial)
                    continue

            # Priority 3: mDNS Wi-Fi discovery
            if service is not None:
                serials_by_type[service.connection].append(serial)
                continue

            logger.warning(
                'Requested device not visible for connection: serial=%s',
                serial,
            )

        for connection_type, serials in serials_by_type.items():
            strategy = get_connection_strategy(connection_type)
            connected_serials.extend(strategy.connect(self.connector, serials))

        for serial in connected_serials:
            self._register_device(serial)

        logger.info(
            'Connected devices: requested=%d connected=%s',
            len(serial_numbers),
            connected_serials,
        )
        return connected_serials

    def disconnect_devices(self, *serial_number: str) -> bool:
        """Disconnects the devices with the provided serial numbers.
        This method will stop the connection to the devices and remove
        the associated DeviceInfo and DeviceActions objects from the
        internal registry.

        Returns:
            bool: True if the disconnection was successful, False otherwise.
        """
        serial_number_list = list(serial_number)
        success_op = self.connector.stop_connection(serial_number_list)
        if success_op:
            for serial in serial_number_list:
                sbn = self.connector.connection_info.get(serial)
                if sbn is None:  # Should Be None
                    self._devices.pop(serial, None)
            logger.info('Disconnected devices: serials=%s', serial_number_list)
        else:
            logger.warning(
                'Failed to disconnect all requested devices: serials=%s',
                serial_number_list,
            )
        return success_op

    def get_device_info(self, serial_number: str) -> DeviceInfo | None:
        """Retrieves the device information associated with a given
        serial number.

        Args:
            serial_number (str): The serial number of the device.

        Returns:
            DeviceInfo: The device information object.
        """
        device = self._devices.get(serial_number)
        return device.device_info if device is not None else None

    def get_device_actions(self, serial_number: str) -> DeviceActions | None:
        """Retrieves the device actions associated with a given serial number.

        Args:
            serial_number (str): The serial number of the device.

        Returns:
            DeviceActions: The device actions object.
        """
        device = self._devices.get(serial_number)
        return device.device_actions if device is not None else None

    def execute_adb_command(
        self,
        command: str,
        comm_uris: list[str] | None = None,
        shell: bool = True,
        subprocess_check_flag: bool = False,
        capture_output: bool = False,
        **kwargs: str,
    ) -> CompletedProcess[str]:
        """Executes a custom adb command on all connected devices.
        Additional arguments and keyword arguments can be provided to
        customize the command, which will be added to the end of the command
        string.

        Passing a command such as `pull remote local` will produce the
        following command: `adb pull remote local`, applied with the
        `-s` flag for each device.

        You can execute a command on a set of specific devices by providing
        the serial numbers as additional arguments.

        Args:
            command (str): The adb command to execute.
            comm_uris (Optional[List[str]]): The serial numbers of the
                devices to execute the command on. Defaults to None.
                In this case, the command will be executed on all
                connected devices.
            shell (bool, optional): A flag to indicate if the command should
            subprocess_check_flag (bool, optional): A flag to check if the
                subprocess execution was successful, passed to the subprocess
                `check` argument. Defaults to False.
                Check the subprocess documentation for more information.
            capture_output (bool, optional): A flag to capture the output of
                the command. Defaults to False.
            **kwargs: Additional arguments to be added to the command.

        Returns:
            CompletedProcess: The result of the command execution.
        """
        uris: list[str] | None = comm_uris
        if comm_uris is None:
            uris = []
            for serial in self._devices:
                service_info = self.connector.connection_info.get(serial)
                if service_info is None:
                    continue

                if service_info.connection == ConnectionType.USB:
                    uris.append(serial)
                else:
                    uris.append(f'{service_info.ip}:{service_info.port}')

        if not isinstance(uris, (list, tuple)):
            raise TypeError(
                f'comm_uris must be a list, tuple or None, got {type(comm_uris)}',  # noqa
            )
        return execute_adb_command(
            command=command,
            comm_uris=uris,
            shell=shell,
            subprocess_check_flag=subprocess_check_flag,
            capture_output=capture_output,
            gateway=getattr(self.connector, '_gateway', None),
            **kwargs,  # pyright: ignore[reportArgumentType]
        )

    def adb_pairing_instance(
        self,
        service_name: str = 'robot_celular',
        service_regex_filter: str | None = None,
        subprocess_check_flag: bool = False,
    ) -> None:
        """Creates an instance of the AdbPairing class. This instance will
        be available at the `adb_pair` attribute of this class.
        All of the parameters are passed to the AdbPairing constructor.

        Args:
            service_name (str, optional): The name of the service in the
                network. Defaults to 'robot_celular'.
            service_regex_filter (Optional[str], optional): The filter that
                will be applied to the mDNSListener operations. Defaults to
                    None.
            subprocess_check_flag (bool, optional): A flag to check if the
                subprocess execution was successful, passed to the subprocess
                `check` argument. Defaults to False.
                Check the subprocess documentation for more information.
        """
        self.adb_pair = AdbPairing(
            service_name=service_name,
            service_regex_filter=service_regex_filter,
            subprocess_check_flag=subprocess_check_flag,
        )

    def is_connected(self, serial_number: str) -> bool:
        """Checks if a device with the provided serial number is connected.

        Args:
            serial_number (str): The serial number of the device.

        Returns:
            bool: True if the device is connected, False otherwise.
        """
        return self.connector.is_connected(serial_number)

    def clear(self) -> None:
        """Clears the internal device registry, removing all devices."""
        self._devices.clear()

    def load_connected_usb_devices(self) -> None:
        """Detects already connected USB devices and registers them.

        Prioritizes USB over Wi-Fi: if a serial was previously registered over
        Wi-Fi, its `ServiceInfo` is upgraded to USB.
        """
        usb_devices = self.connector.usb_scanner.list_connected_devices()

        for service in usb_devices:
            serial = service.serial_number
            existing = self.connector.connection_info.get(serial)
            if existing is None:
                self.connector.connection_info.add(serial, service)
            elif existing.connection == ConnectionType.WIFI:
                self.connector.connection_info.edit(serial, service)

            self._register_device(serial)

        if usb_devices:
            logger.info(
                'Loaded connected USB devices: serials=%s',
                [service.serial_number for service in usb_devices],
            )
