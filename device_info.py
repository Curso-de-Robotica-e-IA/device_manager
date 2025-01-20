import re
import subprocess
from time import sleep
from xml.etree import ElementTree
import uiautomator2 as u2


class DeviceInfo:
    def __init__(self, connection_manager):
        self.connection_manager = connection_manager
        self.current_comm_uri = None

    def actual_activity(self) -> str:
        """
        This method checks the device connection and executes an ADB command
        to obtain information about the top resumed activity from the Android
        activity manager. The output is captured and returned as a string.

        :return: The name of the currently resumed activity.
        """

        if self.connection_manager.validate_connection():
            result = subprocess.run(
                f'adb -s {self.current_comm_uri} shell "dumpsys activity activities | grep topResumedActivity"',
                capture_output=True,
                text=True,
            )
            output = result.stdout

            return output

    def is_screen_on(self):
        if self.connection_manager.validate_connection():
            output = subprocess.run(f'adb -s {self.current_comm_uri} shell "dumpsys deviceidle | grep mScreenOn"', capture_output=True, text=True)
            output = output.stdout.strip()
            output = output.split("=")
            if "true" in output:

                return True

            return False

    def is_device_locked(self):
        if self.connection_manager.validate_connection():
            output = subprocess.run(
                f'adb -s {self.current_comm_uri} shell "dumpsys deviceidle | grep mScreenLocked"', capture_output=True, text=True
            )
            output = output.stdout.strip()
            output = output.split("=")
            if "true" in output:

                return True

            return False

    def get_screen_gui_xml(self):
        if self.connection_manager.validate_connection():
            device = u2.connect(self.current_comm_uri)

            return device.dump_hierarchy()