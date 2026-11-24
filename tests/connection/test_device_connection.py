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


def test_device_connection_exact_commands_retries_and_logs(
    mocker,
    caplog,
) -> None:
    import logging
    import subprocess
    from unittest.mock import MagicMock

    import pytest

    from device_manager.connection.device_connection import (
        DEFAULT_FIXED_PORT,
        DeviceConnection,
    )
    from device_manager.connection.utils.connection_type import ConnectionType
    from device_manager.connection.utils.service_info import ServiceInfo

    gw = MagicMock()
    dc = DeviceConnection(subprocess_check_flag=True, gateway=gw)
    assert dc.fixed_port == DEFAULT_FIXED_PORT == 5555
    gw.run.reset_mock()

    gw.run.return_value = subprocess.CompletedProcess(
        args=['adb', 'devices'],
        returncode=0,
        stdout='List of devices attached\n10.0.0.1:5555\tdevice\n',
    )
    dc.connection_info['S1'] = ServiceInfo(
        'S1', '10.0.0.1', 5555, ConnectionType.WIFI
    )
    dc.connection_info['S2'] = ServiceInfo(
        'S2', '10.0.0.2', 5555, ConnectionType.WIFI
    )
    with caplog.at_level(
        logging.DEBUG, logger='device_manager.connection.device_connection'
    ):
        assert dc.check_connections() is False

    gw.run.assert_called_once_with(
        ['adb', 'devices'],
        capture_output=True,
        text=True,
        check=True,
    )
    assert any(
        r.message
        == 'Connected ADB devices:\nList of devices attached\n10.0.0.1:5555\tdevice\n'
        for r in caplog.records
    )

    mocker.patch.object(dc.connection, 'device_connect', return_value=None)
    with caplog.at_level(
        logging.INFO, logger='device_manager.connection.device_connection'
    ):
        assert dc.establish_first_connection('S_MISS') is False
    assert dc.connection.device_connect.call_count == 5
    assert any(
        r.message == 'Trying to connect to S_MISS (attempt 1/5)...'
        for r in caplog.records
    )
    assert any(
        r.message == 'ADB connection attempt failed: serial=S_MISS attempt=5/5'
        for r in caplog.records
    )

    with caplog.at_level(
        logging.DEBUG, logger='device_manager.connection.device_connection'
    ):
        assert dc.validate_connection('GHOST') is False
    assert any(
        r.message == 'No devices currently connected for GHOST'
        for r in caplog.records
    )

    svc_new = ServiceInfo('S1', '10.0.0.1', 33333, ConnectionType.WIFI)
    mocker.patch.object(
        dc.connection, 'device_connect', side_effect=[None, svc_new]
    )
    mocker.patch.object(dc, 'validate_connection', return_value=True)
    gw.run.reset_mock()
    assert dc.establish_first_connection('S1', max_retries=4) is True
    assert dc.connection.device_connect.call_count == 2
    gw.run.assert_called_once_with(
        ['adb', '-s', '10.0.0.1:33333', 'tcpip', '5555'],
        check=True,
    )
    assert dc.connection_info['S1'].port == 5555

    gw.run.reset_mock()
    dc._DeviceConnection__connect_with_fix_port('S1')
    gw.run.assert_called_once_with(
        ['adb', 'connect', '10.0.0.1:5555'],
        check=True,
    )
    with pytest.raises(ValueError, match=r'^device was not found$'):
        dc._DeviceConnection__connect_with_fix_port('NO_SUCH')

    with pytest.raises(
        ValueError, match=r'^No devices selected to disconnect$'
    ):
        dc.stop_connection([])

    gw.run.reset_mock()
    gw.run.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout='disconnected 10.0.0.1:5555\n'
    )
    assert dc.stop_connection(['S1']) is True
    gw.run.assert_called_once_with(
        ['adb', 'disconnect', '10.0.0.1:5555'],
        check=True,
        capture_output=True,
        text=True,
    )

    mock_sub_run = mocker.patch(
        'device_manager.connection.device_connection.subprocess.run'
    )
    DeviceConnection.disconnect()
    mock_sub_run.assert_called_once_with(['adb', 'kill-server'], check=False)
