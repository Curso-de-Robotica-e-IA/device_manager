import subprocess
import uiautomator2 as u2
from connection.device_connection import DeviceConnection


class DeviceInfo:

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

    def actual_activity(self) -> str:
        """
        This method checks the device connection and executes an ADB command
        to obtain information about the top resumed activity from the Android
        activity manager. The output is captured and returned as a string.

        :return: The name of the currently resumed activity.
        """

        if self.device_connection.validate_connection(
            self.__serial_number,
            force_reconnect=True,
        ):
            result = subprocess.run(
                f'adb -s {self.current_comm_uri} shell "dumpsys activity activities | grep topResumedActivity"',  # noqa
                capture_output=True,
                text=True,
            )
            output = result.stdout

            return output

    def is_screen_on(self):
        if self.device_connection.validate_connection(
            self.__serial_number,
            force_reconnect=True,
        ):
            output = subprocess.run(
                f'adb -s {self.current_comm_uri} shell "dumpsys deviceidle | grep mScreenOn"',  # noqa
                capture_output=True,
                text=True,
            )
            output = output.stdout.strip()
            output = output.split("=")
            if "true" in output:

                return True

            return False

    def is_device_locked(self):
        if self.device_connection.validate_connection(
            self.__serial_number,
            force_reconnect=True,
        ):
            output = subprocess.run(
                f'adb -s {self.current_comm_uri} shell "dumpsys deviceidle | grep mScreenLocked"',  # noqa
                capture_output=True,
                text=True,
            )
            output = output.stdout.strip()
            output = output.split("=")
            if "true" in output:

                return True

            return False

    def get_screen_gui_xml(self):
        if self.device_connection.validate_connection(
            self.__serial_number,
            force_reconnect=True,
        ):
            device = u2.connect(self.current_comm_uri)
            return device.dump_hierarchy()
