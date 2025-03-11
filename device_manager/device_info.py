import subprocess

import uiautomator2 as u2

from device_manager.connection.device_connection import DeviceConnection


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
            result = subprocess.run(
                [
                    'adb',
                    '-s',
                    self.current_comm_uri,
                    'shell',
                    '"dumpsys activity activities | grep topResumedActivity"',
                ],
                capture_output=True,
                text=True,
                check=self.subprocess_check_flag,
            )
            output = result.stdout

            return output

    def is_screen_on(self) -> bool:
        """This method checks if the associated device screen is on.

        Returns:
            bool: True if the screen is on, false otherwise.
        """
        if self.device_connection.validate_connection(
            self.__serial_number,
            force_reconnect=True,
        ):
            output = subprocess.run(
                [
                    'adb',
                    '-s',
                    self.current_comm_uri,
                    'shell',
                    '"dumpsys deviceidle | grep mScreenOn"',
                ],
                capture_output=True,
                text=True,
                check=self.subprocess_check_flag,
            )
            output = output.stdout.strip()
            output = output.split('=')
            if 'true' in output:
                return True

            return False

    def is_device_locked(self) -> bool:
        """This method checks if the associated device is locked.

        Returns:
            bool: True if the device is locked, false otherwise.
        """
        if self.device_connection.validate_connection(
            self.__serial_number,
            force_reconnect=True,
        ):
            output = subprocess.run(
                [
                    'adb',
                    '-s',
                    self.current_comm_uri,
                    'shell',
                    '"dumpsys deviceidle | grep mScreenLocked"',
                ],
                capture_output=True,
                text=True,
                check=self.subprocess_check_flag,
            )
            output = output.stdout.strip()
            output = output.split('=')
            if 'true' in output:
                return True

            return False

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
