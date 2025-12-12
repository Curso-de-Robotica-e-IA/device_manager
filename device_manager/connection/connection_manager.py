import logging
import subprocess

logger = logging.getLogger(__name__)


class ConnectionManager:
    # Connection Manager has been developed based in to code available on
    # https://github.com/openatx/adbutils/issues/111#issuecomment-2094694894


    def __init__(
        self,
        subprocess_check_flag: bool = False,
    ) -> None:
        self.subprocess_check_flag = subprocess_check_flag

    @staticmethod
    def check_devices_adb_connection(
        serial_number: str,
        subprocess_check_flag: bool = False,
    ) -> bool:
        """Check if the device is connected to the adb server.
        A device is considered as connected if it does not appear
        as `offline` in the output of the `adb devices` command.

        Args:
            serial_number (str): The serial number of the device to check.
            subprocess_check_flag (bool, optional): A flag to check if the
                subprocess execution was successful, passed to the subprocess
                `check` argument. Defaults to False.
                Check the subprocess documentation for more information.

        Returns:
            bool: True if the device is connected, False otherwise.
        """
        result = subprocess.run(
            ["adb", "devices"],
            capture_output=True,
            text=True,
            check=subprocess_check_flag,
        )
        devices_lines = str(result.stdout).split("\n")
        for info_line in devices_lines:
            if serial_number in info_line and "offline" not in info_line:
                return True
        return False


class ConnectionManagerSingleton(ConnectionManager):
    """Singleton class to manage the ConnectionManager instance."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ConnectionManagerSingleton, cls).__new__(cls)
        return cls._instance
