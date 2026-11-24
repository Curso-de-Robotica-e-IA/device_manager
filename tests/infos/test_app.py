import subprocess
from unittest.mock import MagicMock

from pytest_mock import MockerFixture

from device_manager.infos.app import AppInfo


def test_app_info_when_disconnected_does_not_raise_attribute_error() -> None:
    conn = MagicMock()
    conn.build_comm_uri.return_value = 'emulator-5554'
    conn.validate_connection.return_value = False

    app = AppInfo('com.example', conn, 'emulator-5554')
    assert app.dumpsys == ''
    assert app.get_property('versionName') is None
    assert app.get_action('MAIN') == ''


def test_app_info_queries_properties_and_actions(mocker: MockerFixture) -> None:
    conn = MagicMock()
    conn.build_comm_uri.return_value = 'emulator-5554'
    conn.validate_connection.return_value = True

    mocker.patch(
        'device_manager.base_device_component.execute_adb_command',
        return_value=subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout='  versionName=1.2.3\n  android.intent.action.MAIN:\n',
        ),
    )

    app = AppInfo('com.example', conn, 'emulator-5554')
    assert app.get_property('versionName') == '1.2.3'
    assert app.get_action('MAIN') == 'android.intent.action.MAIN'


def test_app_info_exact_setup_command_and_get_action(
    mocker,
) -> None:
    import subprocess
    from unittest.mock import MagicMock

    from device_manager.infos.app import AppInfo

    conn = MagicMock()
    conn.build_comm_uri.return_value = 'SER1'
    conn.validate_connection.return_value = True
    mock_exec = mocker.patch(
        'device_manager.base_device_component.execute_adb_command',
        return_value=subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout='  Action: "android.intent.action.MAIN"\n  versionName=1.2.3\n',
        ),
    )

    app = AppInfo('com.example.demo', conn, 'SER1', subprocess_check_flag=True)
    mock_exec.assert_called_once_with(
        command='dumpsys package com.example.demo',
        comm_uris=['SER1'],
        shell=True,
        subprocess_check_flag=True,
        capture_output=True,
        gateway=None,
    )
    assert app.get_action('MAIN') == '"android.intent.action.MAIN'
    assert app.get_property('versionName') == '1.2.3'
