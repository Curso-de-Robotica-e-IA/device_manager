"""Real-device 3-way comparative benchmark suite:
1. `device_manager` (AdbutilsAdbGateway + resident dm_ui_dump.dex)
2. `uiautomator2` (pure u2)
3. `adb` (pure subprocess.run(['adb', '-s', serial, ...]))

Run with:
    pytest -m device --device -o addopts= -vv --benchmark-iterations 5
"""

from __future__ import annotations

import subprocess
from pathlib import Path, PurePosixPath

import pytest

from device_manager.device_actions import DeviceActions
from device_manager.device_info import DeviceInfo
from device_manager.manager import DeviceManager
from tests.conftest import BenchmarkRecorder

pytestmark = pytest.mark.device

SETTINGS_PKG = 'com.android.settings'


def _adb_run(
    serial: str, *args: str, text: bool = True
) -> subprocess.CompletedProcess:
    return subprocess.run(
        ['adb', '-s', serial, *args],
        capture_output=True,
        text=text,
        check=False,
    )


def _close_resident_backend(info: DeviceInfo) -> None:
    backend = getattr(info, '_ui_backend', None)
    if backend is not None and hasattr(backend, 'close'):
        backend.close()


# ============================================================================
# 1. Phase 1 — device_manager (atual)
# ============================================================================
def test_benchmark_01_device_manager(
    real_device: tuple[str, DeviceInfo, DeviceActions],
    real_device_manager: DeviceManager,
    benchmark_recorder: BenchmarkRecorder,
    tmp_path: Path,
) -> None:
    serial, info, actions = real_device
    dm = real_device_manager

    # DeviceInfo
    props = benchmark_recorder.measure(
        'DeviceInfo.get_properties',
        info.get_properties,
        backend='device_manager',
    )
    assert 'serial_number' in props

    width, height = benchmark_recorder.measure(
        'DeviceInfo.get_screen_dimensions',
        info.get_screen_dimensions,
        backend='device_manager',
    )
    assert width > 0
    assert height > 0

    benchmark_recorder.measure(
        'DeviceInfo.get_display_orientation',
        info.get_display_orientation,
        backend='device_manager',
    )
    benchmark_recorder.measure(
        'DeviceInfo.is_screen_on',
        info.is_screen_on,
        backend='device_manager',
    )
    benchmark_recorder.measure(
        'DeviceInfo.is_device_locked',
        info.is_device_locked,
        backend='device_manager',
    )
    benchmark_recorder.measure(
        'DeviceInfo.get_screen_state',
        info.get_screen_state,
        backend='device_manager',
    )
    benchmark_recorder.measure(
        'DeviceInfo.actual_activity',
        info.actual_activity,
        backend='device_manager',
    )

    info.get_screen_gui_xml()  # warm up resident app_process
    xml = benchmark_recorder.measure(
        'DeviceInfo.get_screen_gui_xml',
        info.get_screen_gui_xml,
        backend='device_manager',
    )
    assert xml is None or isinstance(xml, str)

    benchmark_recorder.measure(
        'DeviceInfo.list_installed_all_apps',
        info.list_installed_all_apps,
        backend='device_manager',
    )
    benchmark_recorder.measure(
        'DeviceInfo.is_app_installed',
        lambda: info.is_app_installed(SETTINGS_PKG),
        backend='device_manager',
    )
    benchmark_recorder.measure(
        'DeviceInfo.get_app_path',
        lambda: info.get_app_path(SETTINGS_PKG),
        backend='device_manager',
    )
    benchmark_recorder.measure(
        'DeviceInfo.get_location_mode',
        info.get_location_mode,
        backend='device_manager',
    )
    benchmark_recorder.measure(
        'DeviceInfo.is_stay_awake_enabled',
        info.is_stay_awake_enabled,
        backend='device_manager',
    )
    benchmark_recorder.measure(
        'DeviceInfo.is_airplane_mode_enabled',
        info.is_airplane_mode_enabled,
        backend='device_manager',
    )

    # DeviceActions
    jpeg = benchmark_recorder.measure(
        'DeviceActions.safe_screencap_bytes[jpeg]',
        lambda: actions.safe_screencap_bytes(raw=False),
        backend='device_manager',
    )
    assert jpeg is not None
    assert jpeg.startswith(b'\xff\xd8\xff')

    png = benchmark_recorder.measure(
        'DeviceActions.safe_screencap_bytes[png]',
        lambda: actions.safe_screencap_bytes(raw=True),
        backend='device_manager',
    )
    assert png is not None
    assert png.startswith(b'\x89PNG\r\n\x1a\n')

    benchmark_recorder.measure(
        'DeviceActions.click_by_coordinates',
        lambda: actions.click_by_coordinates(1, 1),
        backend='device_manager',
    )
    benchmark_recorder.measure(
        'DeviceActions.swipe',
        lambda: actions.swipe(100, 100, 100, 100, 50),
        backend='device_manager',
    )
    benchmark_recorder.measure(
        'DeviceActions.back',
        actions.back,
        backend='device_manager',
    )
    benchmark_recorder.measure(
        'DeviceActions.home_button',
        actions.home_button,
        backend='device_manager',
    )
    benchmark_recorder.measure(
        'DeviceActions.screen_shot[jpeg]',
        lambda: actions.screen_shot(
            image_name='dm_bench', destination='/sdcard', raw=False
        ),
        backend='device_manager',
    )
    benchmark_recorder.measure(
        'DeviceActions.screen_shot[png]',
        lambda: actions.screen_shot(
            image_name='dm_bench', destination='/sdcard', raw=True
        ),
        backend='device_manager',
    )
    actions.remove_file(PurePosixPath('/sdcard/dm_bench.jpg'))  # type: ignore[arg-type]
    benchmark_recorder.measure(
        'DeviceActions.remove_file',
        lambda: actions.remove_file(PurePosixPath('/sdcard/dm_bench.png')),  # type: ignore[arg-type]
        backend='device_manager',
    )

    local_src = tmp_path / 'dm_bench.txt'
    local_dst = tmp_path / 'dm_bench_pulled.txt'
    local_src.write_text('device_manager benchmark payload', encoding='utf-8')
    remote_txt = PurePosixPath('/sdcard/dm_bench.txt')
    benchmark_recorder.measure(
        'DeviceActions.push_file',
        lambda: actions.push_file(local_src.as_posix(), remote_txt.as_posix()),
        backend='device_manager',
    )
    benchmark_recorder.measure(
        'DeviceActions.pull_file',
        lambda: actions.pull_file(remote_txt, local_dst),  # type: ignore[arg-type]
        backend='device_manager',
    )
    actions.remove_file(remote_txt)  # type: ignore[arg-type]

    orig_stay_awake = info.is_stay_awake_enabled()
    benchmark_recorder.measure(
        'DeviceActions.set_stay_awake',
        lambda: actions.set_stay_awake(orig_stay_awake),
        backend='device_manager',
    )
    benchmark_recorder.measure(
        'DeviceActions.set_accelerometer_rotation',
        lambda: actions.set_accelerometer_rotation(False),
        backend='device_manager',
    )
    benchmark_recorder.measure(
        'DeviceActions.open_app',
        lambda: actions.open_app(f'{SETTINGS_PKG}/.Settings'),
        backend='device_manager',
    )
    benchmark_recorder.measure(
        'DeviceActions.close_app',
        lambda: actions.close_app(SETTINGS_PKG),
        backend='device_manager',
    )

    # DeviceManager
    benchmark_recorder.measure(
        'DeviceManager.is_connected',
        lambda: dm.is_connected(serial),
        backend='device_manager',
    )
    benchmark_recorder.measure(
        'DeviceManager.execute_adb_command',
        lambda: dm.execute_adb_command(
            'echo benchmark_ok',
            comm_uris=[info.current_comm_uri],
            shell=True,
            capture_output=True,
        ),
        backend='device_manager',
    )

    # Release resident UiAutomation cleanly before Phase 2 (uiautomator2)
    _close_resident_backend(info)


# ============================================================================
# 2. Phase 2 — uiautomator2 puro
# ============================================================================
def test_benchmark_02_uiautomator2(
    real_device: tuple[str, DeviceInfo, DeviceActions],
    benchmark_recorder: BenchmarkRecorder,
    tmp_path: Path,
) -> None:
    u2 = pytest.importorskip(
        'uiautomator2',
        reason='Install uiautomator2 (dev group) to run u2 comparison.',
    )
    _, info, _ = real_device
    _close_resident_backend(info)

    uri = info.current_comm_uri
    d = u2.connect(uri)

    # DeviceInfo equivalents
    benchmark_recorder.measure(
        'DeviceInfo.get_properties',
        lambda: d.device_info,
        backend='uiautomator2',
    )
    benchmark_recorder.measure(
        'DeviceInfo.get_screen_dimensions',
        d.window_size,
        backend='uiautomator2',
    )
    benchmark_recorder.measure(
        'DeviceInfo.get_display_orientation',
        lambda: d.orientation,
        backend='uiautomator2',
    )
    benchmark_recorder.measure(
        'DeviceInfo.is_screen_on',
        lambda: d.info.get('screenOn'),
        backend='uiautomator2',
    )
    benchmark_recorder.measure(
        'DeviceInfo.actual_activity',
        d.app_current,
        backend='uiautomator2',
    )
    benchmark_recorder.measure(
        'DeviceInfo.get_screen_gui_xml',
        d.dump_hierarchy,
        backend='uiautomator2',
    )
    benchmark_recorder.measure(
        'DeviceInfo.list_installed_all_apps',
        d.app_list,
        backend='uiautomator2',
    )
    benchmark_recorder.measure(
        'DeviceInfo.is_app_installed',
        lambda: SETTINGS_PKG in d.app_list(),
        backend='uiautomator2',
    )

    # DeviceActions equivalents
    benchmark_recorder.measure(
        'DeviceActions.safe_screencap_bytes[jpeg]',
        lambda: d.screenshot(format='pillow'),
        backend='uiautomator2',
    )
    benchmark_recorder.measure(
        'DeviceActions.click_by_coordinates',
        lambda: d.click(1, 1),
        backend='uiautomator2',
    )
    benchmark_recorder.measure(
        'DeviceActions.swipe',
        lambda: d.swipe(100, 100, 100, 100, duration=0.05),
        backend='uiautomator2',
    )
    benchmark_recorder.measure(
        'DeviceActions.back',
        lambda: d.press('back'),
        backend='uiautomator2',
    )
    benchmark_recorder.measure(
        'DeviceActions.home_button',
        lambda: d.press('home'),
        backend='uiautomator2',
    )

    local_src = tmp_path / 'u2_bench.txt'
    local_dst = tmp_path / 'u2_bench_pulled.txt'
    local_src.write_text('u2 benchmark payload', encoding='utf-8')
    remote_txt = '/sdcard/u2_bench.txt'
    benchmark_recorder.measure(
        'DeviceActions.push_file',
        lambda: d.push(local_src.as_posix(), remote_txt),
        backend='uiautomator2',
    )
    benchmark_recorder.measure(
        'DeviceActions.pull_file',
        lambda: d.pull(remote_txt, local_dst.as_posix()),
        backend='uiautomator2',
    )
    benchmark_recorder.measure(
        'DeviceActions.remove_file',
        lambda: d.shell(f'rm -f {remote_txt}'),
        backend='uiautomator2',
    )
    benchmark_recorder.measure(
        'DeviceActions.open_app',
        lambda: d.app_start(SETTINGS_PKG),
        backend='uiautomator2',
    )
    benchmark_recorder.measure(
        'DeviceActions.close_app',
        lambda: d.app_stop(SETTINGS_PKG),
        backend='uiautomator2',
    )
    benchmark_recorder.measure(
        'DeviceManager.execute_adb_command',
        lambda: d.shell('echo benchmark_ok'),
        backend='uiautomator2',
    )


# ============================================================================
# 3. Phase 3 — adb/subprocess puro
# ============================================================================
def test_benchmark_03_adb_subprocess(
    real_device: tuple[str, DeviceInfo, DeviceActions],
    benchmark_recorder: BenchmarkRecorder,
    tmp_path: Path,
) -> None:
    _, info, _ = real_device
    uri = info.current_comm_uri

    # DeviceInfo equivalents
    benchmark_recorder.measure(
        'DeviceInfo.get_properties',
        lambda: _adb_run(uri, 'shell', 'getprop'),
        backend='adb',
    )
    benchmark_recorder.measure(
        'DeviceInfo.get_screen_dimensions',
        lambda: _adb_run(uri, 'shell', 'wm', 'size'),
        backend='adb',
    )
    benchmark_recorder.measure(
        'DeviceInfo.get_display_orientation',
        lambda: _adb_run(uri, 'shell', 'dumpsys', 'display'),
        backend='adb',
    )
    benchmark_recorder.measure(
        'DeviceInfo.is_screen_on',
        lambda: _adb_run(uri, 'shell', 'dumpsys', 'deviceidle'),
        backend='adb',
    )
    benchmark_recorder.measure(
        'DeviceInfo.is_device_locked',
        lambda: _adb_run(uri, 'shell', 'dumpsys', 'deviceidle'),
        backend='adb',
    )
    benchmark_recorder.measure(
        'DeviceInfo.get_screen_state',
        lambda: _adb_run(uri, 'shell', 'dumpsys', 'deviceidle'),
        backend='adb',
    )
    benchmark_recorder.measure(
        'DeviceInfo.actual_activity',
        lambda: _adb_run(uri, 'shell', 'dumpsys', 'activity', 'activities'),
        backend='adb',
    )
    benchmark_recorder.measure(
        'DeviceInfo.get_screen_gui_xml',
        lambda: _adb_run(uri, 'shell', 'uiautomator', 'dump', '/dev/tty'),
        backend='adb',
    )
    benchmark_recorder.measure(
        'DeviceInfo.list_installed_all_apps',
        lambda: _adb_run(uri, 'shell', 'pm', 'list', 'packages'),
        backend='adb',
    )
    benchmark_recorder.measure(
        'DeviceInfo.is_app_installed',
        lambda: _adb_run(uri, 'shell', 'pm', 'list', 'packages', SETTINGS_PKG),
        backend='adb',
    )
    benchmark_recorder.measure(
        'DeviceInfo.get_app_path',
        lambda: _adb_run(uri, 'shell', 'pm', 'path', SETTINGS_PKG),
        backend='adb',
    )
    benchmark_recorder.measure(
        'DeviceInfo.get_location_mode',
        lambda: _adb_run(
            uri, 'shell', 'settings', 'get', 'secure', 'location_mode'
        ),
        backend='adb',
    )
    benchmark_recorder.measure(
        'DeviceInfo.is_stay_awake_enabled',
        lambda: _adb_run(
            uri,
            'shell',
            'settings',
            'get',
            'global',
            'stay_on_while_plugged_in',
        ),
        backend='adb',
    )
    benchmark_recorder.measure(
        'DeviceInfo.is_airplane_mode_enabled',
        lambda: _adb_run(
            uri, 'shell', 'settings', 'get', 'global', 'airplane_mode_on'
        ),
        backend='adb',
    )

    # DeviceActions equivalents
    benchmark_recorder.measure(
        'DeviceActions.safe_screencap_bytes[png]',
        lambda: _adb_run(uri, 'exec-out', 'screencap', '-p', text=False),
        backend='adb',
    )
    benchmark_recorder.measure(
        'DeviceActions.click_by_coordinates',
        lambda: _adb_run(uri, 'shell', 'input', 'tap', '1', '1'),
        backend='adb',
    )
    benchmark_recorder.measure(
        'DeviceActions.swipe',
        lambda: _adb_run(
            uri, 'shell', 'input', 'swipe', '100', '100', '100', '100', '50'
        ),
        backend='adb',
    )
    benchmark_recorder.measure(
        'DeviceActions.back',
        lambda: _adb_run(uri, 'shell', 'input', 'keyevent', '4'),
        backend='adb',
    )
    benchmark_recorder.measure(
        'DeviceActions.home_button',
        lambda: _adb_run(uri, 'shell', 'input', 'keyevent', '3'),
        backend='adb',
    )
    benchmark_recorder.measure(
        'DeviceActions.screen_shot[png]',
        lambda: _adb_run(
            uri, 'shell', 'screencap', '-p', '/sdcard/adb_bench.png'
        ),
        backend='adb',
    )
    benchmark_recorder.measure(
        'DeviceActions.remove_file',
        lambda: _adb_run(uri, 'shell', 'rm', '-f', '/sdcard/adb_bench.png'),
        backend='adb',
    )

    local_src = tmp_path / 'adb_bench.txt'
    local_dst = tmp_path / 'adb_bench_pulled.txt'
    local_src.write_text('adb benchmark payload', encoding='utf-8')
    remote_txt = '/sdcard/adb_bench.txt'
    benchmark_recorder.measure(
        'DeviceActions.push_file',
        lambda: _adb_run(uri, 'push', local_src.as_posix(), remote_txt),
        backend='adb',
    )
    benchmark_recorder.measure(
        'DeviceActions.pull_file',
        lambda: _adb_run(uri, 'pull', remote_txt, local_dst.as_posix()),
        backend='adb',
    )
    _adb_run(uri, 'shell', 'rm', '-f', remote_txt)

    benchmark_recorder.measure(
        'DeviceActions.set_stay_awake',
        lambda: _adb_run(
            uri,
            'shell',
            'settings',
            'put',
            'global',
            'stay_on_while_plugged_in',
            '0',
        ),
        backend='adb',
    )
    benchmark_recorder.measure(
        'DeviceActions.set_accelerometer_rotation',
        lambda: _adb_run(
            uri,
            'shell',
            'settings',
            'put',
            'system',
            'accelerometer_rotation',
            '0',
        ),
        backend='adb',
    )
    benchmark_recorder.measure(
        'DeviceActions.open_app',
        lambda: _adb_run(
            uri, 'shell', 'am', 'start', '-n', f'{SETTINGS_PKG}/.Settings'
        ),
        backend='adb',
    )
    benchmark_recorder.measure(
        'DeviceActions.close_app',
        lambda: _adb_run(uri, 'shell', 'am', 'force-stop', SETTINGS_PKG),
        backend='adb',
    )

    # DeviceManager equivalents
    benchmark_recorder.measure(
        'DeviceManager.is_connected',
        lambda: subprocess.run(
            ['adb', 'devices'], capture_output=True, text=True, check=False
        ),
        backend='adb',
    )
    benchmark_recorder.measure(
        'DeviceManager.execute_adb_command',
        lambda: _adb_run(uri, 'shell', 'echo', 'benchmark_ok'),
        backend='adb',
    )
