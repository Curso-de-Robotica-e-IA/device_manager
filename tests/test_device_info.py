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


def test_safe_screencap_bytes_try_first_and_fast_u2(
    mock_connection: MagicMock,
    mocker: MockerFixture,
) -> None:
    import numpy as np

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

    # 3. fast=True uses cached uiautomator2 connection and returns valid PNG bytes
    fake_u2_dev = MagicMock()
    fake_u2_dev.screenshot.return_value = np.zeros((4, 4, 3), dtype=np.uint8)
    mock_connect = mocker.patch(
        'uiautomator2.connect', return_value=fake_u2_dev
    )
    png1 = actions.safe_screencap_bytes(fast=True)
    png2 = actions.safe_screencap_bytes(fast=True)
    assert png1 is not None and png1.startswith(b'\x89PNG\r\n\x1a\n')
    assert png2 is not None and png2.startswith(b'\x89PNG\r\n\x1a\n')
    mock_connect.assert_called_once_with('192.168.1.10:5555')

    # 4. fast=True falls back to adb exec-out when imencode returns False or u2 raises
    mocker.patch('cv2.imencode', return_value=(False, None))
    gw.run.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout=b'\x89PNG\r\n\x1a\nfallback'
    )
    assert actions.safe_screencap_bytes(fast=True) == b'\x89PNG\r\n\x1a\nfallback'

    fake_u2_dev.screenshot.side_effect = RuntimeError('u2 down')
    assert actions.safe_screencap_bytes(fast=True) == b'\x89PNG\r\n\x1a\nfallback'
    assert actions._ui_device is None
