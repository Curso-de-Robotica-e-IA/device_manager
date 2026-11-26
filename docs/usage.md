# Usage

The library is centered around `DeviceManager`, which manages per-device `DeviceInfo` and `DeviceActions` instances, backed by `DeviceConnection`, `AdbPairing`, `AdbConnectionDiscovery`, and `NativeResidentUiBackend`.

## Using `DeviceManager`

`DeviceManager` starts with `connected_devices == []` and exposes 4 nested device properties:

- **`connected_devices`**: devices registered and ready to use via `dm[serial]`.
- **`available_devices`**: `connected_devices` union all authorized (`device`) USB and Wi-Fi devices in `adb devices`, automatically resolved to serial numbers.
- **`unauthorized_devices`**: devices reported as `unauthorized` in `adb devices` (never included in `connected_devices` or `available_devices`).
- **`visible_devices`**: `available_devices` union `unauthorized_devices` union Wi-Fi devices discovered via mDNS.

```python title='Basic Usage' linenums='1'
from device_manager import DeviceManager
from device_manager.adb_gateway import AdbutilsAdbGateway
from device_manager.connection.device_connection import DeviceConnection

connector = DeviceConnection(gateway=AdbutilsAdbGateway())

with DeviceManager(connector=connector) as manager:
    print('Available:', manager.available_devices)
    print('Unauthorized:', manager.unauthorized_devices)
    print('Visible:', manager.visible_devices)

    # Connect by serial — prioritizes USB > active Wi-Fi (ip:5555) > mDNS Wi-Fi
    manager.connect_devices(*manager.available_devices)

    # Iterate over connected devices (yields DeviceObjects NamedTuple)
    for device in manager:
        serial = device.serial_number
        info = device.device_info
        actions = device.device_actions
        print(serial, info.get_device_model())

    # Direct lookup by serial returns (DeviceInfo, DeviceActions)
    info, actions = manager[manager.connected_devices[0]]
```

For a shared singleton instance across modules, use `get_device_manager()` and `reset_device_manager()`:

```python
from device_manager import get_device_manager, reset_device_manager

dm = get_device_manager()
```

## Fast UI XML & Screenshots (`dm_ui_dump.dex`)

`DeviceInfo.get_screen_gui_xml()`, `DeviceActions.safe_screencap_bytes()`, and `DeviceActions.screen_shot()` use the bundled resident `dm_ui_dump.dex` server (Android 5.0+ / API 21+) by default:

```python
# ~12 ms UI hierarchy XML dump (raises UnsupportedAndroidVersionError on API < 21)
xml = info.get_screen_gui_xml()

# Tap UI element by text or content-desc
actions.click_by_text('Allow', exact=True)

# In-memory screenshots: fast JPEG (~150 ms) by default, lossless PNG with raw=True
jpeg_bytes = actions.safe_screencap_bytes()
png_bytes = actions.safe_screencap_bytes(raw=True)

# On-device screenshots: /sdcard/screen.jpg (~150 ms) or /sdcard/screen.png (raw=True)
actions.screen_shot('screen', '/sdcard')
actions.screen_shot('screen', '/sdcard', raw=True)
```

## Polymorphic ADB Streaming (`adbutils`)

Use `DeviceActions.start_stream()` to stream live output without spawning `subprocess.Popen`:

```python
from device_manager.enumerations.adb_stream import (
    AdbStreamCommand,
    CustomAdbStream,
)

# Preset with extra CLI arguments
with actions.start_stream(AdbStreamCommand.LOGCAT.with_args('*:E', '-v', 'time')) as stream:
    for line in stream.iter_lines():
        print(line)
        if 'FATAL' in line:
            stream.terminate()

# Custom shell command
with actions.start_stream(CustomAdbStream('dumpsys battery')) as stream:
    for line in stream.iter_lines():
        print(line)
```

## Pairing a Device (Wireless Debugging)

=== "AdbPairing Context Manager (Sync)"

    ```python title='QR Code Pairing' linenums='1'
    from device_manager import AdbPairing
    from device_manager.cli.qrcode_viewer import show_qr_window

    pair_server = AdbPairing()
    with pair_server.pair() as qrcode_string:
        show_qr_window(pair_server.qrcode_image)
    ```

=== "Manual 6-Digit Pairing Code"

    ```python title='Pairing Code' linenums='1'
    from device_manager import AdbPairing

    pair_server = AdbPairing()
    success = pair_server.pair_device_with_paring_code('192.168.1.42:37123', '482910')
    ```

=== "AsyncAdbPairing (Asyncio)"

    ```python title='Async Pairing' linenums='1'
    from device_manager.asyncio_dm.async_adb_pairing import AsyncAdbPairing

    pair_server = AsyncAdbPairing()
    async with pair_server.pair() as qrcode_string:
        print(qrcode_string)
    ```

## Sending Raw ADB Commands

```python title='execute_adb_command' linenums='1'
# Runs on all connected_devices (shell=True by default)
manager.execute_adb_command('input keyevent 3')

# Runs on specific serials (pass shell=False for host-level commands like pull/push/install)
manager.execute_adb_command(
    'pm list packages',
    comm_uris=['serial_number_1'],
    shell=True,
    capture_output=True,
)
```
