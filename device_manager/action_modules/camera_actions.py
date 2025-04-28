import subprocess
from typing import Callable

from device_manager.connection.device_connection import DeviceConnection


class CameraActions:

    def __init__(
        self,
        device_connection: DeviceConnection,
        serial_number: str,
        subprocess_check_flag: bool,
        comm_uri: str,
        validate_connection_callback: Callable[[], bool] = lambda: True,
    ) -> None:
        self.device_connection = device_connection
        self.serial_number = serial_number
        self.subprocess_check_flag = subprocess_check_flag
        self.comm_uri = comm_uri
        self.validate_connection_callback = validate_connection_callback

    def open(self) -> None:
        """Opens the camera application."""
        if self.validate_connection_callback():
            subprocess.run(
                ['adb', '-s', self.comm_uri,
                 'shell', 'am', 'start', '-a',
                 'android.media.action.IMAGE_CAPTURE'],
                check=self.subprocess_check_flag,
            )
        else:
            raise RuntimeError(
                "Device connection is not valid. Cannot open camera.",
            )

    def open_video(self) -> None:
        """Opens the camera application in video mode."""
        if self.validate_connection_callback():
            subprocess.run(
                ['adb', '-s', self.comm_uri,
                 'shell', 'am', 'start', '-a',
                 'android.media.action.VIDEO_CAPTURE'],
                check=self.subprocess_check_flag,
            )
        else:
            raise RuntimeError(
                "Device connection is not valid. Cannot open camera.",
            )
