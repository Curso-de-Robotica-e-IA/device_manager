"""Real-device compatibility and performance comparison between:
1. Native ADB (`uiautomator dump /dev/tty` and `--compressed`)
2. `uiautomator2` persistent server (`u2.connect(uri).dump_hierarchy()`)
3. Raw `screencap` (PC-side PNG encoding) vs `screencap -p` (device-side PNG)

Run with:
    pytest tests/device/test_ui_xml_backends_benchmark.py --device -o addopts= -vv
"""

from __future__ import annotations

import struct
import xml.etree.ElementTree as ET

import cv2
import numpy as np
import pytest

from device_manager.device_actions import DeviceActions
from device_manager.device_info import DeviceInfo
from device_manager.utils.adb_parsers import extract_ui_hierarchy_xml
from tests.conftest import BenchmarkRecorder

pytestmark = pytest.mark.device


def _assert_valid_hierarchy_xml(xml_str: str | None) -> int:
    assert xml_str is not None
    assert len(xml_str) > 0
    xml_start = xml_str.find('<?xml')
    clean_xml = xml_str[xml_start:] if xml_start != -1 else xml_str
    root = ET.fromstring(clean_xml)
    assert root.tag == 'hierarchy'
    return sum(1 for _ in root.iter('node'))


def test_ui_xml_native_adb_implementation(
    real_device: tuple[str, DeviceInfo, DeviceActions],
    benchmark_recorder: BenchmarkRecorder,
) -> None:
    """Measures native ADB `uiautomator dump /dev/tty` (default vs --compressed)."""
    _, info, _ = real_device

    xml_default = benchmark_recorder.measure(
        'UIXml.native_adb_default',
        info.get_screen_gui_xml,
    )
    nodes_default = _assert_valid_hierarchy_xml(xml_default)
    assert nodes_default > 0

    def _dump_compressed() -> str | None:
        raw = info._query_adb('uiautomator dump --compressed /dev/tty')
        return extract_ui_hierarchy_xml(raw) if raw is not None else None

    xml_compressed = benchmark_recorder.measure(
        'UIXml.native_adb_compressed',
        _dump_compressed,
    )
    nodes_compressed = _assert_valid_hierarchy_xml(xml_compressed)
    assert nodes_compressed > 0


def test_ui_xml_uiautomator2_backend(
    real_device: tuple[str, DeviceInfo, DeviceActions],
    benchmark_recorder: BenchmarkRecorder,
) -> None:
    """Measures `uiautomator2` persistent server `dump_hierarchy()` (optional)."""
    u2 = pytest.importorskip(
        'uiautomator2',
        reason='Install uiautomator2 to run the u2 backend comparison benchmark.',
    )
    _, info, _ = real_device

    # Connect once (warm persistent server on device)
    u2_device = u2.connect(info.current_comm_uri)

    xml_u2 = benchmark_recorder.measure(
        'UIXml.uiautomator2',
        u2_device.dump_hierarchy,
    )
    nodes_u2 = _assert_valid_hierarchy_xml(xml_u2)
    assert nodes_u2 > 0


def test_screencap_raw_pc_encode_vs_device_png(
    real_device: tuple[str, DeviceInfo, DeviceActions],
    benchmark_recorder: BenchmarkRecorder,
) -> None:
    """Compares `safe_screencap_bytes()` (device PNG) vs raw `screencap` (PC PNG)."""
    _, info, actions = real_device

    png_device = benchmark_recorder.measure(
        'Screencap.device_png_flag_p',
        actions.safe_screencap_bytes,
    )
    assert png_device is not None
    assert png_device.startswith(b'\x89PNG')

    gateway = actions._gateway

    def _raw_screencap_pc_png() -> bytes:
        assert gateway is not None
        res = gateway.run(
            ['adb', '-s', info.current_comm_uri, 'exec-out', 'screencap'],
            capture_output=True,
            text=False,
        )
        raw: bytes = res.stdout
        width, height, _fmt = struct.unpack_from('<III', raw, 0)
        pixel_bytes = width * height * 4
        # Android screencap header is 12 bytes (older) or 16 bytes (with colorspace)
        header_size = len(raw) - pixel_bytes
        rgba = np.frombuffer(
            raw, dtype=np.uint8, offset=header_size, count=pixel_bytes
        ).reshape((height, width, 4))
        bgr = cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGR)
        ok, encoded = cv2.imencode('.png', bgr)
        assert ok
        return encoded.tobytes()

    png_pc = benchmark_recorder.measure(
        'Screencap.raw_pc_png_encode',
        _raw_screencap_pc_png,
    )
    assert png_pc.startswith(b'\x89PNG')
