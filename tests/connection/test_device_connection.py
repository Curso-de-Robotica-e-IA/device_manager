import subprocess
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from device_manager.connection.device_connection import DeviceConnection
from device_manager.connection.utils.connection_status import (
    ConnectionInfoStatus,
)
from device_manager.connection.utils.connection_type import ConnectionType
from device_manager.connection.utils.service_info import ServiceInfo


@pytest.fixture
def device_connection(mocker: MockerFixture) -> DeviceConnection:
    mocker.patch('device_manager.connection.device_connection.ConnectionManager')
    mocker.patch('device_manager.connection.device_connection.UsbDeviceScanner')
    return DeviceConnection(subprocess_check_flag=False)


def test_validate_connection_does_not_recurse_infinitely(
    device_connection: DeviceConnection,
    mocker: MockerFixture,
) -> None:
    wifi_dev = ServiceInfo(
        serial_number='WIFI01',
        ip='192.168.1.50',
        port=5555,
        connection=ConnectionType.WIFI,
    )
    device_connection.connection_info.add('WIFI01', wifi_dev)
    device_connection.connection.check_wireless_adb_service_for.return_value = (
        ConnectionInfoStatus.DOWN
    )
    device_connection.connection.check_devices_adb_connection.return_value = False

    mock_establish = mocker.patch.object(
        device_connection,
        'establish_first_connection',
        return_value=False,
    )
    mock_disconnect = mocker.patch.object(device_connection, 'disconnect')
    mock_connect_all = mocker.patch.object(device_connection, 'connect_all_devices')

    result = device_connection.validate_connection('WIFI01', force_reconnect=True)

    assert result is False
    mock_establish.assert_called_once_with('WIFI01')
    mock_disconnect.assert_called_once()
    mock_connect_all.assert_called_once()


def test_build_comm_uri_and_is_connected(
    device_connection: DeviceConnection,
) -> None:
    usb_dev = ServiceInfo('USB01', '', 0, ConnectionType.USB)
    wifi_dev = ServiceInfo('WIFI01', '192.168.1.20', 5555, ConnectionType.WIFI)
    device_connection.connection_info.add('USB01', usb_dev)
    device_connection.connection_info.add('WIFI01', wifi_dev)

    assert device_connection.build_comm_uri('USB01') == 'USB01'
    assert device_connection.build_comm_uri('WIFI01') == '192.168.1.20:5555'
    with pytest.raises(ValueError, match='device was not found'):
        device_connection.build_comm_uri('UNKNOWN')

    adb_out = 'List of devices attached\nUSB01\tdevice\n192.168.1.20:5555\tdevice\n'
    assert device_connection.is_connected('USB01', devices_connected=adb_out) is True
    assert device_connection.is_connected('WIFI01', devices_connected=adb_out) is True
    assert device_connection.is_connected('UNKNOWN', devices_connected=adb_out) is False


def test_stop_connection(
    device_connection: DeviceConnection,
    mocker: MockerFixture,
) -> None:
    with pytest.raises(ValueError, match='No devices selected'):
        device_connection.stop_connection([])

    wifi_dev = ServiceInfo('WIFI01', '192.168.1.20', 5555, ConnectionType.WIFI)
    device_connection.connection_info.add('WIFI01', wifi_dev)
    mocker.patch(
        'device_manager.connection.device_connection.subprocess.run',
        return_value=subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout='disconnected 192.168.1.20:5555\n',
        ),
    )

    assert device_connection.stop_connection(['WIFI01']) is True
    assert device_connection.connection_info.get('WIFI01') is None
