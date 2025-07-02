from pathlib import Path
from typing import Callable, Union

from device_manager.adb_executor import execute_adb_command
from device_manager.connection.device_connection import DeviceConnection
from device_manager.enumerations.adb_keyevents import ADBKeyEvent
from device_manager.enumerations.camera import CameraIntents
from device_manager.utils.util_functions import grep


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
            execute_adb_command(
                command=f'am start -a {CameraIntents.ACTION_STILL_IMAGE_CAMERA}',  # noqa: E501
                comm_uris=[self.comm_uri],
                shell=True,
                subprocess_check_flag=self.subprocess_check_flag,
            )
        else:
            raise RuntimeError(
                'Device connection is not valid. Cannot open camera.',
            )

    def open_video(self) -> None:
        """Opens the camera application in video mode."""
        if self.validate_connection_callback():
            execute_adb_command(
                command=f'am start -a {CameraIntents.ACTION_VIDEO_CAMERA}',
                comm_uris=[self.comm_uri],
                shell=True,
                subprocess_check_flag=self.subprocess_check_flag,
            )
        else:
            raise RuntimeError(
                'Device connection is not valid. Cannot open camera.',
            )

    def close(self) -> None:
        """Closes the camera application."""
        if self.validate_connection_callback():
            execute_adb_command(
                command='am force-stop com.android.camera',
                comm_uris=[self.comm_uri],
                shell=True,
                subprocess_check_flag=self.subprocess_check_flag,
            )
        else:
            raise RuntimeError(
                'Device connection is not valid. Cannot close camera.',
            )

    def package(self) -> str:
        """Returns the package name of the camera application."""
        if self.validate_connection_callback():
            result = execute_adb_command(
                command=f'cmd package resolve-activity --brief -a {CameraIntents.ACTION_IMAGE_CAPTURE}',  # noqa: E501
                comm_uris=[self.comm_uri],
                shell=True,
                subprocess_check_flag=self.subprocess_check_flag,
                capture_output=True,
            ).stdout
            activity = grep(result, 'com.(.*)/')[0].strip()
            package = activity.split('/')[0]
            return package
        else:
            raise RuntimeError(
                'Device connection is not valid. Cannot get camera package.',
            )

    def take_picture(self) -> None:
        """Takes a picture using the camera."""
        if self.validate_connection_callback():
            execute_adb_command(
                command=f'input keyevent {ADBKeyEvent.KEYCODE_ENTER.value}',
                comm_uris=[self.comm_uri],
                shell=True,
                subprocess_check_flag=self.subprocess_check_flag,
            )
        else:
            raise RuntimeError(
                'Device connection is not valid. Cannot take picture.',
            )

    def clear_pictures(self) -> None:
        """Clears the pictures from the device."""
        if self.validate_connection_callback():
            execute_adb_command(
                command='rm -rf /sdcard/DCIM/Camera/*',
                comm_uris=[self.comm_uri],
                shell=True,
                subprocess_check_flag=self.subprocess_check_flag,
            )
        else:
            raise RuntimeError(
                'Device connection is not valid. Cannot clear pictures.',
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
                    'Destination must be a directory.',
                )
        except Exception as e:
            raise RuntimeError(
                f'Failed to create destination directory: {e}',
            ) from e
        try:
            if self.validate_connection_callback():
                result = execute_adb_command(
                    command='ls -t /sdcard/DCIM/Camera',
                    comm_uris=[self.comm_uri],
                    shell=True,
                    subprocess_check_flag=self.subprocess_check_flag,
                    capture_output=True,
                )
                files = result.stdout.splitlines()
                files = files[:amount]
                for file in files:
                    execute_adb_command(
                        command=f'pull /sdcard/DCIM/Camera/{file} {destination.resolve()}',  # noqa: E501
                        comm_uris=[self.comm_uri],
                        subprocess_check_flag=self.subprocess_check_flag,
                    )
            else:
                raise RuntimeError(
                    'Device connection is not valid. Cannot pull pictures.',
                )
        except Exception as e:
            raise RuntimeError(
                f'Failed to pull pictures: {e}',
            ) from e
