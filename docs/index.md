# Device Manager Documentation

**`device_manager`** is a Python 3.10–3.12 library for discovering, pairing, connecting, inspecting, and automating Android devices over Android Debug Bridge (ADB).

## Key Features

- **USB & Wireless (mDNS/Zeroconf) Management:** Discover devices over USB and Android 11+ Wireless Debugging, pair via QR Code or 6-digit pairing code (sync & async), and connect by serial with automatic transport priority (**USB > active Wi-Fi TCP > mDNS Wi-Fi**).
- **4 Nested Device Views:** `connected_devices ⊆ available_devices ⊆ visible_devices`, plus `unauthorized_devices ⊆ visible_devices` (`unauthorized_devices ∩ available_devices = ∅`), with automatic `ip:port → serial` resolution.
- **High-Performance Transport (`AdbutilsAdbGateway`):** Reuses persistent `adbutils` TCP sockets instead of spawning `adb` subprocesses on every call.
- **Ultra-Fast Resident UI & Screenshot Server (`dm_ui_dump.dex`):** Bundled 5.2 KB Android `.dex` (Android 5.0+ / API 21+) delivers **~12 ms** UI hierarchy XML dumps (`get_screen_gui_xml()`) and **~150 ms** JPEG screenshots (`safe_screencap_bytes()` / `screen_shot()`) with **zero `uiautomator2` runtime dependency**.
- **Polymorphic ADB Streaming:** Stream `getevent`, `logcat`, `dmesg`, `top`, `screenrecord`, or custom shell commands via `DeviceActions.start_stream(AdbStreamSpec)` over `adbutils` sockets.

## Installation

Install from a GitHub Release wheel (`.whl`) or build locally with [Poetry](https://python-poetry.org/):

```bash
poetry install
poetry build --format wheel
```

Then install the generated wheel from `dist/`:

```bash
pip install dist/device_manager-*.whl
```
