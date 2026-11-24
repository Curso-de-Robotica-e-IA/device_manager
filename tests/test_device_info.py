import subprocess
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from device_manager.device_info import DeviceInfo


@pytest.fixture
def mock_connection() -> MagicMock:
    conn = MagicMock()
    conn.build_comm_uri.return_value = '192.168.1.10:5555'
    conn.validate_connection.return_value = True
    return conn


def _cp(stdout: str) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=[], returncode=0, stdout=stdout)


def test_device_info_core_queries(
    mock_connection: MagicMock,
    mocker: MockerFixture,
) -> None:
    info = DeviceInfo(mock_connection, 'SER123')
    assert info.serial_number == 'SER123'
    assert info.current_comm_uri == '192.168.1.10:5555'

    mock_exec = mocker.patch(
        'device_manager.base_device_component.execute_adb_command'
    )

    mock_exec.return_value = _cp('  mCurrentFocus=Window{abc com.example.app/com.example.Main}')
    assert info.actual_activity() == 'com.example.app/com.example.Main'

    mock_exec.return_value = _cp('nothing here')
    assert info.actual_activity() == 'No activity'

    mock_exec.return_value = _cp('  mScreenOn=true\n')
    assert info.is_screen_on() is True

    mock_exec.return_value = _cp('  mScreenOn=false\n')
    assert info.is_screen_on() is False

    mock_exec.return_value = _cp('no screen line')
    with pytest.raises(ValueError, match='Unexpected output'):
        info.is_screen_on()

    mock_exec.return_value = _cp('  mScreenLocked=true\n')
    assert info.is_device_locked() is True

    mock_exec.return_value = _cp('  mScreenLocked=false\n')
    assert info.is_device_locked() is False

    mock_exec.return_value = _cp('no lock line')
    with pytest.raises(ValueError, match='Unexpected output'):
        info.is_device_locked()


def test_device_info_properties_dimensions_and_settings(
    mock_connection: MagicMock,
    mocker: MockerFixture,
) -> None:
    info = DeviceInfo(mock_connection, 'SER123')
    mock_exec = mocker.patch(
        'device_manager.base_device_component.execute_adb_command'
    )

    mock_exec.return_value = _cp(
        '[ro.serialno]: [SER123]\n'
        '[ro.product.manufacturer]: [Google]\n'
        '[ro.product.model]: [Pixel]\n'
        '[ro.build.version.release]: [14]\n'
        '[ro.custom.key]: [custom_val]\n'
    )
    props = info.get_properties(extra_keys=['ro.custom.key'])
    assert props['serial_number'] == 'SER123'
    assert props['brand'] == 'Google'
    assert props['ro.custom.key'] == 'custom_val'

    mock_exec.return_value = _cp('Physical size: 1080x2400\n')
    assert info.get_screen_dimensions() == (1080, 2400)

    mock_exec.return_value = _cp('  mCurrentOrientation=1\n')
    assert info.get_display_orientation() == 'Landscape'

    mock_exec.return_value = _cp('package:com.a\npackage:com.b\n')
    assert info.list_installed_all_apps() == ['com.a', 'com.b']
    assert info.is_app_installed('com.a') is True

    mock_exec.return_value = _cp('package:/data/app/com.a/base.apk\n')
    assert info.get_app_path('com.a') == '/data/app/com.a/base.apk'

    mock_exec.return_value = _cp('3\n')
    assert info.get_location_mode() == 'High Accuracy'

    mock_exec.return_value = _cp('3\n')
    assert info.is_stay_awake_enabled() is True

    mock_exec.return_value = _cp('1\n')
    assert info.is_airplane_mode_enabled() is True

    mock_connection.validate_connection.return_value = False
    mock_exec.return_value = subprocess.CompletedProcess(
        args=[], returncode=1, stdout=''
    )
    with pytest.raises(ConnectionError):
        info.get_display_orientation()
    assert info.list_installed_all_apps() == []
    assert info.is_app_installed('com.a') is False
    assert info.get_app_path('com.a') is None
    assert info.get_location_mode() is None
    assert info.is_stay_awake_enabled() is False
    assert info.is_airplane_mode_enabled() is False


def test_device_info_try_first_retry_cache_and_screen_state(
    mock_connection: MagicMock,
    mocker: MockerFixture,
) -> None:
    info = DeviceInfo(mock_connection, 'SER123')
    mock_exec = mocker.patch(
        'device_manager.base_device_component.execute_adb_command'
    )

    # Try-first retry: first call fails, validate_connection=True, retry succeeds
    mock_exec.side_effect = [
        subprocess.CompletedProcess(args=[], returncode=1, stdout=''),
        _cp('  mScreenOn=true\n  mScreenLocked=false\n'),
    ]
    assert info.get_screen_state() == (True, False)
    mock_connection.validate_connection.assert_called_once_with(
        'SER123', force_reconnect=True
    )

    # get_screen_state raises when disconnected
    mock_connection.validate_connection.return_value = False
    mock_exec.side_effect = None
    mock_exec.return_value = subprocess.CompletedProcess(
        args=[], returncode=1, stdout=''
    )
    with pytest.raises(ValueError, match='Unexpected output'):
        info.get_screen_state()

    # Caching for get_properties and get_screen_dimensions + refresh=True
    mock_connection.validate_connection.return_value = True
    mock_exec.return_value = _cp(
        '[ro.serialno]: [SER123]\n'
        '[ro.product.manufacturer]: [Google]\n'
        '[ro.product.model]: [Pixel]\n'
        '[ro.build.version.release]: [14]\n'
    )
    mock_exec.reset_mock()
    p1 = info.get_properties()
    p2 = info.get_properties()
    assert p1 == p2
    assert mock_exec.call_count == 1
    info.get_properties(refresh=True)
    assert mock_exec.call_count == 2

    mock_exec.return_value = _cp('Physical size: 1080x2400\n')
    mock_exec.reset_mock()
    assert info.get_screen_dimensions() == (1080, 2400)
    assert info.get_screen_dimensions() == (1080, 2400)
    assert mock_exec.call_count == 1
    assert info.get_screen_dimensions(refresh=True) == (1080, 2400)
    assert mock_exec.call_count == 2


def test_safe_screencap_bytes_try_first(
    mock_connection: MagicMock,
) -> None:
    from device_manager.device_actions import DeviceActions

    # 1. Try-first retry on failure (reconnect succeeds, then fails on retry; then retry succeeds)
    gw = MagicMock()
    gw.run.side_effect = [
        subprocess.CompletedProcess(args=[], returncode=1, stdout=b''),
        subprocess.CompletedProcess(args=[], returncode=1, stdout=b''),
        subprocess.CompletedProcess(args=[], returncode=1, stdout=b''),
        subprocess.CompletedProcess(
            args=[], returncode=0, stdout=b'\x89PNG\r\n\x1a\nok'
        ),
    ]
    actions = DeviceActions(mock_connection, 'SER123', gateway=gw)
    assert actions.safe_screencap_bytes() is None
    assert actions.safe_screencap_bytes() == b'\x89PNG\r\n\x1a\nok'

    # 2. Try-first when disconnected (validate_connection returns False -> DeviceDisconnectedError)
    mock_connection.validate_connection.return_value = False
    gw.run.side_effect = None
    gw.run.return_value = subprocess.CompletedProcess(
        args=[], returncode=1, stdout=b''
    )
    with pytest.raises(ConnectionError, match='Device not connected'):
        actions.safe_screencap_bytes()


def test_device_info_exact_commands_and_fallbacks(
    mocker: MockerFixture,
) -> None:
    from device_manager.utils.adb_parsers import TouchscreenInfo

    conn = MagicMock()
    conn.build_comm_uri.return_value = 'SER1'
    conn.validate_connection.return_value = True
    info = DeviceInfo(conn, 'SER1', subprocess_check_flag=True)
    mock_exec = mocker.patch(
        'device_manager.base_device_component.execute_adb_command',
        return_value=subprocess.CompletedProcess(
            args=[], returncode=0, stdout=''
        ),
    )

    info.get_screen_gui_xml()
    assert mock_exec.call_args_list[0].kwargs['command'] == 'uiautomator dump /dev/tty'
    assert (
        mock_exec.call_args_list[1].kwargs['command']
        == 'uiautomator dump /sdcard/window_dump.xml && cat /sdcard/window_dump.xml && rm -f /sdcard/window_dump.xml'
    )

    assert info.get_touchscreen_info() == TouchscreenInfo(
        node='event8', name='', x_range=(0, 0), y_range=(0, 0)
    )

    mock_exec.return_value = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout=(
            '[ro.serialno]: [SER1]\n'
            '[ro.product.manufacturer]: [  Google  ]\n'
            '[ro.product.model]: []\n'
            '[ro.build.version.release]: [14]\n'
        ),
    )
    assert info.get_device_model(refresh=True) == 'Google'

    mock_exec.return_value = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout=(
            '[ro.serialno]: [SER1]\n'
            '[ro.product.manufacturer]: []\n'
            '[ro.product.model]: [  Pixel  ]\n'
            '[ro.build.version.release]: [14]\n'
        ),
    )
    assert info.get_device_model(refresh=True) == 'Pixel'

    app_obj = info.app('com.example.app')
    assert app_obj.package == 'com.example.app'
    assert app_obj.device_connection is conn
    assert app_obj.serial_number == 'SER1'
    assert app_obj.subprocess_check_flag is True


def test_device_info_all_query_commands_and_retry_failure(
    mocker: MockerFixture,
) -> None:
    conn = MagicMock()
    conn.build_comm_uri.return_value = 'SER1'
    conn.validate_connection.return_value = True
    info = DeviceInfo(conn, 'SER1')
    mock_exec = mocker.patch(
        'device_manager.base_device_component.execute_adb_command'
    )

    def _ok(stdout: str) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args=[], returncode=0, stdout=stdout)

    mock_exec.side_effect = [
        subprocess.CompletedProcess(args=[], returncode=1, stdout=''),
        subprocess.CompletedProcess(args=[], returncode=1, stdout=''),
    ]
    assert info._query_adb('test_cmd') is None

    mock_exec.side_effect = None
    cases = [
        (lambda: info.actual_activity(), 'dumpsys activity activities', '  mCurrentFocus=Window{a com.x/.Y}\n'),
        (lambda: info.is_screen_on(), 'dumpsys deviceidle', '  mScreenOn=true\n'),
        (lambda: info.is_device_locked(), 'dumpsys deviceidle', '  mScreenLocked=false\n'),
        (lambda: info.get_screen_state(), 'dumpsys deviceidle', '  mScreenOn=true\n  mScreenLocked=false\n'),
        (lambda: info.get_properties(refresh=True), 'getprop', '[ro.serialno]: [S]\n[ro.product.manufacturer]: [B]\n[ro.product.model]: [M]\n[ro.build.version.release]: [14]\n'),
        (lambda: info.get_screen_dimensions(refresh=True), 'wm size', 'Physical size: 1080x2400\n'),
        (lambda: info.get_display_orientation(), 'dumpsys display', '  mCurrentOrientation=0\n'),
        (lambda: info.list_installed_all_apps(), 'pm list packages', 'package:com.a\n'),
        (lambda: info.is_app_installed('com.a'), 'pm list packages', 'package:com.a\n'),
        (lambda: info.get_app_path('com.a'), 'pm path com.a', 'package:/data/a.apk\n'),
        (lambda: info.get_location_mode(), 'settings get secure location_mode', '3\n'),
        (lambda: info.is_stay_awake_enabled(), 'settings get global stay_on_while_plugged_in', ' 0 \n'),
        (lambda: info.is_airplane_mode_enabled(), 'settings get global airplane_mode_on', ' 1 \n'),
        (lambda: info.is_app_running('com.a'), 'pidof com.a', '123\n'),
        (lambda: info.get_all_touchscreens(refresh=True), 'getevent -p -l', ''),
    ]
    for fn, expected_cmd, stdout in cases:
        mock_exec.reset_mock()
        mock_exec.return_value = _ok(stdout)
        fn()
        mock_exec.assert_called_once_with(
            command=expected_cmd,
            comm_uris=['SER1'],
            shell=True,
            subprocess_check_flag=False,
            capture_output=True,
            gateway=None,
        )

    conn.validate_connection.return_value = False
    mock_exec.return_value = subprocess.CompletedProcess(args=[], returncode=1, stdout='')
    with pytest.raises(ConnectionError, match=r'^Device not connected$'):
        info.get_display_orientation()
