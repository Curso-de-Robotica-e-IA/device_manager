import pytest
from pytest_mock import MockerFixture

from device_manager.connection.utils.connection_type import ConnectionType
from device_manager.connection.utils.service_info import ServiceInfo
from device_manager.manager import DeviceManager


def test_device_manager_lifecycle_and_iteration(mocker: MockerFixture) -> None:
    mock_conn_cls = mocker.patch('device_manager.manager.DeviceConnection')
    conn = mock_conn_cls.return_value
    usb_service = ServiceInfo('emulator-5554', '', 0, ConnectionType.USB)
    conn.usb_scanner.list_connected_devices.return_value = [usb_service]
    conn.connection_info.get.side_effect = lambda s: usb_service if s == 'emulator-5554' else None
    conn.build_comm_uri.return_value = 'emulator-5554'

    manager = DeviceManager(check_dependencies=False)

    assert len(manager) == 1
    assert 'emulator-5554' in manager
    assert manager.connected_devices == ['emulator-5554']

    info, actions = manager['emulator-5554']
    assert info.serial_number == 'emulator-5554'
    assert actions.serial_number == 'emulator-5554'

    items = list(manager)
    assert len(items) == 1
    assert items[0].serial_number == 'emulator-5554'
    assert items[0].device_info is info
    assert items[0].device_actions is actions

    mock_exec = mocker.patch('device_manager.manager.execute_adb_command')
    manager.execute_adb_command('input keyevent 3')
    mock_exec.assert_called_once()

    with pytest.raises(TypeError):
        manager.execute_adb_command('input keyevent 3', comm_uris='invalid')  # type: ignore[arg-type]

    manager.clear()
    assert len(manager) == 0

