import subprocess

from pytest_mock import MockerFixture

from device_manager.connection.connection_manager import ConnectionManager
from device_manager.connection.utils.connection_type import ConnectionType
from device_manager.connection.utils.service_info import ServiceInfo


def test_connection_manager_does_not_kill_server_by_default(
    mocker: MockerFixture,
) -> None:
    mock_run = mocker.patch(
        'device_manager.connection.connection_manager.subprocess.run',
    )
    mock_discovery = mocker.patch(
        'device_manager.connection.connection_manager.AdbConnectionDiscovery',
    )
    mocker.patch('device_manager.connection.connection_manager.sleep')

    cm = ConnectionManager(subprocess_check_flag=False)
    mock_run.assert_called_once_with(
        ['adb', 'start-server'],
        shell=False,
        check=False,
        capture_output=False,
        text=None,
    )
    mock_discovery.return_value.start.assert_called_once()

    cm.close_discovery()
    mock_discovery.return_value.stop_discovery_listener.assert_called_once()


def test_connection_manager_kills_server_when_requested(
    mocker: MockerFixture,
) -> None:
    mock_run = mocker.patch(
        'device_manager.connection.connection_manager.subprocess.run',
    )
    mocker.patch(
        'device_manager.connection.connection_manager.AdbConnectionDiscovery',
    )
    mocker.patch('device_manager.connection.connection_manager.sleep')

    ConnectionManager(restart_adb_server=True)
    calls = [c.args[0] for c in mock_run.call_args_list]
    assert calls == [['adb', 'kill-server'], ['adb', 'start-server']]


def test_check_devices_adb_connection_and_device_connect(
    mocker: MockerFixture,
) -> None:
    mocker.patch('device_manager.connection.connection_manager.sleep')
    mock_discovery_cls = mocker.patch(
        'device_manager.connection.connection_manager.AdbConnectionDiscovery',
    )
    mock_run = mocker.patch(
        'device_manager.connection.connection_manager.subprocess.run',
        return_value=subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout='List of devices attached\n192.168.1.5:5555\tdevice\n',
        ),
    )

    cm = ConnectionManager()
    assert cm.check_devices_adb_connection('192.168.1.5:5555') is True
    assert cm.check_devices_adb_connection('192.168.1.9:5555') is False

    service = ServiceInfo('DEV1', '192.168.1.5', 5555, ConnectionType.WIFI)
    mock_discovery_cls.return_value.get_service_info_for.return_value = service
    mock_run.return_value = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout='connected to 192.168.1.5:5555\n',
    )

    assert cm.device_connect('DEV1') == service
