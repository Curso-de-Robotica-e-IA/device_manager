import re
from pathlib import Path, PurePosixPath
from typing import Callable

from device_manager.adb_gateway import AdbGateway
from device_manager.base_device_component import (
    BaseDeviceComponent,
    require_connection,
)
from device_manager.connection.device_connection import DeviceConnection
from device_manager.enumerations.adb_keyevents import ADBKeyEvent
from device_manager.enumerations.camera import CameraIntents
from device_manager.exceptions.errors import DeviceDisconnectedError
from device_manager.utils.util_functions import grep


class CameraActions(BaseDeviceComponent):
    def __init__(
        self,
        device_connection: DeviceConnection,
        serial_number: str,
        subprocess_check_flag: bool,
        comm_uri: str,
        validate_connection_callback: Callable[[], bool] = lambda: True,
        gateway: AdbGateway | None = None,
    ) -> None:
        super().__init__(
            device_connection=device_connection,
            serial_number=serial_number,
            subprocess_check_flag=subprocess_check_flag,
            gateway=gateway,
        )
        self._comm_uri = comm_uri
        self.validate_connection_callback = validate_connection_callback

    @property
    def current_comm_uri(self) -> str:
        """The current communication URI for the device, resolved dynamically."""
        try:
            return self.device_connection.build_comm_uri(self._serial_number)
        except ValueError:
            return self._comm_uri

    def validate_connection(self) -> bool:
        return self.validate_connection_callback()

    @require_connection(
        raise_on_disconnect=True,
        error_message='Device connection is not valid. Cannot open camera.',
    )
    def open(self) -> None:
        """Opens the camera application."""
        self._run_adb(
            f'am start -a {CameraIntents.ACTION_STILL_IMAGE_CAMERA}',
        )

    @require_connection(
        raise_on_disconnect=True,
        error_message='Device connection is not valid. Cannot open camera.',
    )
    def open_video(self) -> None:
        """Opens the camera application in video mode."""
        self._run_adb(
            f'am start -a {CameraIntents.ACTION_VIDEO_CAMERA}',
        )

    @require_connection(
        raise_on_disconnect=True,
        error_message='Device connection is not valid. Cannot close camera.',
    )
    def close(self) -> None:
        """Closes the camera application."""
        self._run_adb('am force-stop com.android.camera')

    @require_connection(
        raise_on_disconnect=True,
        error_message='Device connection is not valid. Cannot get camera package.',
    )
    def package(self) -> str:
        """Returns the package name of the camera application."""
        result = self._run_adb(
            f'cmd package resolve-activity --brief -a {CameraIntents.ACTION_IMAGE_CAPTURE}',
            capture_output=True,
        ).stdout
        activity = grep(result, 'com.(.*)/')[0].strip()
        return activity.split('/')[0]

    @require_connection(
        raise_on_disconnect=True,
        error_message='Device connection is not valid. Cannot take picture.',
    )
    def take_picture(self) -> None:
        """Takes a picture using the camera."""
        self._run_adb(
            f'input keyevent {ADBKeyEvent.KEYCODE_ENTER.value}',
        )

    def clear_pictures(
        self,
        source: str | Path | None = '/sdcard/DCIM/Camera/*',
    ) -> None:
        """Removes all pictures from the specified directory on the device."""
        if source is not None:
            source_posix = (
                source.as_posix()
                if isinstance(source, Path)
                else Path(source).as_posix()
            )
        else:
            raise ValueError('Source path invalid.')

        if not self.validate_connection():
            raise DeviceDisconnectedError(
                'Device connection is not valid. Cannot clear pictures.',
            )
        self._run_adb(f'rm -rf {source_posix}')

    def pull_pictures(
        self,
        destination: str | Path,
        amount: int = 1,
    ) -> None:
        """Pulls the last taken pictures from the device to the local machine."""
        try:
            if isinstance(destination, str):
                destination = Path(destination)
            if not destination.exists():
                destination.mkdir(parents=True, exist_ok=True)
            if not destination.is_dir():
                raise ValueError('Destination must be a directory.')
        except Exception as e:
            raise RuntimeError(
                f'Failed to create destination directory: {e}',
            ) from e
        try:
            if not self.validate_connection():
                raise DeviceDisconnectedError(
                    'Device connection is not valid. Cannot pull pictures.',
                )
            result = self._run_adb(
                'ls -t /sdcard/DCIM/Camera',
                capture_output=True,
            )
            files = result.stdout.splitlines()[:amount]
            for file in files:
                self._run_adb(
                    f'pull /sdcard/DCIM/Camera/{file} {destination.resolve()}',
                    shell=False,
                )
        except Exception as e:
            raise RuntimeError(f'Failed to pull pictures: {e}') from e

    def pull_picture_by_name(
        self,
        image_name: str,
        destination: str | Path,
        source: str | Path = Path('/sdcard/DCIM/Camera'),
    ) -> None:
        """Pulls a specific image from the device."""
        destination_dir = self._verify_path_exists_and_create_if_not(
            destination
        )
        remote_path = (PurePosixPath(source) / image_name).as_posix()
        local_path = str((destination_dir / image_name).resolve())

        if not self.validate_connection():
            raise DeviceDisconnectedError(
                'Device connection is not valid. Cannot pull image.',
            )

        try:
            command = f'pull "{remote_path}" "{local_path}"'
            result = self._run_adb(
                command,
                shell=False,
                capture_output=True,
            ).stdout
            self._validate_adb_pull_output(result, image_name)
        except Exception as e:
            raise RuntimeError(
                f"Failed to pull image '{image_name}': {e}"
            ) from e

    def _validate_adb_pull_output(self, output: str, image_name: str) -> None:
        match = re.search(r'(\d+)\s+file[s]?\s+pulled', output)
        if match:
            count = int(match.group(1))
            if count == 0:
                raise RuntimeError(
                    f"File not found on device or 0 files pulled: '{image_name}'"
                )
            if count > 1:
                raise RuntimeError(
                    f"Multiple files were pulled ({count}). Expected only 1: '{image_name}'"
                )
        elif '0 files pulled' in output or 'error' in output.lower():
            raise RuntimeError(
                f'ADB pull failed or file not found: {output.strip()}'
            )

    def _verify_path_exists_and_create_if_not(
        self,
        path: str | Path,
    ) -> Path:
        resolved_path = Path(path).resolve()
        try:
            resolved_path.mkdir(parents=True, exist_ok=True)
        except (PermissionError, ValueError, OSError) as e:
            raise RuntimeError(
                f"Failed to ensure destination directory '{resolved_path}': {e}"
            ) from e
        return resolved_path
