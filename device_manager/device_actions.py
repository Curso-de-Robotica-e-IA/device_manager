import subprocess
from time import sleep

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
        open_gravity_sensor() -> None:
            Starts the gravity sensor application.
        stop_gravity_sensor() -> None:
            Stops the gravity sensor application.
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

    @property
    def serial_number(self) -> str:
        """The serial number associated with the device.

        Returns:
            str: The device serial number.
        """
        return self.__serial_number

    def click_by_coordinates(self, x: int, y: int) -> None:
        """
        This method validates the device connection and then uses an ADB
        command to simulate a swipe gesture that acts as a click at the
        provided (x, y)coordinates.
        The swipe coordinates are the same for the start and end
        points to ensure it functions as a click.
        :param x:The x-coordinate on the screen where the click should occur.
        :param y:The y-coordinate on the screen where the click should occur.
        :return:
        """

        if self.device_connection.validate_connection(
            self.__serial_number,
            force_reconnect=True,
        ):
            subprocess.run(
                [
                    'adb',
                    '-s',
                    self.current_comm_uri,
                    'shell',
                    'input',
                    'swipe',
                    str(x),
                    str(y),
                    str(x),
                    str(y),
                ],
                shell=True,
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

        if self.device_connection.validate_connection(
            self.__serial_number,
            force_reconnect=True,
        ):
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
                shell=True,
                check=self.subprocess_check_flag,
            )

    def open_app(self, package_name: str, activity_name: str) -> None:
        """Opens an application on the device using the provided package
        name and activity name.

        Args:
            package_name (str): The package name of the application.
            activity_name (str): The activity name of the application.
        """

        if self.device_connection.validate_connection(
            self.__serial_number,
            force_reconnect=True,
        ):
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
                shell=True,
                check=self.subprocess_check_flag,
            )

    def close_app(self, package_name: str) -> None:
        """Closes an application on the device using the provided package
        name.

        Args:
            package_name (str): The package name of the application.
        """

        if self.device_connection.validate_connection(
            self.__serial_number,
            force_reconnect=True,
        ):
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
                shell=True,
                check=self.subprocess_check_flag,
            )

    # Remove
    def open_gravity_sensor(self) -> None:
        """
        This method start the app gravity sensor.
        """
        if self.device_connection.validate_connection(
            self.__serial_number,
            force_reconnect=True,
        ):
            uri = self.current_comm_uri
            subprocess.run(
                [
                    'adb',
                    '-s',
                    uri,
                    'shell',
                    'am',
                    'start',
                    'com.rria.gravity/com.rria.gravity.MainActivity',
                ],
                check=self.subprocess_check_flag,
            )
            sleep(2)

    # Remove
    def stop_gravity_sensor(self) -> None:
        """
        This method executes an ADB (Android Debug Bridge) command to clear the
        application data of the specified package, effectively stopping the
        gravity sensor service.
        """
        if self.device_connection.validate_connection(
            self.__serial_number,
            force_reconnect=True,
        ):
            uri = self.current_comm_uri
            subprocess.run(
                [
                    'adb',
                    '-s',
                    uri,
                    'shell',
                    'am',
                    'force-stop',
                    'com.rria.gravity',
                ],
                check=self.subprocess_check_flag,
            )

    def turn_on_screen(self):
        """
        This method executes the adb `keyevent 26`, which represents
        the `wakeup screen` action.
        """
        if self.device_connection.validate_connection(
            self.__serial_number,
            force_reconnect=True,
        ):
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
        if self.device_connection.validate_connection(
            self.__serial_number,
            force_reconnect=True,
        ):
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
        if self.device_connection.validate_connection(
            self.__serial_number,
            force_reconnect=True,
        ):
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
