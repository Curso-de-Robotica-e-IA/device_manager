from pathlib import Path
import subprocess
from typing import Optional

from device_manager.actions.camera_actions import CameraActions
from device_manager.adb_gateway import AdbGateway, resolve_gateway
from device_manager.base_device_component import (
    BaseDeviceComponent,
    require_connection,
)
from device_manager.connection.device_connection import DeviceConnection
from device_manager.enumerations.adb_keyevents import ADBKeyEvent
from device_manager.exceptions.errors import DeviceDisconnectedError
from device_manager.utils.adb_parsers import (
    find_text_bounds_center,
    parse_bool_flag,
)


class DeviceActions(BaseDeviceComponent):
    """Executes predefined ADB interaction commands on a single device."""

    def __init__(
        self,
        device_connection: DeviceConnection,
        serial_number: str,
        subprocess_check_flag: bool = False,
        gateway: AdbGateway | None = None,
    ):
        super().__init__(
            device_connection=device_connection,
            serial_number=serial_number,
            subprocess_check_flag=subprocess_check_flag,
            gateway=gateway,
        )
        self.camera = CameraActions(
            device_connection=self.device_connection,
            serial_number=self._serial_number,
            subprocess_check_flag=self.subprocess_check_flag,
            comm_uri=self.current_comm_uri,
            validate_connection_callback=self.validate_connection,
        )

    def validate_connection(self) -> bool:
        """Validates the connection to the device.

        Returns:
            bool: True if the connection is valid, False otherwise.
        """
        return self.device_connection.validate_connection(
            self._serial_number,
            force_reconnect=False,
        )

    @require_connection(raise_on_disconnect=True)
    def click_by_coordinates(self, x: int, y: int) -> None:
        """Simulates a tap at the provided (x, y) coordinates."""
        self._run_adb(f'input tap {x} {y}')

    @require_connection(raise_on_disconnect=True)
    def click_by_text(
        self,
        text: str,
        *,
        exact: bool = False,
        xml_content: str | None = None,
    ) -> bool:
        """Finds a UI element by text/content-desc in the screen XML and taps its center."""
        if xml_content is None:
            res = self._run_adb('uiautomator dump /dev/tty', capture_output=True)
            out = res.stdout or ''
            xml_start = out.find('<?xml')
            xml_content = out[xml_start:] if xml_start != -1 else ''

        center = find_text_bounds_center(xml_content, text, exact=exact)
        if center is None:
            return False
        self._run_adb(f'input tap {center[0]} {center[1]}')
        return True

    @require_connection(raise_on_disconnect=True)
    def swipe(self, x1: int, y1: int, x2: int, y2: int, time: int) -> None:
        """Inputs a swipe gesture on the device screen."""
        self._run_adb(f'input swipe {x1} {y1} {x2} {y2} {time}')

    def _open_app_one_arg(self, package_activity: str) -> None:
        self._run_adb(f'am start -n {package_activity}')

    def _open_app_two_args(
        self,
        package_name: str,
        activity_name: str,
    ) -> None:
        self._run_adb(f'am start -n {package_name}/{activity_name}')

    @require_connection(raise_on_disconnect=True)
    def open_app(
        self,
        package_name: str,
        activity_name: Optional[str] = None,
    ) -> None:
        """Opens an application on the device."""
        if activity_name is None:
            self._open_app_one_arg(package_name)
        else:
            self._open_app_two_args(package_name, activity_name)

    @require_connection(raise_on_disconnect=True)
    def close_app(self, package_name: str) -> None:
        """Closes an application on the device using the provided package name."""
        self._run_adb(f'am force-stop {package_name}')

    def install_apk(
        self,
        apk_path: str,
        replace: bool = False,
    ) -> None:
        """Installs an APK file on the device."""
        path = Path(apk_path)
        if not path.exists():
            raise FileNotFoundError(f'File not found: {apk_path}')

        if self.validate_connection():
            apk_file_path = (path.resolve()).as_posix()
            command = (
                f'install -r -g {apk_file_path}'
                if replace
                else f'install {apk_file_path}'
            )
            self._run_adb(command, shell=False)

    @require_connection(raise_on_disconnect=True)
    def uninstall_apk(self, package_name: str) -> None:
        """Uninstalls an APK from the device."""
        self._run_adb(f'pm uninstall --user 0 {package_name}')

    @require_connection(raise_on_disconnect=True)
    def turn_on_screen(self) -> None:
        """Executes `keyevent KEYCODE_POWER`."""
        self._run_adb(f'input keyevent {ADBKeyEvent.KEYCODE_POWER.value}')

    @require_connection(raise_on_disconnect=True)
    def unlock_screen(self, fallback_swipe: bool = True) -> None:
        """Unlocks the screen using `KEYCODE_MENU`, with swipe fallback if still locked."""
        self._run_adb(f'input keyevent {ADBKeyEvent.KEYCODE_MENU.value}')
        if not fallback_swipe:
            return
        res = self._run_adb('dumpsys deviceidle', capture_output=True)
        try:
            still_locked = parse_bool_flag(res.stdout or '', 'mScreenLocked')
        except ValueError:
            still_locked = False
        if still_locked:
            self._run_adb('wm dismiss-keyguard')
            self._run_adb('input swipe 500 1800 500 400 300')

    def turn_on_and_unlock_screen(self) -> None:
        """Turns on and unlocks the device screen."""
        self.turn_on_screen()
        self.unlock_screen()

    @require_connection(raise_on_disconnect=True)
    def home_button(self) -> None:
        """Executes `keyevent KEYCODE_HOME`."""
        self._run_adb(f'input keyevent {ADBKeyEvent.KEYCODE_HOME.value}')

    @require_connection(raise_on_disconnect=True)
    def screen_shot(
        self,
        image_name: str = 'screen',
        destination: str = '/sdcard',
    ) -> None:
        """Takes a screenshot of the device screen."""
        self._run_adb(f'screencap -p {destination}/{image_name}.png')

    @require_connection(raise_on_disconnect=True)
    def remove_file(self, remote_path: Path) -> None:
        """Removes a file from the device."""
        self._run_adb(f'rm {remote_path}')

    def safe_screencap_bytes(self) -> bytes | None:
        """Takes a screenshot and returns PNG bytes via try-first `adb exec-out`."""
        gateway = resolve_gateway(self._gateway, subprocess.run)
        cmd = [
            'adb',
            '-s',
            self.current_comm_uri,
            'exec-out',
            'screencap',
            '-p',
        ]
        result = gateway.run(
            cmd,
            capture_output=True,
            check=self.subprocess_check_flag,
        )
        if result.returncode != 0 or not result.stdout:
            if not self.validate_connection():
                raise DeviceDisconnectedError('Device not connected')
            result = gateway.run(
                cmd,
                capture_output=True,
                check=self.subprocess_check_flag,
            )
            if result.returncode != 0 or not result.stdout:
                return None

        return result.stdout

    @require_connection(raise_on_disconnect=True)
    def push_file(
        self,
        local_path: str,
        remote_path: str,
    ) -> None:
        """Pushes a file from the local machine to the device."""
        self._run_adb(f'push {local_path} {remote_path}', shell=False)

    @require_connection(raise_on_disconnect=True)
    def pull_file(
        self,
        remote_path: Path,
        local_path: Path,
    ) -> None:
        """Pulls a file from the device to the local machine."""
        self._run_adb(f'pull {remote_path} {local_path}', shell=False)

    @require_connection(raise_on_disconnect=True)
    def back(self) -> None:
        """Executes `keyevent KEYCODE_BACK`."""
        self._run_adb(f'input keyevent {ADBKeyEvent.KEYCODE_BACK.value}')

    @require_connection(raise_on_disconnect=True)
    def set_location_mode(self, mode: str) -> None:
        """Sets the location mode on the device."""
        if mode not in ['0', '1', '2', '3']:
            raise ValueError("Invalid mode. Valid values are '0', '1', '2', '3'.")
        self._run_adb(f'settings put secure location_mode {mode}')

    @require_connection(raise_on_disconnect=True)
    def set_stay_awake(self, enabled: bool) -> None:
        """Sets the Stay Awake developer option on the device."""
        value = '3' if enabled else '0'
        self._run_adb(f'settings put global stay_on_while_plugged_in {value}')

    @require_connection(raise_on_disconnect=True)
    def set_air_plane_mode(self, enabled: bool) -> None:
        """Enables or disables airplane mode on the device."""
        action = 'enable' if enabled else 'disable'
        self._run_adb(f'cmd connectivity airplane-mode {action}')

    @require_connection(raise_on_disconnect=True)
    def set_accelerometer_rotation(self, enable: bool) -> None:
        """Enables or disables accelerometer-based screen rotation."""
        rotation_value = 1 if enable else 0
        self._run_adb(
            f'settings put system accelerometer_rotation {rotation_value}'
        )
