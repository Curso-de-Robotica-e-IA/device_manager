"""Real-device end-to-end and latency benchmark suite covering
DeviceInfo, DeviceActions, and DeviceManager.

Run with:
    pytest -m device --device -o addopts= -vv
Optional flags:
    --device-serial <SERIAL>
    --benchmark-iterations 3
    --benchmark-output benchmark_report.md
"""

from __future__ import annotations

from pathlib import Path, PurePosixPath

import pytest

from device_manager.device_actions import DeviceActions
from device_manager.device_info import DeviceInfo
from device_manager.manager import DeviceManager
from device_manager.ui_hierarchy import Uiautomator2Backend
from tests.conftest import BenchmarkRecorder

pytestmark = pytest.mark.device

SETTINGS_PKG = 'com.android.settings'


# ============================================================================
# 1. DeviceInfo Benchmarks
# ============================================================================
def test_benchmark_device_info_all(
    real_device: tuple[str, DeviceInfo, DeviceActions],
    benchmark_recorder: BenchmarkRecorder,
) -> None:
    _, info, _ = real_device

    props = benchmark_recorder.measure(
        'DeviceInfo.get_properties', info.get_properties
    )
    assert isinstance(props, dict)
    assert 'serial_number' in props

    width, height = benchmark_recorder.measure(
        'DeviceInfo.get_screen_dimensions', info.get_screen_dimensions
    )
    assert width > 0
    assert height > 0

    orientation = benchmark_recorder.measure(
        'DeviceInfo.get_display_orientation', info.get_display_orientation
    )
    assert isinstance(orientation, str)

    screen_on = benchmark_recorder.measure(
        'DeviceInfo.is_screen_on', info.is_screen_on
    )
    screen_locked = benchmark_recorder.measure(
        'DeviceInfo.is_device_locked', info.is_device_locked
    )
    state = benchmark_recorder.measure(
        'DeviceInfo.get_screen_state', info.get_screen_state
    )
    assert isinstance(screen_on, bool)
    assert isinstance(screen_locked, bool)
    assert state == (screen_on, screen_locked)

    activity = benchmark_recorder.measure(
        'DeviceInfo.actual_activity', info.actual_activity
    )
    assert isinstance(activity, str)
    assert len(activity) > 0

    apps = benchmark_recorder.measure(
        'DeviceInfo.list_installed_all_apps', info.list_installed_all_apps
    )
    assert isinstance(apps, list)

    installed = benchmark_recorder.measure(
        'DeviceInfo.is_app_installed',
        lambda: info.is_app_installed(SETTINGS_PKG),
    )
    assert isinstance(installed, bool)

    app_path = benchmark_recorder.measure(
        'DeviceInfo.get_app_path',
        lambda: info.get_app_path(SETTINGS_PKG),
    )
    assert app_path is None or isinstance(app_path, str)

    loc_mode = benchmark_recorder.measure(
        'DeviceInfo.get_location_mode', info.get_location_mode
    )
    assert loc_mode is None or isinstance(loc_mode, str)

    stay_awake = benchmark_recorder.measure(
        'DeviceInfo.is_stay_awake_enabled', info.is_stay_awake_enabled
    )
    airplane = benchmark_recorder.measure(
        'DeviceInfo.is_airplane_mode_enabled', info.is_airplane_mode_enabled
    )
    assert isinstance(stay_awake, bool)
    assert isinstance(airplane, bool)


@pytest.mark.parametrize('ui_backend_name', ['native', 'u2'])
def test_benchmark_device_info_gui_xml(
    ui_backend_name: str,
    real_device: tuple[str, DeviceInfo, DeviceActions],
    benchmark_recorder: BenchmarkRecorder,
) -> None:
    serial, info, _ = real_device
    if ui_backend_name == 'u2':
        pytest.importorskip(
            'uiautomator2',
            reason='Install uiautomator2 (device_manager[u2]) to benchmark u2 backend.',
        )
        target_info = DeviceInfo(
            info.device_connection,
            serial,
            subprocess_check_flag=info.subprocess_check_flag,
            gateway=info._gateway,
            ui_backend=Uiautomator2Backend(),
        )
        target_info.get_screen_gui_xml()  # warm up persistent u2 server
    else:
        target_info = info

    xml = benchmark_recorder.measure(
        f'DeviceInfo.get_screen_gui_xml[{ui_backend_name}]',
        target_info.get_screen_gui_xml,
    )
    assert xml is None or isinstance(xml, str)


# ============================================================================
# 2. DeviceActions Benchmarks
# ============================================================================
def test_benchmark_device_actions_all(
    real_device: tuple[str, DeviceInfo, DeviceActions],
    benchmark_recorder: BenchmarkRecorder,
    tmp_path: Path,
) -> None:
    _, info, actions = real_device

    png = benchmark_recorder.measure(
        'DeviceActions.safe_screencap_bytes',
        actions.safe_screencap_bytes,
    )
    assert png is not None
    assert png.startswith(b'\x89PNG\r\n\x1a\n')

    benchmark_recorder.measure(
        'DeviceActions.click_by_coordinates',
        lambda: actions.click_by_coordinates(1, 1),
    )
    benchmark_recorder.measure(
        'DeviceActions.swipe', lambda: actions.swipe(100, 100, 100, 100, 50)
    )
    benchmark_recorder.measure('DeviceActions.back', actions.back)
    benchmark_recorder.measure(
        'DeviceActions.home_button', actions.home_button
    )

    # Screenshot on device + remove
    benchmark_recorder.measure(
        'DeviceActions.screen_shot',
        lambda: actions.screen_shot(
            image_name='dm_bench', destination='/sdcard'
        ),
    )
    benchmark_recorder.measure(
        'DeviceActions.remove_file',
        lambda: actions.remove_file(PurePosixPath('/sdcard/dm_bench.png')),  # type: ignore[arg-type]
    )

    # Push + pull + cleanup
    local_src = tmp_path / 'dm_bench.txt'
    local_dst = tmp_path / 'dm_bench_pulled.txt'
    local_src.write_text('benchmark', encoding='utf-8')
    remote_txt = PurePosixPath('/sdcard/dm_bench.txt')

    benchmark_recorder.measure(
        'DeviceActions.push_file',
        lambda: actions.push_file(local_src.as_posix(), str(remote_txt)),
    )
    benchmark_recorder.measure(
        'DeviceActions.pull_file',
        lambda: actions.pull_file(remote_txt, local_dst.as_posix()),  # type: ignore[arg-type]
    )
    actions.remove_file(remote_txt)  # type: ignore[arg-type]
    assert local_dst.exists()

    # Non-destructive settings (preserve current stay_awake state)
    current_stay_awake = info.is_stay_awake_enabled()
    benchmark_recorder.measure(
        'DeviceActions.set_stay_awake',
        lambda: actions.set_stay_awake(current_stay_awake),
    )
    benchmark_recorder.measure(
        'DeviceActions.set_accelerometer_rotation',
        lambda: actions.set_accelerometer_rotation(True),
    )

    # App lifecycle
    benchmark_recorder.measure(
        'DeviceActions.open_app', lambda: actions.open_app(SETTINGS_PKG)
    )
    benchmark_recorder.measure(
        'DeviceActions.close_app', lambda: actions.close_app(SETTINGS_PKG)
    )


# ============================================================================
# 3. DeviceManager Benchmarks
# ============================================================================
def test_benchmark_device_manager_all(
    real_device: tuple[str, DeviceInfo, DeviceActions],
    real_device_manager: DeviceManager,
    benchmark_recorder: BenchmarkRecorder,
) -> None:
    serial, _, _ = real_device

    connected = benchmark_recorder.measure(
        'DeviceManager.is_connected',
        lambda: real_device_manager.is_connected(serial),
    )
    assert connected is True

    dev_info = benchmark_recorder.measure(
        'DeviceManager.get_device_info',
        lambda: real_device_manager.get_device_info(serial),
    )
    dev_actions = benchmark_recorder.measure(
        'DeviceManager.get_device_actions',
        lambda: real_device_manager.get_device_actions(serial),
    )
    assert dev_info is not None
    assert dev_actions is not None

    benchmark_recorder.measure(
        'DeviceManager.load_connected_usb_devices',
        real_device_manager.load_connected_usb_devices,
    )

    result = benchmark_recorder.measure(
        'DeviceManager.execute_adb_command',
        lambda: real_device_manager.execute_adb_command(
            'echo benchmark',
            comm_uris=[serial],
            shell=True,
            capture_output=True,
        ),
    )
    assert result.returncode == 0
    assert 'benchmark' in result.stdout
