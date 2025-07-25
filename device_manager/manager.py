from subprocess import CompletedProcess
from typing import Iterable, List, NamedTuple, Optional, Tuple

from device_manager.adb_executor import execute_adb_command
from device_manager.components.object_manager import ObjectManager
from device_manager.connection.adb_pairing import AdbPairing
from device_manager.connection.device_connection import (
    DEFAULT_FIXED_PORT,
    DeviceConnection,
)
from device_manager.device_actions import DeviceActions
from device_manager.device_info import DeviceInfo
from device_manager.utils.dm_warnings import check_adb_dependencies_version

check_adb_dependencies_version()

DeviceObjects = NamedTuple(
    'DeviceObjects',
    [
        ('serial_number', str),
        ('device_info', DeviceInfo),
        ('device_actions', DeviceActions),
    ],
)


class DeviceManager:
    """This class is able to manage multiple device connections, storing
    each of their reference internally. It is able to retrieve the associated
    `DeviceInfo` and `DeviceAction` for each device, by accessing this
    class as a dict, using the device serial used for connection as key.

    Args:
        subprocess_check_flag (bool, optional): A flag to check if the
            subprocess execution was successful, passed to the subprocess
            `check` argument. Defaults to False.
            Check the subprocess documentation for more information.
        fixed_port (int, optional): The fixed port to be used by the devices.
            Defaults to DEFAULT_FIXED_PORT.

    Attributes:
        `connected_devices` (List[str]): The list of serial numbers of the
            devices that are currently connected.
        `connector` (DeviceConnection): The `DeviceConnection` object used to
            manage the device connections.
        `adb_pair` (Optional[AdbPairing]): The `AdbPairing` object used to
            manage the pairing of devices.

    Properties:
        - `connected_devices` (List[str]): The list of serial numbers of the
            devices that are currently connected.

    Methods:
        connect_devices: Connects to the devices with the provided serial
            numbers.
        get_device_info: Retrieves the device information associated with a
            given serial number.
        get_device_actions: Retrieves the device actions associated with a
            given serial number.
        build_command_list: Builds a list of commands to be executed on
            multiple devices.
        execute_adb_command: Executes a custom adb command on all connected
            devices.
        adb_pairing_instance: Creates an instance of the AdbPairing class.
        is_connected: Checks if a device with the provided serial number is
            connected.
        disconnect_devices: Disconnects the devices with the provided serial
            numbers.
    """

    def __init__(
        self,
        subprocess_check_flag: bool = False,
        fixed_port: int = DEFAULT_FIXED_PORT,
    ):
        self.subprocess_check = subprocess_check_flag
        self._devices_fixed_port = fixed_port
        self.connector = DeviceConnection(
            subprocess_check_flag=self.subprocess_check,
            fixed_port=self._devices_fixed_port,
        )
        self.adb_pair: Optional[AdbPairing] = None
        self.__device_info: ObjectManager[DeviceInfo] = ObjectManager()
        self.__device_actions: ObjectManager[DeviceActions] = ObjectManager()

    def __getitem__(
        self,
        serial_number: str,
    ) -> Optional[Tuple[DeviceInfo, DeviceActions]]:
        """Get the device information and actions associated with a
        serial number. If the serial number is not found, None is returned.

        Args:
            serial_number (str): The serial number of the device.

        Returns:
            Optional[Tuple[DeviceInfo, DeviceActions]]: The device information
            and actions associated with the serial number.
        """
        try:
            info = self.__device_info.get(serial_number)
            actions = self.__device_actions.get(serial_number)
            return info, actions
        except KeyError:
            return None

    def __len__(self) -> int:
        """Returns the number of devices currently managed by this class."""
        return len(self.__device_info)

    def __iter__(self) -> Iterable[DeviceObjects]:
        """Iterates over the devices being managed by this class.
        Returns an iterator with a tuple containing the device serial number,
        device information and device actions.

        Supports usage of the `for` loop to iterate over the devices."""
        device_objects = map(
            lambda info, actions: DeviceObjects(
                serial_number=info.serial_number,
                device_info=info,
                device_actions=actions,
            ),
            self.__device_info,
            self.__device_actions,
        )
        return device_objects

    def __delitem__(self, key: str) -> None:
        """Removes a device from the manager.

        Args:
            key (str): The serial number of the device to remove.
        """
        del self.__device_info[key]
        del self.__device_actions[key]

    def __contains__(self, key: str) -> bool:
        """Checks if a device with the provided serial number is managed.

        Args:
            key (str): The serial number of the device to check.

        Returns:
            bool: True if the device is managed, False otherwise.
        """
        return key in self.__device_info

    def __repr__(self) -> str:
        """Returns a string representation of the class.

        Returns:
            str: The string representation of the class.
        """
        return f'device_manager.DeviceManager({len(self)} devices: {list(self.__device_info.keys())})'  # noqa

    def __str__(self) -> str:
        return f'DeviceManager({len(self)} devices: {list(self.__device_info.keys())})'  # noqa

    @property
    def connected_devices(self) -> List[str]:
        """Returns the list of serial numbers of the devices that are
        currently connected.

        Returns:
            List[str]: The list of serial numbers of the connected devices.
        """
        return list(self.__device_info.keys())

    def connect_devices(self, *serial_number: str) -> bool:
        """Connects to the devices with the provided serial numbers.
        This method will start the connection to the devices and create
        the necessary DeviceInfo and DeviceActions objects, which will be
        stored in the internal object manager objects.

        Returns:
            bool: True if the connection was successful, False otherwise.
        """
        serial_number_list = list(serial_number)
        success_op = self.connector.start_connection(serial_number_list)
        if success_op:
            for serial in self.connector.connection_info.keys():
                if serial not in self.__device_info.keys():
                    dev_info = DeviceInfo(
                        self.connector,
                        serial,
                        subprocess_check_flag=self.subprocess_check,
                    )
                    dev_actions = DeviceActions(
                        self.connector,
                        serial,
                        subprocess_check_flag=self.subprocess_check,
                    )
                    self.__device_info.add(serial, dev_info)
                    self.__device_actions.add(serial, dev_actions)
        return success_op

    def disconnect_devices(self, *serial_number: str) -> bool:
        """Disconnects the devices with the provided serial numbers.
        This method will stop the connection to the devices and remove
        the associated DeviceInfo and DeviceActions objects from the
        internal object manager objects.

        Returns:
            bool: True if the disconnection was successful, False otherwise.
        """
        serial_number_list = list(serial_number)
        success_op = self.connector.stop_connection(serial_number_list)
        if success_op:
            for serial in serial_number_list:
                sbn = self.connector.connection_info.get(serial)
                if sbn is None:  # Should Be None
                    self.__device_info.remove(serial)
                    self.__device_actions.remove(serial)
        return success_op

    def get_device_info(self, serial_number: str) -> DeviceInfo:
        """Retrieves the device information associated with a given
        serial number.

        Args:
            serial_number (str): The serial number of the device.

        Returns:
            DeviceInfo: The device information object.
        """
        return self.__device_info.get(serial_number)

    def get_device_actions(self, serial_number: str) -> DeviceActions:
        """Retrieves the device actions associated with a given serial number.

        Args:
            serial_number (str): The serial number of the device.

        Returns:
            DeviceActions: The device actions object.
        """
        return self.__device_actions.get(serial_number)

    def execute_adb_command(
        self,
        command: str,
        comm_uris: Optional[List[str]] = None,
        shell: bool = True,
        subprocess_check_flag: bool = False,
        capture_output: bool = False,
        **kwargs,
    ) -> CompletedProcess:
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
        uris = comm_uris
        if comm_uris is None:
            uris = [device.current_comm_uri for device in self.__device_info]
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
            **kwargs,
        )

    def adb_pairing_instance(
        self,
        service_name: str = 'robot_celular',
        service_regex_filter: Optional[str] = None,
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
        """Clears the internal object managers, removing all devices."""
        self.__device_info = ObjectManager()
        self.__device_actions = ObjectManager()
