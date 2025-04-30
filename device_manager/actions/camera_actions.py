import subprocess
from pathlib import Path
from typing import Callable, Union

from device_manager.connection.device_connection import DeviceConnection
from device_manager.enumerations.adb_keyevents import ADBKeyEvent


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
                 'android.media.action.STILL_IMAGE_CAMERA'],
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
                 'android.media.action.VIDEO_CAMERA'],
                check=self.subprocess_check_flag,
            )
        else:
            raise RuntimeError(
                "Device connection is not valid. Cannot open camera.",
            )

    def close(self) -> None:
        """Closes the camera application."""
        if self.validate_connection_callback():
            subprocess.run(
                ['adb', '-s', self.comm_uri,
                 'shell', 'am', 'force-stop',
                 'com.android.camera'],
                check=self.subprocess_check_flag,
            )
        else:
            raise RuntimeError(
                "Device connection is not valid. Cannot close camera.",
            )

    def take_picture(self) -> None:
        """Takes a picture using the camera."""
        if self.validate_connection_callback():
            subprocess.run(
                ['adb', '-s', self.comm_uri,
                 'shell', 'input', 'keyevent',
                 ADBKeyEvent.KEYCODE_ENTER.value],
                check=self.subprocess_check_flag,
            )
        else:
            raise RuntimeError(
                "Device connection is not valid. Cannot take picture.",
            )

    def clear_pictures(self) -> None:
        """Clears the pictures from the device."""
        if self.validate_connection_callback():
            subprocess.run(
                ['adb', '-s', self.comm_uri,
                 'shell', 'rm', '-rf',
                 '/sdcard/DCIM/Camera/*'],
                check=self.subprocess_check_flag,
            )
        else:
            raise RuntimeError(
                "Device connection is not valid. Cannot clear pictures.",
            )

    def pull_pictures(
        self,
        destination: Union[str, Path],
        amount: int = 1,
    ) -> None:
        """Pulls the last taken pictures from the device to the local machine.

        Args:
            destination (Union[str, Path]): The destination path on the local
                machine.
            amount (int): The number of pictures to pull. Default is 1.
        """
        try:
            if isinstance(destination, str):
                destination = Path(destination)
            if not destination.exists():
                destination.mkdir(parents=True, exist_ok=True)
            if not destination.is_dir():
                raise ValueError(
                    "Destination must be a directory.",
                )
        except Exception as e:
            raise RuntimeError(
                f"Failed to create destination directory: {e}",
            ) from e
        try:
            if self.validate_connection_callback():
                result = subprocess.run(
                    ['adb', '-s', self.comm_uri,
                     'shell', 'ls', '-t',
                     '/sdcard/DCIM/Camera'],
                    check=self.subprocess_check_flag,
                    capture_output=True,
                )
                print(result)
                files = result.stdout.decode().splitlines()
                files = files[:amount]
                for file in files:
                    subprocess.run(
                        ['adb', '-s', self.comm_uri,
                         'pull',
                         f'/sdcard/DCIM/Camera/{file}',
                         str(destination.resolve())],
                        check=self.subprocess_check_flag,
                    )
            else:
                raise RuntimeError(
                    "Device connection is not valid. Cannot pull pictures.",
                )
        except Exception as e:
            raise RuntimeError(
                f"Failed to pull pictures: {e}",
            ) from e
