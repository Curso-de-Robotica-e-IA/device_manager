import subprocess
from pathlib import Path
from typing import Optional

from device_manager.actions.camera_actions import CameraActions
from device_manager.connection.device_connection import DeviceConnection


class DeviceActions:
    """Class responsible for interacting with a single device. It is able
    to execute predefined actions at the device.

    Args:
        device_connection (DeviceConnection): the `DeviceConnection` object.
        serial_number (str): the serial number associated with the device.
        subprocess_check_flag (bool): the flag to check the subprocess
            execution status. Defaults to False.
            Check the subprocess documentation for more information

    Attributes:
        current_comm_uri (str): the current communication URI for the device.

    Properties:
        - `serial_number` (str): The serial number associated with
            the device.

    Methods:
        click_by_coordinates(x: int, y: int) -> None:
            Simulates a click at the provided (x, y) coordinates.
        swipe(x1: int, y1: int, x2: int, y2: int, time: int) -> None:
            Inputs a swipe gesture on the device screen using the provided
            coordinates and time duration.
        open_app(package_name: str, activity_name: str) -> None:
            Opens an application on the device using the provided package
            name and activity name.
        close_app(package_name: str) -> None:
            Closes an application on the device using the provided package
            name.
        install_apk(apk_path: str, replace: bool = False) -> None:
            Installs an APK file on the device.
        turn_on_screen() -> None:
            Turns on the device screen.
        unlock_screen() -> None:
            Unlocks the device screen.
        home_button() -> None:
            Simulates the Home button press on the device
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
        self.camera = CameraActions(
            device_connection=self.device_connection,
            serial_number=self.__serial_number,
            subprocess_check_flag=self.subprocess_check_flag,
            comm_uri=self.current_comm_uri,
            validate_connection_callback=self.validate_connection,
        )

    @property
    def serial_number(self) -> str:
        """The serial number associated with the device.

        Returns:
            str: The device serial number.
        """
        return self.__serial_number

    def validate_connection(self) -> bool:
        """Validates the connection to the device.

        Returns:
            bool: True if the connection is valid, False otherwise.
        """
        return self.device_connection.validate_connection(
            self.__serial_number,
            force_reconnect=True,
        )

    def click_by_coordinates(self, x: int, y: int) -> None:
        """
        This method validates the device connection and then uses an ADB
        command to simulate a swipe gesture that acts as a click at the
        provided (x, y)coordinates.
        The swipe coordinates are the same for the start and end
        points to ensure it functions as a click.

        Args:
            x (int): The x-coordinate on the screen where the click should
                occur.
            y (int): The y-coordinate on the screen where the click should
                occur.
        """

        if self.validate_connection():
            subprocess.run(
                [
                    'adb',
                    '-s',
                    self.current_comm_uri,
                    'shell',
                    'input',
                    'tap',
                    str(x),
                    str(y),
                ],
                check=self.subprocess_check_flag,
            )

    def swipe(self, x1: int, y1: int, x2: int, y2: int, time: int) -> None:
        """Inputs a swipe gesture on the device screen using the provided
        coordinates and time duration.

        Args:
            x1 (int): The x-coordinate of the starting point.
            y1 (int): The y-coordinate of the starting point.
            x2 (int): The x-coordinate of the ending point.
            y2 (int): The y-coordinate of the ending point.
            time (int): The duration of the swipe gesture.
        """

        if self.validate_connection():
            subprocess.run(
                [
                    'adb',
                    '-s',
                    self.current_comm_uri,
                    'shell',
                    'input',
                    'swipe',
                    str(x1),
                    str(y1),
                    str(x2),
                    str(y2),
                    str(time),
                ],
                check=self.subprocess_check_flag,
            )

    def _open_app_one_arg(self, package_activity: str) -> None:
        """Opens an application on the device using the provided package
        name and activity name. This method is used when the package name
        and activity name are combined into a single string argument.

        Args:
            package_activity (str): The package name and activity name
                of the application.
                Ex.: 'com.android.deskclock/.DeskClockTabActivity'
        """
        subprocess.run(
            [
                'adb',
                '-s',
                self.current_comm_uri,
                'shell',
                'am',
                'start',
                '-n',
                package_activity,
            ],
            check=self.subprocess_check_flag,
        )

    def _open_app_two_args(
        self,
        package_name: str,
        activity_name: str,
    ) -> None:
        """Opens an application on the device using the provided package
        name and activity name. This method is used when the package name
        and activity name are provided as separate string arguments.

        Usage Example:
        ```
        open_app('com.android.deskclock', '.DeskClockTabActivity')
        ```

        Args:
            package_name (str): The package name of the application.
            activity_name (str): The activity name of the application.
        """
        subprocess.run(
            [
                'adb',
                '-s',
                self.current_comm_uri,
                'shell',
                'am',
                'start',
                '-n',
                f'{package_name}/{activity_name}',
            ],
            check=self.subprocess_check_flag,
        )

    def open_app(
        self,
        package_name: str,
        activity_name: Optional[str] = None,
    ) -> None:
        """Opens an application on the device using the provided package
        name and activity name.

        Args:
            package_name (str): The package name of the application.
            activity_name (str): The activity name of the application.
        """

        if self.validate_connection():
            if activity_name is None:
                self._open_app_one_arg(package_name)
            else:
                self._open_app_two_args(package_name, activity_name)

    def close_app(self, package_name: str) -> None:
        """Closes an application on the device using the provided package
        name.

        Args:
            package_name (str): The package name of the application.
        """

        if self.validate_connection():
            subprocess.run(
                [
                    'adb',
                    '-s',
                    self.current_comm_uri,
                    'shell',
                    'am',
                    'force-stop',
                    package_name,
                ],
                check=self.subprocess_check_flag,
            )

    def install_apk(
        self,
        apk_path: str,
        replace: bool = False,
    ) -> None:
        """Installs an APK file on the device.

        Args:
            apk_path (str): The path to the APK file.
            replace (bool): Whether to replace the existing APK file.
                Defaults to False.
        """
        path = Path(apk_path)
        if not path.exists():
            raise FileNotFoundError(f'File not found: {apk_path}')

        if self.validate_connection():
            apk_file_path = (path.resolve()).as_posix()
            subprocess.run(
                [
                    'adb',
                    '-s',
                    self.current_comm_uri,
                    'install',
                    '-r' if replace else '',
                    apk_file_path,
                ],
                check=self.subprocess_check_flag,
            )

    def turn_on_screen(self):
        """
        This method executes the adb `keyevent 26`, which represents
        the `wakeup screen` action.
        """
        if self.validate_connection():
            subprocess.run(
                [
                    'adb',
                    '-s',
                    self.current_comm_uri,
                    'shell',
                    'input',
                    'keyevent',
                    '26',
                ],
                check=self.subprocess_check_flag,
            )

    def unlock_screen(self):
        """
        This method executes the adb `keyevent 82`, which represents
        the `unlock screen` action.
        """
        if self.validate_connection():
            subprocess.run(
                [
                    'adb',
                    '-s',
                    self.current_comm_uri,
                    'shell',
                    'input',
                    'keyevent',
                    '82',
                ],
                check=self.subprocess_check_flag,
            )

    def home_button(self):
        """
        This method executes the adb `keyevent 3`, which represents
        the `Home` phone button.
        """
        if self.validate_connection():
            subprocess.run(
                [
                    'adb',
                    '-s',
                    self.current_comm_uri,
                    'shell',
                    'input',
                    'keyevent',
                    '3',
                ],
                check=self.subprocess_check_flag,
            )

    def push_file(
        self,
        local_path: str,
        remote_path: str,
    ) -> None:
        """Pushes a file from the local machine to the device.

        Args:
            local_path (str): The path to the file on the local machine.
            remote_path (str): The destination path on the device.
        """
        if self.validate_connection():
            subprocess.run(
                [
                    'adb',
                    '-s',
                    self.current_comm_uri,
                    'push',
                    local_path,
                    remote_path,
                ],
                check=self.subprocess_check_flag,
            )

    def pull_file(
        self,
        remote_path: str,
        local_path: str,
    ) -> None:
        """Pulls a file from the device to the local machine.

        Args:
            remote_path (str): The path to the file on the device.
            local_path (str): The destination path on the local machine.
        """
        if self.validate_connection():
            subprocess.run(
                [
                    'adb',
                    '-s',
                    self.current_comm_uri,
                    'pull',
                    remote_path,
                    local_path,
                ],
                check=self.subprocess_check_flag,
            )
