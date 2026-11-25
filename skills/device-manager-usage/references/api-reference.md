# `device_manager` v2.0.0 Public API Reference

## Top-Level Exports (`device_manager`)
- `DeviceManager`
- `DeviceActions`
- `DeviceInfo`
- `AdbPairing`
- `AdbConnectionDiscovery`
- `get_device_manager(*args, **kwargs) -> DeviceManager`
- `reset_device_manager() -> None`

---

## `DeviceManager` (`device_manager.manager`)

```python
DeviceManager(
    subprocess_check_flag: bool = False,
    fixed_port: int = 5555,
    check_dependencies: bool = True,
    connector: DeviceConnection | None = None,
    ui_backend: UiHierarchyBackend | None = None,
)
```

- **Properties & container protocol:**
  - `connected_devices -> list[str]`
  - `dm[serial] -> tuple[DeviceInfo, DeviceActions]` (raises `DeviceNotFoundError`)
  - `serial in dm -> bool`, `len(dm) -> int`, `del dm[serial]`
  - `iter(dm) -> Iterator[DeviceObjects(serial_number, device_info, device_actions)]`
  - Context manager: `with DeviceManager(...) as dm:` calls `dm.close()` on exit.
- **Methods:**
  - `load_connected_usb_devices() -> None`
  - `connect_devices(*serial_numbers: str) -> list[str]`
  - `disconnect_devices(*serial_number: str) -> bool`
  - `get_device_info(serial_number: str) -> DeviceInfo | None`
  - `get_device_actions(serial_number: str) -> DeviceActions | None`
  - `is_connected(serial_number: str) -> bool`
  - `execute_adb_command(command: str, comm_uris: list[str] | None = None, shell: bool = True, subprocess_check_flag: bool = False, capture_output: bool = False, **kwargs: str) -> CompletedProcess[str]`
  - `adb_pairing_instance(service_name: str = 'robot_celular', service_regex_filter: str | None = None, subprocess_check_flag: bool = False) -> None` (sets `self.adb_pair`)
  - `clear() -> None`
  - `close() -> None`

---

## `DeviceInfo` (`device_manager.device_info`)

```python
DeviceInfo(
    device_connection: DeviceConnection,
    serial_number: str,
    subprocess_check_flag: bool = False,
    gateway: AdbGateway | None = None,
    ui_backend: UiHierarchyBackend | None = None,
)
```

| Method | Return | Notes / Exceptions |
| :--- | :--- | :--- |
| `actual_activity()` | `str \| None` | Top resumed activity |
| `is_screen_on()` | `bool` | Raises `UnexpectedAdbOutputError` on failure |
| `is_device_locked()` | `bool` | Raises `UnexpectedAdbOutputError` on failure |
| `get_screen_state()` | `tuple[bool, bool]` | `(is_screen_on, is_device_locked)` in 1 ADB call |
| `get_screen_gui_xml()` | `str \| None` | Native `uiautomator dump /dev/tty` with `/sdcard` fallback |
| `get_properties(extra_keys=None, refresh=False)` | `dict[str, str]` | Keys: `serial_number`, `brand`, `model`, `android_version`; cached when `extra_keys is None` |
| `get_screen_dimensions(refresh=False)` | `tuple[int, int]` | `(width, height)`, cached on instance |
| `get_display_orientation()` | `str` | `'Portrait'`, `'Landscape'`, `'Reverse Portrait'`, `'Reverse Landscape'`; raises `DeviceDisconnectedError` |
| `get_device_model(refresh=False)` | `str` | `'<brand> <model>'` or `'unknown'` |
| `list_installed_all_apps()` | `list[str]` | Package names |
| `is_app_installed(package_name)` | `bool` | Validates connection first |
| `is_app_running(package_name)` | `bool` | Checks `pidof <package_name>` |
| `get_app_path(package_name)` | `str \| None` | APK path via `pm path` |
| `app(package)` | `AppInfo` | Per-app info helper (`device_manager.infos.app.AppInfo`) |
| `get_location_mode()` | `str \| None` | `'Off'`, `'Sensors Only'`, `'Battery Saving'`, `'High Accuracy'` |
| `is_stay_awake_enabled()` | `bool` | Global `stay_on_while_plugged_in != '0'` |
| `is_airplane_mode_enabled()` | `bool` | Global `airplane_mode_on == '1'` |
| `get_all_touchscreens(refresh=False)` | `dict[str, TouchscreenInfo]` | Parsed from `getevent -p -l`; cached |
| `get_touchscreen_events(refresh=False)` | `list[str]` | Prioritized event nodes (direct touch first); cached |
| `get_touchscreen_info(refresh=False)` | `TouchscreenInfo` | Primary touchscreen or fallback `TouchscreenInfo('event8', '', (0, 0), (0, 0))` |
| `get_touch_axis_ranges(event_node=None)` | `tuple[tuple[int, int], tuple[int, int]]` | `(x_range, y_range)` for `event_node` or primary touchscreen |

---

## `DeviceActions` (`device_manager.device_actions`)

```python
DeviceActions(
    device_connection: DeviceConnection,
    serial_number: str,
    subprocess_check_flag: bool = False,
    gateway: AdbGateway | None = None,
)
```

| Method | Signature | Notes |
| :--- | :--- | :--- |
| `click_by_coordinates` | `(x: int, y: int) -> None` | `@require_connection` |
| `click_by_text` | `(text: str, *, exact: bool = False, xml_content: str \| None = None) -> bool` | Matches `text` or `content-desc` |
| `swipe` | `(x1: int, y1: int, x2: int, y2: int, time: int) -> None` | `time` in ms |
| `open_app` | `(package_name: str, activity_name: str \| None = None) -> None` | If `activity_name` omitted, expects `'pkg/act'` |
| `start_app` | `(package_name: str, activity: str, *, extras: dict[str, object] \| None = None, stop_first: bool = False) -> None` | Typed extras (`--ez`, `--ei`, `--ef`, `--es`) + `-S` |
| `close_app` | `(package_name: str) -> None` | `am force-stop` |
| `install_apk` | `(apk_path: str, replace: bool = False) -> None` | Raises `FileNotFoundError` if path missing; `replace=True` adds `-r -g` |
| `uninstall_apk` | `(package_name: str) -> None` | `pm uninstall --user 0` |
| `turn_on_screen` | `() -> None` | `KEYCODE_POWER` (toggles power!) |
| `wake_up_screen` | `() -> None` | Idempotent `KEYCODE_WAKEUP (224)` + `wm dismiss-keyguard` |
| `unlock_screen` | `(fallback_swipe: bool = True) -> None` | `KEYCODE_MENU`, then `dismiss-keyguard` + swipe if still locked |
| `turn_on_and_unlock_screen` | `() -> None` | Calls `turn_on_screen()` + `unlock_screen()` |
| `keep_screen_on_and_awake` | `(timeout_ms: int = 1800000) -> None` | `svc power stayon true`, `stay_on_while_plugged_in 7`, timeout, wakeup |
| `home_button` / `back` | `() -> None` | `KEYCODE_HOME` / `KEYCODE_BACK` |
| `screen_shot` | `(image_name: str = 'screen', destination: str = '/sdcard') -> None` | Saves PNG on device |
| `safe_screencap_bytes` | `() -> bytes \| None` | Try-first `exec-out screencap -p` in memory; raises `DeviceDisconnectedError` if invalid |
| `take_screenshot_to_file` | `(local_path: str \| Path) -> Path \| None` | Calls `safe_screencap_bytes()` and writes file |
| `push_file` / `pull_file` | `push_file(local_path: str, remote_path: str)` / `pull_file(remote_path: Path, local_path: Path)` | Uses `shell=False` |
| `remove_file` | `(remote_path: Path) -> None` | `rm <remote_path>` |
| `set_location_mode` | `(mode: str) -> None` | Valid: `'0'`, `'1'`, `'2'`, `'3'` (else `ValueError`) |
| `set_stay_awake` | `(enabled: bool) -> None` | `'3'` or `'0'` |
| `set_air_plane_mode` | `(enabled: bool) -> None` | `cmd connectivity airplane-mode enable\|disable` |
| `set_accelerometer_rotation` | `(enable: bool) -> None` | `1` or `0` |
| `set_android_setting` | `(setting_name: str, value: str, namespace: str = 'system') -> None` | `settings put <namespace> <setting_name> <value>` |
| `start_getevent_process` | `() -> subprocess.Popen[str]` | Legacy `subprocess.Popen` for `getevent` |
| `start_stream` | `(stream: AdbStreamSpec, *, timeout: float \| None = None) -> AdbStreamProcess` | Polymorphic `adbutils` streaming |

---

## `CameraActions` (`actions.camera` — `device_manager.actions.camera_actions`)
- `open() -> None` (`ACTION_STILL_IMAGE_CAMERA`)
- `open_video() -> None` (`ACTION_VIDEO_CAMERA`)
- `close() -> None` (`am force-stop com.android.camera`)
- `package() -> str` (resolves default camera package)
- `take_picture() -> None` (`KEYCODE_ENTER`)
- `clear_pictures(source: str | Path | None = '/sdcard/DCIM/Camera/*') -> None`
- `pull_pictures(destination: str | Path, amount: int = 1) -> None`
- `pull_picture_by_name(image_name: str, destination: str | Path, source: str | Path = Path('/sdcard/DCIM/Camera')) -> None`

---

## Gateways (`device_manager.adb_gateway`)
- `AdbGateway` (`Protocol`): `.run(args, *, check=False, capture_output=False, text=None) -> CompletedProcess[Any]`
- `SubprocessAdbGateway(runner=None)`: default `subprocess.run(..., shell=False)` adapter.
- `AdbutilsAdbGateway(client=None, fallback=None)`: persistent TCP socket adapter for `devices`, `shell`, `exec-out`, `push`, `pull`, and `open_stream(...)`, automatically delegating unsupported commands (`pair`, `connect`, `start-server`, `kill-server`, etc.) to `fallback`.

---

## UI Hierarchy Backends (`device_manager.ui_hierarchy`)
- `UiHierarchyBackend` (`Protocol`): `.dump_xml(comm_uri: str) -> str | None`
- `Uiautomator2Backend(connector=None)`: optional fast backend (`pip install "device_manager[u2]"`), caches `u2.connect(comm_uri)` per device and extracts clean `<hierarchy>` XML via `extract_ui_hierarchy_xml()`. Falls back to native ADB in `DeviceInfo.get_screen_gui_xml()` when `None` is returned.
