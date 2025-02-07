import subprocess
from time import sleep
from device_manager.connection.device_connection import DeviceConnection


class DeviceActions:

    def __init__(
        self,
        device_connection: DeviceConnection,
        serial_number: str,
    ):
        self.device_connection = device_connection
        self.__serial_number = serial_number
        self.current_comm_uri = self.device_connection.build_comm_uri(
            self.__serial_number,
        )

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
                ["adb", "-s", self.current_comm_uri,
                 "shell", "input", "swipe",
                 str(x), str(y), str(x), str(y)],
                shell=True,
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
                ["adb", "-s", self.current_comm_uri,
                 "shell", "input", "swipe",
                 str(x1), str(y1), str(x2), str(y2), str(time)],
                shell=True,
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
                ["adb", "-s", self.current_comm_uri,
                 "shell", "am", "start", "-n",
                 f"{package_name}/{activity_name}"],
                shell=True,
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
                ["adb", "-s", self.current_comm_uri,
                 "shell", "am", "force-stop", package_name],
                shell=True,
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
                ["adb", '-s', uri, "shell", "am", "start",
                 "com.rria.gravity/com.rria.gravity.MainActivity"],
                check=True,
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
                ["adb", '-s', uri, "shell", "am", "force-stop",
                 "com.rria.gravity"],
                check=True,
            )

    def turn_on_screen(self):
        if self.device_connection.validate_connection(
            self.__serial_number,
            force_reconnect=True,
        ):
            subprocess.run(
                ["adb", "-s", self.current_comm_uri,
                 "shell", "input", "keyevent", "26"],
            )

    def unlock_screen(self):
        if self.device_connection.validate_connection(
            self.__serial_number,
            force_reconnect=True,
        ):
            subprocess.run(
                ["adb", "-s", self.current_comm_uri,
                 "shell", "input", "keyevent", "82"],
            )

    def home_button(self):
        if self.device_connection.validate_connection(
            self.__serial_number,
            force_reconnect=True,
        ):
            subprocess.run(
                ["adb", "-s", self.current_comm_uri,
                 "shell", "input", "keyevent", "3"],
            )
