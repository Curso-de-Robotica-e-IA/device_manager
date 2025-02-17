import subprocess
from device_manager.components.object_manager import ObjectManager
from device_manager.connection.device_connection import DeviceConnection
from device_manager.device_actions import DeviceActions
from device_manager.device_info import DeviceInfo
from subprocess import CompletedProcess
from typing import Tuple, Optional, List, NamedTuple, Iterable


DeviceObjects = NamedTuple(
    'DeviceObjects',
    [
        ('serial_number', str),
        ('device_info', DeviceInfo),
        ('device_actions', DeviceActions),
    ]
)


class DeviceManager:
    """This class is able to manage multiple device connections, storing
    each of their reference internally. It is able to retrieve the associated
    `DeviceInfo` and `DeviceAction` for each device, by accessing this
    class as a dict, using the device serial used for connection as key.
    """

    def __init__(self):
        self.connector = DeviceConnection()
        self.__device_info: ObjectManager[DeviceInfo] = ObjectManager()
        self.__device_actions: ObjectManager[DeviceActions] = ObjectManager()

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
                    )
                    dev_actions = DeviceActions(
                        self.connector,
                        serial,
                    )
                    self.__device_info.add(serial, dev_info)
                    self.__device_actions.add(serial, dev_actions)
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

    @staticmethod
    def build_command_list(
        base_command: List[str],
        comm_uri_list: List[str],
        custom_command: str,
        **kwargs,
    ) -> List[str]:
        """Builds a list of commands to be executed on multiple devices.
        This method is used to build a list of commands that will be executed
        on multiple devices. The command is built using the base command
        provided, the list of communication URIs, the custom command to be
        executed, and any additional arguments that should be added to the
        command.

        Args:
            base_command (List[str]): The base command to be executed.
            comm_uri_list (List[str]): The list of communication URIs for the
                devices.
            custom_command (str): The custom command to be executed.
            **kwargs: Additional arguments to be added to the command.
        """
        command = base_command.copy()
        command_as_list = custom_command.split(" ")
        for idx, uri in enumerate(comm_uri_list):
            command.extend(["-s", uri])
            command.append("shell")
            command.extend(command_as_list)
            if idx < len(comm_uri_list) - 1:
                command.extend(["&&", "adb"])
        if kwargs:
            for key, value in kwargs.items():
                command.extend([key, value])
        return command

    def execute_adb_command(
        self,
        command: str,
        comm_uris: Optional[List[str]] = None,
        **kwargs,
    ) -> CompletedProcess:
        """Executes a custom adb command on all connected devices.
        Additional arguments and keyword arguments can be provided to
        customize the command, which will be added to the end of the command
        string.
        This function already adds the `adb shell` part of the shell command.

        Passing a command such as `input keyevent 3` will produce the
        following command: `adb shell input keyevent 3`, applied with the
        `-s` flag for each device.

        You can execute a command on a set of specific devices by providing
        the serial numbers as additional arguments.

        Args:
            command (str): The adb command to execute.
            *comm_uri (str): The serial numbers of the devices to execute the
                command on.

        Returns:
            CompletedProcess: The result of the command execution.
        """
        uris = comm_uris
        if comm_uris is None:
            uris = [device.current_comm_uri
                    for device in self.__device_info]
        base_command = ["adb"]
        adb_command = self.build_command_list(
            base_command=base_command,
            comm_uri_list=uris,
            custom_command=command,
            **kwargs,
        )
        return subprocess.run(
            adb_command,
            shell=True,
        )

    def __iter__(self) -> Iterable[DeviceObjects]:
        """Iterates over the devices being managed by this class.
        Returns an iterator with a tuple containing the device serial number,
        device information and device actions.

        Supports usage of the `for` loop to iterate over the devices."""
        device_objects = map(lambda info, actions: DeviceObjects(
            serial_number=info.serial_number,
            device_info=info,
            device_actions=actions,
        ), self.__device_info, self.__device_actions)
        return device_objects
