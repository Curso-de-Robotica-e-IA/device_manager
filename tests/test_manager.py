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
    conn.connection_info.get.side_effect = (
        lambda s: usb_service if s == 'emulator-5554' else None
    )
    conn.build_comm_uri.return_value = 'emulator-5554'

    manager = DeviceManager(check_dependencies=False)
    manager.load_connected_usb_devices()

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


def test_device_manager_nested_device_properties_and_usb_priority() -> None:
    import subprocess
    from unittest.mock import MagicMock

    from device_manager.components.object_manager import ObjectManager
    from device_manager.connection.device_connection import DeviceConnection
    from device_manager.connection.utils.connection_type import ConnectionType
    from device_manager.connection.utils.service_info import ServiceInfo
    from device_manager.manager import DeviceManager

    # 1. DeviceConnection.list_adb_device_states parses USB + Wi-Fi + ignores blank/malformed
    gw = MagicMock()
    gw.run.return_value = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout=(
            'List of devices attached\n'
            '\n'
            'bad_line_no_tab\n'
            'USB_1\tdevice\n'
            '192.168.155.42:5555\tdevice\n'
            '192.168.155.63:5555\tunauthorized\n'
            '192.168.155.65:5555\tdevice\n'
        ),
        stderr='',
    )
    dc = DeviceConnection.__new__(DeviceConnection)
    dc._gateway = gw
    dc._DeviceConnection__subprocess_check_flag = False
    assert dc.list_adb_device_states() == {
        'USB_1': 'device',
        '192.168.155.42:5555': 'device',
        '192.168.155.63:5555': 'unauthorized',
        '192.168.155.65:5555': 'device',
    }

    # 2. Nested properties: connected ⊆ available ⊆ visible, unauthorized ⊆ visible
    conn = MagicMock()
    conn_info: ObjectManager[ServiceInfo] = ObjectManager()
    wifi_registered = ServiceInfo(
        '0088157940', '192.168.155.42', 5555, ConnectionType.WIFI
    )
    conn_info.add('0088157940', wifi_registered)
    conn.connection_info = conn_info
    conn.usb_scanner.list_connected_devices.return_value = []
    conn.list_adb_device_states.return_value = {
        '192.168.155.42:5555': 'device',
        '192.168.155.65:5555': 'device',
        '192.168.155.63:5555': 'unauthorized',
    }
    conn.connection.available_devices.return_value = {
        '0088157940': wifi_registered,
        'MDNS_NEW': ServiceInfo(
            'MDNS_NEW', '192.168.155.99', 41000, ConnectionType.WIFI
        ),
    }

    dm = DeviceManager(check_dependencies=False, connector=conn)
    dm._register_device('0088157940')

    assert dm.connected_devices == ['0088157940']
    # Deduplicated: 192.168.155.42:5555 maps to 0088157940; unauthorized excluded
    assert dm.available_devices == ['0088157940', '192.168.155.65:5555']
    assert dm.unauthorized_devices == ['192.168.155.63:5555']
    assert dm.visible_devices == [
        '0088157940',
        '192.168.155.65:5555',
        '192.168.155.63:5555',
        'MDNS_NEW',
    ]
    assert set(dm.connected_devices) <= set(dm.available_devices)
    assert set(dm.available_devices) <= set(dm.visible_devices)
    assert set(dm.unauthorized_devices) <= set(dm.visible_devices)
    assert set(dm.unauthorized_devices).isdisjoint(set(dm.available_devices))

    # 3. connect_devices accepts already-connected ip:port from available_devices
    conn.visible_devices.return_value = []
    assert dm.connect_devices('192.168.155.65:5555') == ['192.168.155.65:5555']
    assert '192.168.155.65:5555' in dm.connected_devices
    # Calling again when already in connection_info still registers cleanly
    assert dm.connect_devices('192.168.155.65:5555') == ['192.168.155.65:5555']
    # Non-numeric port is rejected
    conn.list_adb_device_states.return_value = {'192.168.155.65:abc': 'device'}
    assert dm.connect_devices('192.168.155.65:abc') == []

    # 4. USB priority over Wi-Fi in load_connected_usb_devices and connect_devices
    usb_svc = ServiceInfo('0088157940', '', 0, ConnectionType.USB)
    conn.usb_scanner.list_connected_devices.return_value = [usb_svc]
    dm.load_connected_usb_devices()
    upgraded = conn.connection_info.get('0088157940')
    assert upgraded is not None
    assert upgraded.connection == ConnectionType.USB

    # connect_devices chooses USB when both USB and Wi-Fi are visible (even if USB appears first)
    conn.visible_devices.return_value = [
        usb_svc,
        ServiceInfo('0088157940', '192.168.155.42', 5555, ConnectionType.WIFI),
    ]
    conn.is_connected.return_value = True
    assert dm.connect_devices('0088157940') == ['0088157940']
    conn.start_connection.assert_not_called()


def test_device_manager_resolves_tcp_serial_and_connects_by_serial_priority(
    mocker: MockerFixture,
) -> None:
    import subprocess
    from unittest.mock import MagicMock

    from device_manager.components.object_manager import ObjectManager
    from device_manager.connection.utils.connection_type import ConnectionType
    from device_manager.connection.utils.service_info import ServiceInfo
    from device_manager.manager import DeviceManager

    conn = MagicMock()
    conn.connection_info = ObjectManager()
    conn.usb_scanner.list_connected_devices.return_value = []
    conn.connection.available_devices.return_value = {}
    conn.visible_devices.return_value = []
    conn.list_adb_device_states.return_value = {
        '192.168.155.65:5555': 'device',
        '192.168.155.70:5555': 'device',
    }

    mock_exec = mocker.patch(
        'device_manager.manager.execute_adb_command',
        side_effect=[
            subprocess.CompletedProcess(
                args=[], returncode=0, stdout='SER_WIFI_1\n', stderr=''
            ),
            RuntimeError('adb error'),
        ],
    )

    dm = DeviceManager(check_dependencies=False, connector=conn)
    assert dm.available_devices == ['SER_WIFI_1', '192.168.155.70:5555']
    # Second call uses cache for 192.168.155.65:5555 (no extra getprop call for it)
    assert dm._resolve_endpoint_serial('192.168.155.65:5555') == 'SER_WIFI_1'
    assert mock_exec.call_count == 2

    # Connect by pure serial -> picks Priority 2 (already-connected TCP ip:5555)
    assert dm.connect_devices('SER_WIFI_1') == ['SER_WIFI_1']
    assert 'SER_WIFI_1' in dm.connected_devices
    svc = conn.connection_info.get('SER_WIFI_1')
    assert svc is not None
    assert svc.ip == '192.168.155.65'
    assert svc.port == 5555
    assert svc.connection == ConnectionType.WIFI

    # Priority 3: mDNS Wi-Fi when not in USB or active TCP
    mdns_svc = ServiceInfo(
        'SER_MDNS', '192.168.155.88', 41000, ConnectionType.WIFI
    )
    conn.visible_devices.return_value = [mdns_svc]
    conn.start_connection.return_value = ['SER_MDNS']
    assert dm.connect_devices('SER_MDNS') == ['SER_MDNS']
