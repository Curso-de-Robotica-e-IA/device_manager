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
    with pytest.raises(ConnectionError):
        info.get_display_orientation()
    assert info.list_installed_all_apps() == []
    assert info.is_app_installed('com.a') is False
    assert info.get_app_path('com.a') is None
    assert info.get_location_mode() is None
    assert info.is_stay_awake_enabled() is False
    assert info.is_airplane_mode_enabled() is False
