---
name: device-manager-streaming
description: >-
  Use when streaming continuous live output from an Android device with `device_manager`
  (v2.0.0+) such as getevent, logcat, dmesg, top, screenrecord, or custom shell commands via
  `adbutils` TCP sockets instead of subprocess.Popen. Covers DeviceActions.start_stream,
  AdbStreamSpec (Protocol), AdbStreamCommand, .with_args(), CustomAdbStream,
  AdbStreamProcess, AdbutilsAdbGateway.open_stream, and unit-test mocking.
---

# Polymorphic ADB Streaming via `adbutils`

`DeviceActions.start_stream()` opens a persistent `adbutils` TCP shell stream (`device.shell(cmd, stream=True)`) and returns an `AdbStreamProcess` with a familiar `Popen`-like interface — **without spawning an `adb` subprocess**.

*(Legacy note: `DeviceActions.start_getevent_process()` still exists for backwards compatibility with callers requiring a literal `subprocess.Popen[str]`, but prefer `start_stream(...)` for all new streaming code.)*

---

## 1. Polymorphic Design (`AdbStreamSpec`)

Defined in `device_manager.enumerations.adb_stream`:

```python
@runtime_checkable
class AdbStreamSpec(Protocol):
    def build_command(self) -> str: ...
    @property
    def default_encoding(self) -> str | None: ...
```

`DeviceActions.start_stream(stream: AdbStreamSpec, *, timeout: float | None = None) -> AdbStreamProcess` has **zero conditionals on stream types**: it validates `isinstance(stream, AdbStreamSpec)` and delegates directly to `stream.build_command()` and `stream.default_encoding`.

### Built-in Presets (`AdbStreamCommand`)

| Preset | `build_command()` | `default_encoding` | Typical Use |
| :--- | :--- | :--- | :--- |
| `AdbStreamCommand.GETEVENT` | `getevent -lt` | `'utf-8'` | Real-time touchscreen / input events |
| `AdbStreamCommand.LOGCAT` | `logcat` | `'utf-8'` | Android system & application logs |
| `AdbStreamCommand.DMESG` | `dmesg -w` | `'utf-8'` | Live kernel ring-buffer messages |
| `AdbStreamCommand.TOP` | `top -b` | `'utf-8'` | Batch-mode CPU & process telemetry |
| `AdbStreamCommand.SCREENRECORD` | `screenrecord --output-format=h264 -` | `None` (binary) | Raw H.264 video stream over stdout |

Every preset exposes `.with_args(*args: str) -> CustomAdbStream`, preserving the preset's `default_encoding` while appending extra CLI flags.

---

## 2. Usage Recipes

### A. Text Line Streaming (`iter_lines()`)
```python
from device_manager.enumerations.adb_stream import AdbStreamCommand

# Stream touchscreen events from a specific input node
spec = AdbStreamCommand.GETEVENT.with_args('/dev/input/event1')
with actions.start_stream(spec, timeout=30.0) as stream:
    for line in stream.iter_lines():
        print(line)
        if 'ABS_MT_TRACKING_ID ffffffff' in line:
            stream.terminate()  # cleanly exits loop and closes socket
```

### B. Filtered Logcat Streaming
```python
spec = AdbStreamCommand.LOGCAT.with_args('*:E', '-v', 'time')
with actions.start_stream(spec) as stream:
    for line in stream.iter_lines():
        if 'FATAL EXCEPTION' in line:
            stream.terminate()
```

### C. Binary Streaming (`read_chunks()`)
`AdbStreamCommand.SCREENRECORD` sets `default_encoding = None` automatically. Use `read_chunks(chunk_size=4096)` for binary streams:

```python
with actions.start_stream(AdbStreamCommand.SCREENRECORD) as stream:
    with open('capture.h264', 'wb') as out_file:
        for chunk in stream.read_chunks(chunk_size=8192):
            out_file.write(chunk)
```

### D. Ad-Hoc Custom Commands (`CustomAdbStream`)
`CustomAdbStream(command: str, encoding: str | None = 'utf-8')` is a frozen dataclass implementing `AdbStreamSpec`. It validates `command` in `__post_init__` (raises `ValueError` on empty/whitespace strings):

```python
from device_manager.enumerations.adb_stream import CustomAdbStream

with actions.start_stream(CustomAdbStream('dumpsys battery')) as stream:
    for line in stream.iter_lines():
        print(line)
```

### E. Extending Polymorphically with Domain Classes
Implement `build_command()` and `default_encoding` on your own class — no inheritance required:

```python
class AppLogcatStream:
    def __init__(self, tag: str, level: str = 'V') -> None:
        self._tag = tag
        self._level = level

    def build_command(self) -> str:
        return f'logcat -s {self._tag}:{self._level}'

    @property
    def default_encoding(self) -> str | None:
        return 'utf-8'

with actions.start_stream(AppLogcatStream('MyApp', 'D')) as stream:
    for line in stream.iter_lines():
        print(line)
```

---

## 3. `AdbStreamProcess` Lifecycle & Threading

Defined in `device_manager.adb_stream`:
- `stream.command -> str`: resolved shell command string.
- `stream.is_open -> bool`: `True` until `close()`/`terminate()` is called.
- `stream.iter_lines() -> Iterator[str]`: yields `\r\n`-stripped lines (`errors='replace'`), stops on EOF or `close()`.
- `stream.read_chunks(chunk_size: int = 4096) -> Iterator[bytes]`: yields raw bytes via `conn.recv(chunk_size)`, stops on `b''` or `close()`.
- `stream.close()` / `stream.terminate()`: idempotent; sets `is_open = False` and closes the underlying `adbutils.AdbConnection` socket.
- **Context manager (`with`):** always prefer `with actions.start_stream(...) as stream:` so sockets are never leaked on exceptions.
- **Stopping a background reader thread:** calling `stream.terminate()` from another thread closes the underlying socket, unblocking `iter_lines()` / `read_chunks()`.

---

## 4. Errors & Validation

| Error | Cause |
| :--- | :--- |
| `DeviceDisconnectedError` | Device connection invalid when calling `actions.start_stream(...)` (`@require_connection`) |
| `TypeError` | `stream` does not implement `AdbStreamSpec` (e.g., passing a raw `str` like `'logcat'`) |
| `ValueError` | Constructing `CustomAdbStream('')` or whitespace-only command |

- **Gateway behavior:** if `actions._gateway` is an `AdbutilsAdbGateway`, `start_stream` reuses it directly; otherwise it instantiates a fresh `AdbutilsAdbGateway()` and calls `open_stream(serial, command, timeout=..., encoding=...)`.

---

## 5. Unit Testing Streams Without Hardware

Inject a fake `adbutils` client into `AdbutilsAdbGateway(client=fake_client)`:

```python
import io
from unittest.mock import MagicMock
from device_manager import DeviceActions
from device_manager.adb_gateway import AdbutilsAdbGateway
from device_manager.enumerations.adb_stream import AdbStreamCommand

fake_adb_conn = MagicMock()
fake_adb_conn.conn.makefile.return_value = io.StringIO('line1\r\nline2\n')

fake_device = MagicMock()
fake_device.shell.return_value = fake_adb_conn
fake_client = MagicMock()
fake_client.device.return_value = fake_device

conn = MagicMock()
conn.validate_connection.return_value = True
conn.build_comm_uri.return_value = 'SER-1'

actions = DeviceActions(conn, 'SER-1', gateway=AdbutilsAdbGateway(client=fake_client))
with actions.start_stream(AdbStreamCommand.LOGCAT) as stream:
    assert list(stream.iter_lines()) == ['line1', 'line2']
```
