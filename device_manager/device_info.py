from typing import TypedDict # pyright: ignore[reportMissingTypeStubs]

from device_manager.adb_gateway import AdbGateway
from device_manager.base_device_component import BaseDeviceComponent
from device_manager.connection.device_connection import DeviceConnection
from device_manager.exceptions.errors import (
    DeviceDisconnectedError,
    UnexpectedAdbOutputError,
)
from device_manager.infos.app import AppInfo
from device_manager.utils.adb_parsers import (
    TouchscreenInfo,
    UNEXPECTED_ADB_OUTPUT,
    parse_app_path,
    parse_bool_flag,
    parse_current_activity,
    parse_display_orientation,
    parse_getprop,
    parse_installed_packages,
    parse_location_mode,
    parse_screen_dimensions,
    parse_touchscreen_devices,
)


class DeviceProperties(TypedDict):
    """TypedDict for device properties."""

    serial_number: str
    brand: str
    model: str
    android_version: str


class DeviceInfo(BaseDeviceComponent):
    """Class responsible for retrieving information from a single device.
    It is able to execute predefined actions at the device.

    Args:
        device_connection (DeviceConnection): the `DeviceConnection` object.
        serial_number (str): the serial number associated with the device.
        subprocess_check_flag (bool): the flag to check the subprocess
            execution status. Defaults to False.
            Check the subprocess documentation for more information.

    Attributes:
        current_comm_uri (str): the current communication URI for the device.

    Properties:
        - `serial_number` (str): The serial number associated with the device.

    Methods:
        actual_activity() -> str:
            Checks the device connection and executes an ADB command to obtain
            information about the top resumed activity from the Android
            activity manager. The output is captured and returned as a string.
        is_screen_on() -> bool:
            Checks if the associated device screen is on.
        is_device_locked() -> bool:
            Checks if the associated device is locked.
        get_screen_gui_xml() -> str:
            Retrieves the .xml that represents the current state of the device
            screen.
    """

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
        self._cached_properties: dict[str, str] | None = None
        self._cached_screen_dimensions: tuple[int, int] | None = None
        self._cached_touchscreens: dict[str, TouchscreenInfo] | None = None
        self._cached_touchscreen_events: list[str] | None = None

    def _query_adb(self, command: str) -> str | None:
        """Try-first ADB shell query: runs directly and only validates/reconnects on failure."""
        result = self._run_adb(command, capture_output=True)
        if result.returncode == 0:
            return result.stdout
        if not self.device_connection.validate_connection(
            self._serial_number,
            force_reconnect=True,
        ):
            return None
        retry = self._run_adb(command, capture_output=True)
        return retry.stdout if retry.returncode == 0 else None

    def actual_activity(self) -> str | None:
        """
        This method checks the device connection and executes an ADB command
        to obtain information about the top resumed activity from the Android
        activity manager. The output is captured and returned as a string.

        Returns:
            str: The name of the currently resumed activity.
        """
        output = self._query_adb('dumpsys activity activities')
        if output is None:
            return None
        return parse_current_activity(output)

    def is_screen_on(self) -> bool:
        """This method checks if the associated device screen is on.

        Returns:
            bool: True if the screen is on, false otherwise.
        """
        output = self._query_adb('dumpsys deviceidle')
        if output is None:
            raise UnexpectedAdbOutputError(UNEXPECTED_ADB_OUTPUT)
        return parse_bool_flag(output, 'mScreenOn')

    def is_device_locked(self) -> bool:
        """This method checks if the associated device is locked.

        Returns:
            bool: True if the device is locked, false otherwise.
        """
        output = self._query_adb('dumpsys deviceidle')
        if output is None:
            raise UnexpectedAdbOutputError(UNEXPECTED_ADB_OUTPUT)
        return parse_bool_flag(output, 'mScreenLocked')

    def get_screen_state(self) -> tuple[bool, bool]:
        """Returns `(is_screen_on, is_device_locked)` using a single `dumpsys deviceidle` call."""
        output = self._query_adb('dumpsys deviceidle')
        if output is None:
            raise UnexpectedAdbOutputError(UNEXPECTED_ADB_OUTPUT)
        return (
            parse_bool_flag(output, 'mScreenOn'),
            parse_bool_flag(output, 'mScreenLocked'),
        )

    def get_screen_gui_xml(self) -> str | None:
        """Retrieves the UI hierarchy XML for the current screen via native ADB."""
        output = self._query_adb('uiautomator dump /dev/tty')
        if output is None:
            return None
        xml_start = output.find('<?xml')
        if xml_start != -1:
            return output[xml_start:]

        fallback = self._query_adb(
            'uiautomator dump /sdcard/window_dump.xml && '
            'cat /sdcard/window_dump.xml && rm -f /sdcard/window_dump.xml'
        )
        if fallback is None:
            return None
        xml_start = fallback.find('<?xml')
        return fallback[xml_start:] if xml_start != -1 else None

    def get_properties(
        self,
        extra_keys: list[str] | None = None,
        refresh: bool = False,
    ) -> dict[str, str]:
        """Retrieves device properties (cached on the instance when `extra_keys` is None)."""
        if (
            extra_keys is None
            and not refresh
            and self._cached_properties is not None
        ):
            return dict(self._cached_properties)

        output = self._query_adb('getprop')
        if output is None:
            raise UnexpectedAdbOutputError(UNEXPECTED_ADB_OUTPUT)
        base_result = parse_getprop(output, extra_keys=extra_keys)
        props = DeviceProperties(**base_result)  # pyright: ignore[reportReturnType]
        if extra_keys is None:
            self._cached_properties = dict(props)
        return props

    def get_screen_dimensions(self, refresh: bool = False) -> tuple[int, int]:
        """Gets the dimensions of the device screen (cached on the instance)."""
        if not refresh and self._cached_screen_dimensions is not None:
            return self._cached_screen_dimensions
        output = self._query_adb('wm size')
        if output is None:
            raise UnexpectedAdbOutputError(UNEXPECTED_ADB_OUTPUT)
        self._cached_screen_dimensions = parse_screen_dimensions(output)
        return self._cached_screen_dimensions

    def app(self, package: str) -> AppInfo:
        """Returns an instance of AppInfo for the specified package.

        Args:
            package (str): The package name of the application.

        Returns:
            AppInfo: An instance of AppInfo for the specified package.
        """
        return AppInfo(
            package=package,
            device_connection=self.device_connection,
            serial_number=self._serial_number,
            subprocess_check_flag=self.subprocess_check_flag,
        )

    def get_display_orientation(self) -> str:
        """Gets the current orientation of the device.

        Returns:
            str: The current orientation of the device [Portrait, Landscape, Reverse Portrait or Reverse Landscape ].
        """
        output = self._query_adb('dumpsys display')
        if output is None:
            raise DeviceDisconnectedError('Device not connected')
        return parse_display_orientation(output)

    def list_installed_all_apps(self) -> list[str]:
        """Lists installed applications on the device.

        Returns:
            list[str]: A list with application package names.
        """
        output = self._query_adb('pm list packages')
        if output is None:
            return []
        return parse_installed_packages(output)

    def is_app_installed(self, package_name: str) -> bool:
        """Checks if an application is installed on the device.

        Args:
            package_name (str): The package name of the application to check.

        Returns:
            bool: True if the application is installed, False otherwise.
        """
        if self.device_connection.validate_connection(
            self._serial_number,
            force_reconnect=True,
        ):
            installed_apps = self.list_installed_all_apps()
            return package_name in installed_apps
        return False

    def get_app_path(self, package_name: str) -> str | None:
        """Gets the installation path of an application on the device.

        Args:
            package_name (str): The package name of the application.

        Returns:
            Optional[str]: The full path to the APK file on the device,
                or None if the app is not installed.
        """
        output = self._query_adb(f'pm path {package_name}')
        if output is None:
            return None
        return parse_app_path(output)

    def get_location_mode(self) -> str | None:
        """Return the current location mode reported by the device.

        This method runs ``adb shell settings get secure location_mode`` and
        converts the numeric response into a human-readable label.

        Returns:
            Optional[str]: One of ``'Off'``, ``'Sensors Only'``,
                ``'Battery Saving'`` or ``'High Accuracy'``. Returns ``None``
                when the device cannot be queried or when the value is not
                recognized.

        Location mode values:
            0: Off
            1: Sensors Only
            2: Battery Saving
            3: High Accuracy
        """
        output = self._query_adb('settings get secure location_mode')
        if output is None:
            return None
        return parse_location_mode(output)

    def is_stay_awake_enabled(self) -> bool:
        """Checks if the "Stay Awake" developer option is enabled on the device.

        Returns:
            bool: True if "Stay Awake" is enabled, False otherwise.
        """
        output = self._query_adb('settings get global stay_on_while_plugged_in')
        if output is None:
            return False
        return output.strip() != '0'

    def is_airplane_mode_enabled(self) -> bool:
        """Gets the current airplane mode status of the device.

        Returns:
            bool: True if airplane mode is enabled, False otherwise.
        """
        output = self._query_adb('settings get global airplane_mode_on')
        if output is None:
            return False
        return output.strip() == '1'

    def get_device_model(self, refresh: bool = False) -> str:
        """Returns `'brand model'` from cached device properties."""
        props = self.get_properties(refresh=refresh)
        brand = props.get('brand', '').strip()
        model = props.get('model', '').strip()
        return f'{brand} {model}'.strip() if (brand or model) else 'unknown'

    def is_app_running(self, package_name: str) -> bool:
        """Checks whether `package_name` currently has an active process (`pidof`)."""
        output = self._query_adb(f'pidof {package_name}')
        return bool(output and output.strip())

    def get_all_touchscreens(
        self, refresh: bool = False
    ) -> dict[str, TouchscreenInfo]:
        """Returns all detected touchscreen devices mapped by `/dev/input/` node."""
        if not refresh and self._cached_touchscreens is not None:
            return dict(self._cached_touchscreens)
        output = self._query_adb('getevent -p -l')
        if not output:
            return {}
        touch_map, nodes = parse_touchscreen_devices(output)
        self._cached_touchscreens = touch_map
        self._cached_touchscreen_events = nodes
        return dict(touch_map)

    def get_touchscreen_events(self, refresh: bool = False) -> list[str]:
        """Returns prioritized touchscreen event nodes (direct touch first)."""
        if not refresh and self._cached_touchscreen_events is not None:
            return list(self._cached_touchscreen_events)
        self.get_all_touchscreens(refresh=refresh)
        return list(self._cached_touchscreen_events or [])

    def get_touchscreen_info(self, refresh: bool = False) -> TouchscreenInfo:
        """Returns the primary touchscreen info, or a safe fallback if undetected."""
        touch_map = self.get_all_touchscreens(refresh=refresh)
        events = self._cached_touchscreen_events or []
        if events and events[0] in touch_map:
            return touch_map[events[0]]
        return TouchscreenInfo(
            node='event8', name='', x_range=(0, 0), y_range=(0, 0)
        )

    def get_touch_axis_ranges(
        self, event_node: str | None = None
    ) -> tuple[tuple[int, int], tuple[int, int]]:
        """Returns `(x_range, y_range)` for `event_node` or the primary touchscreen."""
        touch_map = self.get_all_touchscreens()
        if event_node is not None:
            clean = event_node.rsplit('/', 1)[-1]
            if clean in touch_map:
                info = touch_map[clean]
                return info.x_range, info.y_range
            return (0, 0), (0, 0)
        primary = self.get_touchscreen_info()
        return primary.x_range, primary.y_range
