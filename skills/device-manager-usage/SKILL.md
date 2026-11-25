---
name: device-manager-usage
description: >-
  Use when writing, refactoring, debugging, or testing Python code that uses `device_manager`
  (v2.0.0+) to control or inspect Android devices via ADB. Covers DeviceManager,
  get_device_manager/reset_device_manager, DeviceInfo (screen state, native UI XML, properties,
  touchscreen hardware ranges), DeviceActions (tap, click_by_text, swipe, screenshots, apps,
  settings), CameraActions, AdbutilsAdbGateway, exception handling, and unit-test mocking.
---

# Using `device_manager` (v2.0.0+)

`device_manager` is a Python 3.10–3.12 library for discovering, pairing, connecting, inspecting, and automating Android devices over ADB. It supports both `subprocess` and persistent `adbutils` TCP sockets via the `AdbGateway` abstraction, uses native ADB for UI XML by default, and includes `Uiautomator2Backend` (`uiautomator2` bundled as a dependency) for ~160 ms UI hierarchy dumps.

For exact signatures of every public class and method, read [references/api-reference.md](references/api-reference.md).

---

## 1. Architecture & Layering

```text
DeviceManager (registry indexed by serial: DeviceObjects(serial_number, device_info, device_actions))
 ├── connector: DeviceConnection (USB + Wi-Fi mDNS discovery, URI resolution, reconnect strategies)
 ├── DeviceInfo (try-first queries, instance caching for static props/screen/touchscreens)
 │    └── app(pkg) -> AppInfo
 ├── DeviceActions (input, screen, apps, files, settings, polymorphic adbutils streaming)
 │    └── camera: CameraActions
 └── execute_adb_command() -> AdbGateway (SubprocessAdbGateway | AdbutilsAdbGateway)
```

---

## 2. Initialization & Device Lookup

```python
from device_manager import (
    DeviceManager,
    get_device_manager,
    reset_device_manager,
)
from device_manager.adb_gateway import AdbutilsAdbGateway
from device_manager.connection.device_connection import DeviceConnection

# Option A: Context manager with high-performance adbutils socket gateway
connector = DeviceConnection(gateway=AdbutilsAdbGateway())
with DeviceManager(connector=connector) as dm:
    # USB devices are auto-loaded in DeviceManager.__init__()
    serials: list[str] = dm.connected_devices

    # Lookup returns (DeviceInfo, DeviceActions) or raises DeviceNotFoundError
    info, actions = dm[serials[0]]

    # Safe lookups return None when serial is absent
    maybe_info = dm.get_device_info(serials[0])
    maybe_actions = dm.get_device_actions(serials[0])

# Option B: Shared singleton (cached via lru_cache(maxsize=1))
dm = get_device_manager()
# Clear singleton in teardown/tests:
reset_device_manager()
```

### Important Iteration & Initialization Details
- **`for dev in dm:` yields `DeviceObjects` NamedTuples**, NOT serial strings! Unpack as `for serial, info, actions in dm:` or access `dev.serial_number`, `dev.device_info`, `dev.device_actions`.
- **`DeviceManager.__init__`** automatically runs `check_adb_dependencies_version()` (unless `check_dependencies=False`) and calls `self.load_connected_usb_devices()` (which returns `None` and populates `dm.connected_devices`).
- **Enabling `adbutils` sockets globally:** by default `DeviceConnection(gateway=None)` uses `SubprocessAdbGateway`. Pass `DeviceConnection(gateway=AdbutilsAdbGateway())` into `DeviceManager(connector=...)` so `DeviceInfo`, `DeviceActions`, and `execute_adb_command` all reuse persistent TCP sockets instead of spawning `adb` processes.

---

## 3. Common Workflows

### A. Inspecting State & UI Hierarchy (`DeviceInfo`)

`DeviceInfo` uses a **try-first** `_query_adb()` strategy: it executes the ADB shell command directly and only triggers `validate_connection(..., force_reconnect=True)` + one retry if the command fails.

```python
# Single ADB call for both screen-on and lock state (prefer over calling both separately)
screen_on, is_locked = info.get_screen_state()

# Static metadata (cached on the instance; pass refresh=True to bypass cache)
width, height = info.get_screen_dimensions()
props = info.get_properties()  # {'serial_number', 'brand', 'model', 'android_version'}
model = info.get_device_model()

# Native UI XML dump (uses `uiautomator dump /dev/tty`, strips trailing `/dev/tty` status text)
xml = info.get_screen_gui_xml()

# Fast UI XML (~160 ms vs ~2.4–3.5 s native) via `Uiautomator2Backend`
from device_manager.ui_hierarchy import Uiautomator2Backend
fast_dm = DeviceManager(ui_backend=Uiautomator2Backend())
# Falls back automatically to native ADB if `ui_backend.dump_xml(...)` returns None

# Touchscreen hardware discovery (for raw input / robotic touch calibration)
touchscreens = info.get_all_touchscreens()       # dict[node_name, TouchscreenInfo]
primary_ts = info.get_touchscreen_info()         # TouchscreenInfo(node, name, x_range, y_range)
x_range, y_range = info.get_touch_axis_ranges()  # or pass event_node='/dev/input/event2'

# App checks
if info.is_app_installed('com.example.app') and not info.is_app_running('com.example.app'):
    apk_path = info.get_app_path('com.example.app')
```

### B. Screen Control, Touch, Apps & Screenshots (`DeviceActions`)

```python
# Wake and unlock reliably (KEYCODE_MENU + dismiss-keyguard + swipe fallback)
actions.wake_up_screen()
actions.unlock_screen(fallback_swipe=True)
actions.keep_screen_on_and_awake(timeout_ms=1_800_000)

# Tap by coordinates or by UI text/content-desc
actions.click_by_coordinates(540, 960)
tapped = actions.click_by_text('Allow', exact=True)

# Avoid double XML dump when searching multiple labels
xml = info.get_screen_gui_xml() or ''
if not actions.click_by_text('Accept', xml_content=xml):
    actions.click_by_text('OK', xml_content=xml)

# In-memory PNG screenshot (try-first `exec-out screencap -p`) or save directly to disk
png_bytes = actions.safe_screencap_bytes()
saved_path = actions.take_screenshot_to_file('artifacts/screen.png')

# Launch an activity with typed Intent extras and optional force-stop (-S)
actions.start_app(
    'com.example.app',
    '.MainActivity',
    extras={'debug': True, 'retries': 3, 'threshold': 0.5, 'user': 'qa'},
    stop_first=True,
)

# Arbitrary Android setting — NOTE parameter order: (setting_name, value, namespace='system')
actions.set_android_setting('screen_brightness', '128', namespace='system')
```

### C. Camera Operations (`actions.camera`)

```python
cam = actions.camera
cam.open()                        # STILL_IMAGE_CAMERA intent (not open_camera!)
cam.take_picture()                # KEYCODE_ENTER
cam.pull_pictures('./shots', amount=1)
cam.pull_picture_by_name('IMG_001.jpg', './shots')
cam.clear_pictures()              # default: '/sdcard/DCIM/Camera/*'
cam.close()
```

---

## 4. Critical Gotchas & Pitfalls

1. **Opposite `shell` default between `DeviceManager` and `adb_executor`:**
   - `DeviceManager.execute_adb_command(..., shell=True)` defaults to `shell=True`.
   - `device_manager.adb_executor.execute_adb_command(..., shell=False)` defaults to `shell=False`.
   - Always pass `shell=False` for host-level ADB commands (`install`, `pull`, `push`, `devices`, `version`, `connect`, `disconnect`, `forward`, `reverse`).
2. **`**kwargs` in `execute_adb_command` are CLI tokens, NOT `subprocess.run` options:**
   - Passing `timeout=10` would append `['timeout', 10]` to the ADB command! Never pass `subprocess.run` kwargs there.
3. **`comm_uris` cannot be empty:**
   - `execute_adb_command` raises `ValueError('No devices specified for command execution.')` if `comm_uris` is empty. Pass `comm_uris=[serial]` or `comm_uris=['default']` for global commands.
4. **Parameter order in `set_android_setting`:**
   - Signature is `set_android_setting(setting_name: str, value: str, namespace: str = 'system')`, NOT `(namespace, key, value)`.
5. **Exception hierarchy (`device_manager.exceptions.errors`):**
   - `DeviceManagerError` (base)
     - `DeviceNotFoundError(DeviceManagerError, ValueError)` — unknown serial in `dm[serial]` or `build_comm_uri()`.
     - `DeviceDisconnectedError(DeviceManagerError, ConnectionError, RuntimeError)` — raised by `@require_connection(raise_on_disconnect=True)` methods and `validate_connection(..., raise_on_error=True)`.
     - `UnexpectedAdbOutputError(DeviceManagerError, ValueError)` — raised by `DeviceInfo.is_screen_on()`, `is_device_locked()`, `get_screen_state()`, `get_properties()`, `get_screen_dimensions()` when ADB fails or output cannot be parsed.
   - `DependencyNotFoundError` / `DependencyVersionError` (`device_manager.exceptions`) — raised during `check_adb_dependencies_version()`.
6. **Return value differences on failure in `DeviceInfo`:**
   - Methods returning `None` when disconnected/unavailable: `actual_activity()`, `get_screen_gui_xml()`, `get_app_path()`, `get_location_mode()`.
   - Methods returning empty/False: `list_installed_all_apps() -> []`, `get_all_touchscreens() -> {}`, `is_app_installed() -> False`, `is_app_running() -> False`, `is_stay_awake_enabled() -> False`, `is_airplane_mode_enabled() -> False`.
   - Methods raising: `get_display_orientation() -> DeviceDisconnectedError`; `is_screen_on()`, `is_device_locked()`, `get_screen_state()`, `get_properties()`, `get_screen_dimensions()` -> `UnexpectedAdbOutputError`.

---

## 5. Unit Testing Without a Physical Device or `adb` Binary

Because `DeviceInfo._query_adb` and `DeviceActions.safe_screencap_bytes` use a **try-first** strategy, tests that omit a mocked `gateway` will try to execute real `adb` and fail with `FileNotFoundError` in CI runners where `adb` is not installed. Always inject a mock `gateway`:

```python
import subprocess
from unittest.mock import MagicMock
from device_manager import DeviceInfo

conn = MagicMock()
conn.build_comm_uri.return_value = 'emulator-5554'
conn.validate_connection.return_value = True

gw = MagicMock()
gw.run.return_value = subprocess.CompletedProcess(
    args=[], returncode=0, stdout='Physical size: 1080x2400\n', stderr=''
)

info = DeviceInfo(conn, 'emulator-5554', gateway=gw)
assert info.get_screen_dimensions() == (1080, 2400)
```

For `DeviceManager` tests, also pass `check_dependencies=False` (or mock `device_manager.manager.check_adb_dependencies_version`) and `connector=mock_connector`.
