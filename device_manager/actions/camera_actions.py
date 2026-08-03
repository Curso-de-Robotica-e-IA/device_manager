from pathlib import Path, PurePosixPath
from typing import Callable, Optional, Union

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

    def clear_pictures(self, source: Union[str, Path] = "/sdcard/DCIM/Camera/*") -> None:
        """
        Removes all pictures from the specified directory on the device.

        Args:
            source (Union[str, Path]): The path to the directory containing pictures on the device. Defaults to '/sdcard/DCIM/Camera/*'.

        Raises:
            ValueError: If the source path is invalid.
            RuntimeError: If the device connection is not valid or if the operation fails.
        """
        if source is not None:
            if isinstance(source, Path):
                # Convert to POSIX string for ADB because ADB expects Unix-style paths
                source = source.as_posix()
            else:
                source = Path(source).as_posix()
        else:
            raise ValueError('Source path invalid.')     

        if self.validate_connection_callback():
            execute_adb_command(
                command= f'rm -rf {source}',
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
        
    def pull_picture_by_name(
        self,
        image_name: str,
        destination: Union[str, Path],
        source: Union[str, Path] = Path("/sdcard/DCIM/Camera"),
    ) -> None:
        """Pulls a specific image from the device.

        Args:
            image_name (str): The name of the image file to be retrieved.
            destination (Union[str, Path]): Local directory destination.
            source (Union[str, Path]): Source directory on the device.
        """
        destination_dir = self._verify_path_exists_and_create_if_not(destination)
        remote_path = (PurePosixPath(source) / image_name).as_posix()
        local_path = str((destination_dir / image_name).resolve())

        if not self.validate_connection_callback():
            raise RuntimeError("Device connection is not valid. Cannot pull image.")

        try:
            command = f'pull "{remote_path}" "{local_path}"'
            
            result = execute_adb_command(
                command=command,
                comm_uris=[self.comm_uri],
                shell=False,
                subprocess_check_flag=self.subprocess_check_flag,
                capture_output=True,
            ).stdout

            self._validate_adb_pull_output(result, image_name)

        except Exception as e:
            raise RuntimeError(f"Failed to pull image '{image_name}': {e}") from e
        
    def _validate_adb_pull_output(self, output: str, image_name: str) -> None:
        """Verify that only one file was pulled.
        """
        match = re.search(r"(\d+)\s+file[s]?\s+pulled", output)
        if match:
            count = int(match.group(1))
            if count == 0:
                raise RuntimeError(f"File not found on device or 0 files pulled: '{image_name}'")
            if count > 1:
                raise RuntimeError(f"Multiple files were pulled ({count}). Expected only 1: '{image_name}'")
        elif "0 files pulled" in output or "error" in output.lower():
            raise RuntimeError(f"ADB pull failed or file not found: {output.strip()}")

    def _verify_path_exists_and_create_if_not(
        self,
        path: Union[str, Path],
    ) -> Path:
        """Verifies if a local directory exists and creates it if needed.

        Args:
            path (Union[str, Path]): Target path on local machine.

        Returns:
            Path: The resolved directory path.
        """
        resolved_path = Path(path).resolve()
        try:
            resolved_path.mkdir(parents=True, exist_ok=True)
        except (PermissionError, ValueError, OSError) as e:
            raise RuntimeError(f"Failed to ensure destination directory '{resolved_path}': {e}") from e

        return resolved_path
