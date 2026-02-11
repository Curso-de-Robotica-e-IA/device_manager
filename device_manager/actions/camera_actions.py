from pathlib import Path
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
            image_name (str): The name of the image file to be retrieved from
                the device.
            source (Union[str, Path]): The source path on the device.
            destination (Union[str, Path]): The destination path on the local
                machine.
        """
        destination, source = self._verify_path_exists_and_create_if_not(destination, source)
        try:
            if self.validate_connection_callback(): #TODO see the Gonça PR
                remote_path = f'{source}/{image_name}' # build remote file path from device source and image name turned into string
                local_path = str(destination.resolve()) # turn into absolute path string
                
                result = execute_adb_command(
                    command=f'pull {remote_path} {local_path}',
                    comm_uris=[self.comm_uri],
                    shell=False,
                    subprocess_check_flag=self.subprocess_check_flag,
                    capture_output=True,
                ).stdout
                
                # Verify that only one file was pulled
                if 'file pulled' in result and '1 file pulled' not in result:
                    # If more than one file was pulled, this might indicate a problem
                    matches = grep(result, r'(\d+) file')
                    if matches and int(matches[0]) > 1:
                        raise RuntimeError(
                            f'Multiple files were pulled ({matches[0]}). Expected only one file: {image_name}',
                        )
            else:
                raise RuntimeError(
                    'Device connection is not valid. Cannot pull image.',
                )
        except Exception as e:
            raise RuntimeError(
                f'Failed to pull image: {e}',
            ) from e
        
    def _verify_path_exists_and_create_if_not(
            self, 
            destination: Union[str, Path],
            source: Union[str, Path]
        ) -> tuple[Path, Path]:
        """Verifies if a path exists on the local machine and creates it if it
        does not exist.

        Args:
            **destination** (Union[str, Path]): The destination path on the local machine.
            **source** (Union[str, Path]): The source path on the device.

        Returns: tupel[Path, Path]: The resolved **destination** and **source** paths as Path objects.
        """

        destination = Path(destination).resolve()
        source = Path(source).as_posix()
        try:            
            if not destination.exists() or not destination.is_dir():
                # create destination directory if it doesn't exist
                destination.mkdir(parents=True, exist_ok=True)       
        except PermissionError as e:
            raise RuntimeError(
                f'Permission denied when creating destination directory: {destination}',
            ) from e
        except ValueError as e:
            raise RuntimeError(
                f'Invalid destination path: {destination}',
            ) from e
        except OSError as e:
            raise RuntimeError(
                f'Failed to create destination directory: {destination} - {e}',
            ) from e
        
        return destination, source
