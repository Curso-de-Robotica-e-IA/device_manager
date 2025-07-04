import re
from typing import Dict, List, Optional, TypedDict

import uiautomator2 as u2

from device_manager.adb_executor import execute_adb_command
from device_manager.connection.device_connection import DeviceConnection
from device_manager.infos.app import AppInfo
from device_manager.utils.util_functions import grep

UNEXPECTED_ADB_OUTPUT = 'Unexpected output from ADB command'


class DeviceProperties(TypedDict):
    """TypedDict for device properties."""

    serial_number: str
    brand: str
    model: str
    android_version: str


class DeviceInfo:
    """Class responsible for retrieving information from a single device.
    It is able to execute predefined actions at the device.

    Args:
        device_connection (DeviceConnection): the `DeviceConnection` object.
        serial_number (str): the serial number associated with the device.
        subprocess_check_flag (bool): the flag to check the subprocess
            execution status. Defaults to False.
            Check the subprocess documentation for more information.

    Attributes:
        current_comm_uri (str): the current communication URI for the device.

    Properties:
        - `serial_number` (str): The serial number associated with the device.

    Methods:
        actual_activity() -> str:
            Checks the device connection and executes an ADB command to obtain
            information about the top resumed activity from the Android
            activity manager. The output is captured and returned as a string.
        is_screen_on() -> bool:
            Checks if the associated device screen is on.
        is_device_locked() -> bool:
            Checks if the associated device is locked.
        get_screen_gui_xml() -> str:
            Retrieves the .xml that represents the current state of the device
            screen.
    """

    def __init__(
        self,
        device_connection: DeviceConnection,
        serial_number: str,
        subprocess_check_flag: bool = False,
    ):
        self.subprocess_check_flag = subprocess_check_flag
        self.device_connection = device_connection
        self.__serial_number = serial_number
        self.current_comm_uri = self.device_connection.build_comm_uri(
            self.__serial_number,
        )

    @property
    def serial_number(self) -> str:
        """The serial number associated with the device.

        Returns:
            str: The device serial number.
        """
        return self.__serial_number

    def actual_activity(self) -> str:
        """
        This method checks the device connection and executes an ADB command
        to obtain information about the top resumed activity from the Android
        activity manager. The output is captured and returned as a string.

        Returns:
            str: The name of the currently resumed activity.
        """

        if self.device_connection.validate_connection(
            self.__serial_number,
            force_reconnect=True,
        ):
            output = execute_adb_command(
                command='dumpsys activity activities',
                shell=True,
                comm_uris=[self.current_comm_uri],
                subprocess_check_flag=self.subprocess_check_flag,
                capture_output=True,
            ).stdout
            greplines = grep(output, 'mCurrentFocus')
            if len(greplines) == 0:
                return 'No activity'
            package_pattern = re.compile(
                r'com\.[a-zA-Z0-9_]+(?:\.[a-zA-Z0-9_]+)*'
            )
            result = re.findall(package_pattern, greplines[0])
            if len(result) == 0:
                return 'No activity'
            return '/'.join(result)

    def is_screen_on(self) -> bool:
        """This method checks if the associated device screen is on.

        Returns:
            bool: True if the screen is on, false otherwise.
        """
        if self.device_connection.validate_connection(
            self.__serial_number,
            force_reconnect=True,
        ):
            output = execute_adb_command(
                command='dumpsys deviceidle',
                shell=True,
                comm_uris=[self.current_comm_uri],
                subprocess_check_flag=self.subprocess_check_flag,
                capture_output=True,
            ).stdout
            greplines = grep(output, 'mScreenOn')
            assert len(greplines) == 1
            result = greplines[0].split('=')
            if 'true' in result:
                return True
            elif 'false' in result:
                return False
            raise ValueError(UNEXPECTED_ADB_OUTPUT)

    def is_device_locked(self) -> bool:
        """This method checks if the associated device is locked.

        Returns:
            bool: True if the device is locked, false otherwise.
        """
        if self.device_connection.validate_connection(
            self.__serial_number,
            force_reconnect=True,
        ):
            output = execute_adb_command(
                command='dumpsys deviceidle',
                shell=True,
                comm_uris=[self.current_comm_uri],
                subprocess_check_flag=self.subprocess_check_flag,
                capture_output=True,
            ).stdout
            grep_lines = grep(output, 'mScreenLocked')
            if len(grep_lines) != 1:
                raise ValueError(UNEXPECTED_ADB_OUTPUT)

            result = grep_lines[0].split('=')
            if 'true' in result:
                return True
            elif 'false' in result:
                return False

            raise ValueError(UNEXPECTED_ADB_OUTPUT)

    def get_screen_gui_xml(self) -> str:
        """This method retrieves the .xml that represents the current state
        of the device screen.

        Returns:
            str: The device screen xml as a string.
        """
        if self.device_connection.validate_connection(
            self.__serial_number,
            force_reconnect=True,
        ):
            device = u2.connect(self.current_comm_uri)
            return device.dump_hierarchy()

    def get_properties(
        self,
        extra_keys: Optional[List[str]] = None,
    ) -> Dict[str, str]:
        """This method retrieves the properties of the device, and returns a
        dictionary containing the properties. By default, it retrieves the
        serial number, brand, model, and Android version. If extra keys are
        provided, it will also retrieve those properties.
        The properties are obtained by executing the `adb shell getprop`
        command, so the extra keys must be valid properties, without the
        trailing brackets (`[]`).

        Args:
            extra_keys (Optional[List[str]]): A list of extra keys to retrieve
                from the device properties. Defaults to None.

        Returns:
            Dict[str, str]: A dictionary containing the properties of the
                device.
        """
        if self.device_connection.validate_connection(
            self.__serial_number,
            force_reconnect=True,
        ):
            output = execute_adb_command(
                command='getprop',
                shell=True,
                comm_uris=[self.current_comm_uri],
                subprocess_check_flag=self.subprocess_check_flag,
                capture_output=True,
            ).stdout
            prop_dict = dict()
            EXPECTED_LENGTH = 2
            for line in output.splitlines():
                key_value = line.split(': ', 1)
                if len(key_value) == EXPECTED_LENGTH:
                    key_ = key_value[0][1:-1]
                    value_ = key_value[1][1:-1]
                    prop_dict[key_] = value_
            base_result = {
                'serial_number': prop_dict['ro.serialno'],
                'brand': prop_dict['ro.product.manufacturer'],
                'model': prop_dict['ro.product.model'],
                'android_version': prop_dict['ro.build.version.release'],
            }
            if extra_keys is not None:
                for key in extra_keys:
                    if key in prop_dict:
                        base_result[key] = prop_dict[key]
            return DeviceProperties(**base_result)

    def get_screen_dimensions(self) -> tuple[int, int]:
        """Gets the dimensions of the device screen.

        Returns:
            tuple[int, int]: The width and height of the device screen.
        """
        if self.device_connection.validate_connection(
            self.__serial_number,
            force_reconnect=True,
        ):
            result = execute_adb_command(
                command='wm size',
                shell=True,
                comm_uris=[self.current_comm_uri],
                subprocess_check_flag=self.subprocess_check_flag,
                capture_output=True,
            ).stdout
            grep_lines = grep(result, 'Physical size:')
            if len(grep_lines) > 0:
                dimensions = grep_lines[0].split(':')[1].strip().split('x')
                return int(dimensions[0]), int(dimensions[1])

    def app(self, package: str) -> AppInfo:
        """Returns an instance of AppInfo for the specified package.

        Args:
            package (str): The package name of the application.

        Returns:
            AppInfo: An instance of AppInfo for the specified package.
        """
        return AppInfo(
            package=package,
            device_connection=self.device_connection,
            serial_number=self.__serial_number,
            subprocess_check_flag=self.subprocess_check_flag,
        )
