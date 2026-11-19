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
