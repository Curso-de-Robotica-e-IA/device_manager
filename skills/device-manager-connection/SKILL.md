---
name: device-manager-connection
description: >-
  Use when connecting, pairing, discovering, validating, or troubleshooting Android devices
  over USB or wireless ADB (mDNS/Zeroconf) using `device_manager` (v2.0.0+). Covers
  DeviceConnection, ConnectionManager, AdbConnectionDiscovery, UsbDeviceScanner,
  WifiConnectionStrategy, AdbPairing (sync), AsyncAdbPairing (async), and offline mocking.
---

# Connection, Discovery & Pairing with `device_manager`

`device_manager` abstracts USB and Wireless Debugging (Android 11+ mDNS/Zeroconf) behind `DeviceConnection` and transport-specific `ConnectionStrategy` classes (`UsbConnectionStrategy` and `WifiConnectionStrategy`).

---

## 1. Architecture Overview

```text
DeviceManager
 └── connector: DeviceConnection(subprocess_check_flag=False, fixed_port=5555, gateway=None)
      ├── connection: ConnectionManager (runs `adb start-server` + AdbConnectionDiscovery)
      │    └── AdbConnectionDiscovery (mDNS `_adb-tls-connect._tcp.local.`)
      ├── usb_scanner: UsbDeviceScanner (parses `adb devices`, checks authorization)
      ├── connection_info: ObjectManager[ServiceInfo] (serial -> ServiceInfo)
      └── strategies.get_connection_strategy(ConnectionType.USB | ConnectionType.WIFI)
```

`ServiceInfo` (`device_manager.connection.utils.service_info`):
- `serial_number: str`, `ip: str`, `port: int`, `connection: ConnectionType` (`USB` or `WIFI`).
- **Addressing:** USB uses `serial_number`; Wi-Fi uses `f'{ip}:{port}'`.

---

## 2. Device Discovery Properties & USB Priority

`DeviceManager` starts with `connected_devices == []` and exposes 4 nested properties (`connected_devices ⊆ available_devices ⊆ visible_devices`, and `unauthorized_devices ⊆ visible_devices`):

```python
from device_manager import DeviceManager
from device_manager.adb_gateway import AdbutilsAdbGateway
from device_manager.connection.device_connection import DeviceConnection

dm = DeviceManager(connector=DeviceConnection(gateway=AdbutilsAdbGateway()))

print(dm.available_devices)     # authorized USB + Wi-Fi (resolved to serials via cached ro.serialno)
print(dm.unauthorized_devices)  # awaiting RSA authorization
print(dm.visible_devices)       # available ∪ unauthorized ∪ mDNS Wi-Fi

# Connect by serial — automatically prioritizes: 1. USB > 2. active TCP (ip:5555) > 3. mDNS Wi-Fi
dm.connect_devices(*dm.available_devices)
```

- `dm.load_connected_usb_devices()` can also be called explicitly to load all authorized USB devices (upgrading any existing Wi-Fi entry for the same serial to USB).
- `DeviceConnection.list_adb_device_states() -> dict[str, str]` returns `{identifier: state}` for all USB and Wi-Fi (`ip:port`) entries in `adb devices`.
- `UsbDeviceScanner.list_connected_devices() -> list[ServiceInfo]` returns only authorized (`device`) USB devices.

---

## 3. Wireless mDNS Discovery & Connecting

### Standalone Discovery (`AdbConnectionDiscovery`)
```python
from device_manager import AdbConnectionDiscovery

discovery = AdbConnectionDiscovery()
with discovery.start_discovery_listener():
    online = discovery.online_devices()     # dict[serial, ServiceInfo]
    offline = discovery.offline_devices()   # dict[serial, ServiceInfo]
    svc = discovery.get_service_info_for('SERIAL_1')
```

`discovery.connection_status_for_device(service_info)` returns a `ConnectionInfoStatus`:
- `UPDATED` — online with the same IP.
- `CHANGED` — online, IP changed.
- `DOWN` — moved to offline list.
- `UNKNOWN` — absent from both online and offline maps.

### Connecting & Disconnecting via `DeviceManager`
```python
# Discover visible USB + Wi-Fi devices
visible = dm.connector.visible_devices()  # list[ServiceInfo]

# Connect selected serials (dispatches automatically to USB or Wi-Fi strategy)
connected_serials = dm.connect_devices('SERIAL_1', 'SERIAL_2')

# Disconnect specific devices cleanly (runs `adb disconnect <uri>`)
ok = dm.disconnect_devices('SERIAL_1')

# Release mDNS Zeroconf threads cleanly when done
dm.close()
```

### Important Behavior & Gotchas
- **Fixed TCP/IP port (`fixed_port=5555`):** during `DeviceConnection.start_connection()`, Wi-Fi devices whose ephemeral wireless debugging port differs from `fixed_port` are switched via `adb -s <uri> tcpip <fixed_port>` and reconnected at `<ip>:<fixed_port>`.
- **Warning about `DeviceConnection.disconnect()`:** this static method runs `adb kill-server` and drops **all** ADB sessions on the host. Use `dm.disconnect_devices(*serials)` to disconnect individual devices.
- **`ConnectionManager.__init__` sleeps 2 seconds** after starting mDNS discovery and runs `adb start-server` (and `adb kill-server` only if `restart_adb_server=True`). Always close `DeviceManager`/`DeviceConnection` (or use `with`) so Zeroconf background threads are stopped.

---

## 4. Connection Validation & Targeted Wi-Fi Reconnect

```python
# Returns bool without reconnecting
is_ok = dm.connector.validate_connection('SERIAL_1', force_reconnect=False)

# Reconnect if invalid, and raise DeviceDisconnectedError if still invalid
dm.connector.validate_connection(
    'SERIAL_1',
    force_reconnect=True,
    raise_on_error=True,
)
```

When `force_reconnect=True` on a Wi-Fi device (`WifiConnectionStrategy.validate`):
1. **Step 1 (targeted, non-disruptive):** calls `connector.establish_first_connection(serial)` and re-validates without disturbing other connected devices.
2. **Step 2 (fallback):** only if Step 1 fails, calls `connector.disconnect()` (`adb kill-server`) + `connector.connect_all_devices()` and re-validates.

---

## 5. Wireless Pairing (QR Code & Pairing Code)

### A. Synchronous Pairing (`AdbPairing`)
```python
from device_manager import AdbPairing
from device_manager.cli.qrcode_viewer import show_qr_cli, show_qr_window

pairing = AdbPairing(
    service_name='my-host',
    password=None,               # auto-generates 8-char alphanumeric password if None
    subprocess_check_flag=False,
    max_zeroconf_instances=10,
)

# Show QR code in terminal or OpenCV window while listening on `_adb-tls-pairing._tcp.local.`
with pairing.pair(max_attempts=3) as qr_payload:
    show_qr_cli(pairing.qrcode)           # or show_qr_window(pairing.qrcode_image)
    pairing._context.wait_for_online_service(timeout=30.0)

# Rotate credentials if needed
pairing.update_qrcode(new_password=True)
pairing.set_password('custom123', update_qrcode=True)
```

### B. Manual Pairing Code (Android "Pair device with pairing code")
> **Exact method name note:** the method is spelled `pair_device_with_paring_code` (without the second `i`).

```python
pairing = AdbPairing()
paired: bool = pairing.pair_device_with_paring_code('192.168.1.42:37123', '482910')
```

### C. Asynchronous Pairing (`AsyncAdbPairing`)
Uses composition (`AsyncZeroconf` + `asyncio.create_subprocess_exec`) and does not block an `asyncio` event loop:

```python
from device_manager.asyncio_dm.async_adb_pairing import AsyncAdbPairing

pairing = AsyncAdbPairing(service_name='my-host', password='123456')
async with pairing.pair(max_attempts=3) as qr_payload:
    print(qr_payload)
```

---

## 6. Testing Connection Code Offline (CI-Safe)

Never let unit tests instantiate an unmocked `ConnectionManager` (which invokes `adb start-server`, starts real Zeroconf sockets, and sleeps 2 seconds):

```python
import subprocess
from unittest.mock import MagicMock
from device_manager.connection.device_connection import DeviceConnection
from device_manager.connection.utils.connection_type import ConnectionType
from device_manager.connection.utils.service_info import ServiceInfo

gw = MagicMock()
gw.run.return_value = subprocess.CompletedProcess(
    args=[], returncode=0, stdout='List of devices attached\nSER1\tdevice\n', stderr=''
)
# Patch ConnectionManager or sleep + AdbConnectionDiscovery when constructing DeviceConnection
dc = DeviceConnection(gateway=gw)
dc.connection_info.add('SER1', ServiceInfo('SER1', '', 0, ConnectionType.USB))
assert dc.is_connected('SER1') is True
```
