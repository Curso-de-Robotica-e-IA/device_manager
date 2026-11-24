from pathlib import Path
import subprocess
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from device_manager.device_actions import DeviceActions


@pytest.fixture
def mock_connection() -> MagicMock:
    conn = MagicMock()
    conn.build_comm_uri.return_value = '192.168.1.10:5555'
    conn.validate_connection.return_value = True
    return conn


def test_current_comm_uri_is_dynamic(mock_connection: MagicMock) -> None:
    actions = DeviceActions(mock_connection, 'SER123')
    assert actions.serial_number == 'SER123'
    assert actions.current_comm_uri == '192.168.1.10:5555'

    mock_connection.build_comm_uri.return_value = '192.168.1.99:5555'
    assert actions.current_comm_uri == '192.168.1.99:5555'
    assert actions.camera.current_comm_uri == '192.168.1.99:5555'


def test_basic_input_and_app_actions(
    mock_connection: MagicMock,
    mocker: MockerFixture,
    tmp_path: Path,
) -> None:
    mock_exec = mocker.patch(
        'device_manager.base_device_component.execute_adb_command'
    )
    actions = DeviceActions(mock_connection, 'SER123')

    actions.click_by_coordinates(10, 20)
    actions.swipe(0, 0, 100, 200, 300)
    actions.open_app('com.example/.MainActivity')
    actions.open_app('com.example', '.MainActivity')
    actions.close_app('com.example')
    actions.uninstall_apk('com.example')
    actions.turn_on_and_unlock_screen()
    actions.home_button()
    actions.back()
    actions.screen_shot('cap', '/sdcard')
    actions.remove_file(Path('/sdcard/cap.png'))
    actions.push_file('local.txt', '/sdcard/local.txt')
    actions.pull_file(Path('/sdcard/local.txt'), Path('local.txt'))
    actions.set_location_mode('3')
    actions.set_stay_awake(True)
    actions.set_air_plane_mode(False)
    actions.set_accelerometer_rotation(True)

    apk = tmp_path / 'app.apk'
    apk.write_bytes(b'apk')
    actions.install_apk(str(apk), replace=True)

    assert mock_exec.call_count == 20

    with pytest.raises(FileNotFoundError):
        actions.install_apk(str(tmp_path / 'missing.apk'))

    with pytest.raises(ValueError, match='Invalid mode'):
        actions.set_location_mode('9')


def test_safe_screencap_bytes_uses_exec_out_in_memory(
    mock_connection: MagicMock,
    mocker: MockerFixture,
) -> None:
    mock_run = mocker.patch(
        'device_manager.device_actions.subprocess.run',
        return_value=subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=b'\x89PNG\r\n\x1a\nfake',
        ),
    )
    actions = DeviceActions(mock_connection, 'SER123')
    data = actions.safe_screencap_bytes()
    assert data == b'\x89PNG\r\n\x1a\nfake'
    mock_run.assert_called_once_with(
        ['adb', '-s', '192.168.1.10:5555', 'exec-out', 'screencap', '-p'],
        shell=False,
        check=False,
        capture_output=True,
        text=None,
    )

    mock_connection.validate_connection.return_value = False
    mock_run.return_value = subprocess.CompletedProcess(
        args=[], returncode=1, stdout=b''
    )
    from device_manager.exceptions.errors import DeviceDisconnectedError

    with pytest.raises(DeviceDisconnectedError):
        actions.safe_screencap_bytes()


def test_device_actions_exact_commands_and_flags(
    mocker: MockerFixture,
    tmp_path,
) -> None:
    conn = MagicMock()
    conn.build_comm_uri.return_value = 'SER1'
    conn.validate_connection.return_value = True
    gw = MagicMock()
    gw.run.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout=b'\x89PNG\r\n\x1a\nok'
    )
    actions = DeviceActions(conn, 'SER1', subprocess_check_flag=True, gateway=gw)

    assert actions.validate_connection() is True
    conn.validate_connection.assert_called_once_with('SER1', force_reconnect=False)

    assert actions.safe_screencap_bytes() == b'\x89PNG\r\n\x1a\nok'
    gw.run.assert_called_once_with(
        ['adb', '-s', 'SER1', 'exec-out', 'screencap', '-p'],
        capture_output=True,
        check=True,
    )

    apk = tmp_path / 'demo.apk'
    apk.write_bytes(b'apk')
    mock_exec = mocker.patch(
        'device_manager.base_device_component.execute_adb_command',
        return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout=''),
    )
    actions.install_apk(str(apk), replace=False)
    mock_exec.assert_called_with(
        command=f'install {apk.resolve().as_posix()}',
        comm_uris=['SER1'],
        shell=False,
        subprocess_check_flag=True,
        capture_output=False,
        gateway=gw,
    )
    actions.install_apk(str(apk), replace=True)
    mock_exec.assert_called_with(
        command=f'install -r -g {apk.resolve().as_posix()}',
        comm_uris=['SER1'],
        shell=False,
        subprocess_check_flag=True,
        capture_output=False,
        gateway=gw,
    )
    with pytest.raises(FileNotFoundError, match=r'^File not found: missing\.apk$'):
        actions.install_apk('missing.apk')
