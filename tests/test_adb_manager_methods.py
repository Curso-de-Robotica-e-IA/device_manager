"""Unit tests for methods incorporated from adb_manager.py (100% coverage)."""

from __future__ import annotations

from pathlib import Path
import subprocess
from unittest.mock import MagicMock

from pytest_mock import MockerFixture

from device_manager.device_actions import DeviceActions
from device_manager.device_info import DeviceInfo
from device_manager.utils.adb_parsers import (
    TouchscreenInfo,
    parse_touchscreen_devices,
)

SAMPLE_GETEVENT = """\
preamble line before any device
add device 1: /dev/input/event1
  name:     "gpio-keys"
  events:   KEY (0001)
add device 2: /dev/input/event5
  name:     "indirect-pad"
  ABS_X : value 0, min 0, max 500
  ABS_Y : value 0, min 0, max 600
add device 3: /dev/input/event10
  name:     "goodix-ts"
  INPUT_PROP_DIRECT
  ABS_MT_POSITION_X : value 0, min 0, max 1079
  ABS_MT_POSITION_Y : value 0, min 0, max 2399
add device 4: /dev/other/no_input
  ABS_MT_POSITION_X : value 0
  ABS_MT_POSITION_Y : value 0
"""


def test_parse_touchscreen_devices_direct_and_indirect() -> None:
    touch_map, nodes = parse_touchscreen_devices(SAMPLE_GETEVENT)
    assert nodes == ['event10', 'event5']
    assert touch_map['event10'] == TouchscreenInfo(
        node='event10',
        name='goodix-ts',
        x_range=(0, 1079),
        y_range=(0, 2399),
    )
    assert touch_map['event5'] == TouchscreenInfo(
        node='event5',
        name='indirect-pad',
        x_range=(0, 500),
        y_range=(0, 600),
    )
    assert parse_touchscreen_devices('') == ({}, [])


def test_device_info_model_running_and_touchscreen_methods(
    mocker: MockerFixture,
) -> None:
    conn = MagicMock()
    conn.build_comm_uri.return_value = 'SER1'
    conn.validate_connection.return_value = True
    info = DeviceInfo(conn, 'SER1')
    mock_exec = mocker.patch(
        'device_manager.base_device_component.execute_adb_command'
    )

    # get_device_model (normal + empty -> unknown)
    mock_exec.return_value = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout=(
            '[ro.serialno]: [SER1]\n'
            '[ro.product.manufacturer]: [Google]\n'
            '[ro.product.model]: [Pixel 8]\n'
            '[ro.build.version.release]: [14]\n'
        ),
    )
    assert info.get_device_model() == 'Google Pixel 8'

    mock_exec.return_value = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout=(
            '[ro.serialno]: [SER1]\n'
            '[ro.product.manufacturer]: []\n'
            '[ro.product.model]: []\n'
            '[ro.build.version.release]: [14]\n'
        ),
    )
    assert info.get_device_model(refresh=True) == 'unknown'

    # is_app_running
    mock_exec.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout='1234\n'
    )
    assert info.is_app_running('com.example.app') is True
    mock_exec.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout=''
    )
    assert info.is_app_running('com.example.app') is False

    # touchscreen queries when empty -> fallback
    mock_exec.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout=''
    )
    assert info.get_all_touchscreens() == {}
    assert info.get_touchscreen_events() == []
    assert info.get_touchscreen_info().node == 'event8'
    assert info.get_touch_axis_ranges('/dev/input/missing') == ((0, 0), (0, 0))

    # touchscreen queries with real getevent output + caching
    mock_exec.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout=SAMPLE_GETEVENT
    )
    assert info.get_touchscreen_events(refresh=True) == ['event10', 'event5']
    assert info.get_touchscreen_events() == ['event10', 'event5']
    assert info.get_touchscreen_info().node == 'event10'
    assert info.get_touch_axis_ranges() == ((0, 1079), (0, 2399))
    assert info.get_touch_axis_ranges('/dev/input/event5') == (
        (0, 500),
        (0, 600),
    )


def test_device_actions_incorporated_methods(
    mocker: MockerFixture,
    tmp_path: Path,
) -> None:
    conn = MagicMock()
    conn.build_comm_uri.return_value = 'SER1'
    conn.validate_connection.return_value = True
    actions = DeviceActions(conn, 'SER1')
    mock_exec = mocker.patch(
        'device_manager.base_device_component.execute_adb_command',
        return_value=subprocess.CompletedProcess(
            args=[], returncode=0, stdout=''
        ),
    )

    actions.set_android_setting('screen_off_timeout', '60000', namespace='system')
    actions.start_app(
        'com.example',
        '.MainActivity',
        extras={'flag': True, 'port': 50605, 'ratio': 1.5, 'host': '127.0.0.1'},
        stop_first=True,
    )
    actions.start_app('com.example', '.MainActivity')
    actions.wake_up_screen()
    actions.keep_screen_on_and_awake()
    assert mock_exec.call_count == 10

    # take_screenshot_to_file (success + None)
    mocker.patch.object(
        actions, 'safe_screencap_bytes', return_value=b'\x89PNG\r\n\x1a\n123'
    )
    out_file = tmp_path / 'sub' / 'shot.png'
    saved = actions.take_screenshot_to_file(out_file)
    assert saved == out_file.resolve()
    assert out_file.read_bytes() == b'\x89PNG\r\n\x1a\n123'

    mocker.patch.object(actions, 'safe_screencap_bytes', return_value=None)
    assert actions.take_screenshot_to_file(out_file) is None

    # start_getevent_process
    mock_popen = mocker.patch('device_manager.device_actions.subprocess.Popen')
    proc = actions.start_getevent_process()
    assert proc is mock_popen.return_value
    mock_popen.assert_called_once_with(
        ['adb', '-s', 'SER1', 'shell', '-tt', 'getevent'],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        bufsize=1,
    )
