import subprocess
from time import sleep


class DeviceActions:
    def __init__(self, connection_manager):
        self.connection_manager = connection_manager
        self.current_comm_uri = self.connection_manager.current_comm_uri

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

        if self.connection_manager.validate_connection():
            subprocess.run(
                f"adb -s {self.current_comm_uri} shell input swipe {x} {y} {x} {y}",  # noqa
                shell=True,
            )

    def swipe(self, x1: int, y1: int, x2: int, y2: int, time: int) -> None:
        """ """

        if self.connection_manager.validate_connection():
            subprocess.run(
                f"adb -s {self.current_comm_uri} shell input swipe {x1} {y1} {x2} {y2} {time}",  # noqa
                shell=True,
            )

    def open_gravity_sensor(self) -> None:
        """
        This method start the app gravity sensor.
        """
        if self.connection_manager.validate_connection():
            subprocess.run(
                ["adb", "shell", "am", "start",
                 "com.rria.gravity/com.rria.gravity.MainActivity"],
                check=True,
            )
            sleep(2)

    @staticmethod
    def stop_gravity_sensor() -> None:
        """
        This method executes an ADB (Android Debug Bridge) command to clear the
        application data of the specified package, effectively stopping the
        gravity sensor service.
        """

        subprocess.run("adb shell am force-stop com.example.gravity_sensor")

    def turn_on_screen(self):
        if self.connection_manager.validate_connection():
            subprocess.run(
                f"adb -s {self.current_comm_uri} shell input keyevent 26",
            )

    def unlock_screen(self):
        if self.connection_manager.validate_connection():
            subprocess.run(
                f"adb -s {self.current_comm_uri} shell input keyevent 82",
            )

    def home_button(self):
        if self.connection_manager.validate_connection():
            subprocess.run(
                f"adb -s {self.current_comm_uri} shell input keyevent 3",
            )
