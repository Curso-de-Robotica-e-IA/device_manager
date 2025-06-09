import re
from typing import Optional

from device_manager.adb_executor import execute_adb_command
from device_manager.connection.device_connection import DeviceConnection
from device_manager.utils.util_functions import grep


class AppInfo:
    def __init__(
        self,
        package: str,
        device_connection: DeviceConnection,
        serial_number: str,
        subprocess_check_flag: bool = False,
    ) -> None:
        self.package = package
        self.subprocess_check_flag = subprocess_check_flag
        self.device_connection = device_connection
        self.__serial_number = serial_number
        self.current_comm_uri = self.device_connection.build_comm_uri(
            self.__serial_number,
        )
        self.setup()

    def setup(self) -> None:
        """Sets up the AppInfo instance by validating the device connection."""
        if self.device_connection.validate_connection(
            self.__serial_number,
            force_reconnect=True,
        ):
            self.dumpsys = execute_adb_command(
                command=f'dumpsys package {self.package}',
                shell=True,
                comm_uris=[self.current_comm_uri],
                subprocess_check_flag=self.subprocess_check_flag,
                capture_output=True,
            ).stdout

    def get_property(
        self,
        property_name: str,
    ) -> Optional[str]:
        """Gets a property of an application on the device using the
        provided package name and property name.

        Args:
            property_name (str): The property name to retrieve.
        Returns:
            The value of the specified property if found, otherwise None.
        """
        grep_lines = grep(self.dumpsys, property_name)
        if len(grep_lines) > 0:
            value = grep_lines[0].strip().split('=')[1]
            return value

    def get_action(self, action: str) -> str:
        """Checks if a specific action exists in the application's
        intent filters and returns it.

        Args:
            action (str): The action to check for existence.
        Returns:
            str: The grep lines containing the action if it exists,
            otherwise an empty string.
        """
        grep_lines = grep(self.dumpsys, rf'{action}')
        best_match = ''
        if grep_lines:
            for line in grep_lines:
                stripped = line.strip().strip(":")
                if stripped.endswith(action):
                    best_match = stripped
            if not best_match:
                best_match = grep_lines[0].strip().strip(":").strip('"').strip('Action: ')  # noqa: E501
        return best_match
