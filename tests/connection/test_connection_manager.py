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


def test_connection_manager_exact_adb_args_and_logs(
    mocker,
    caplog,
) -> None:
    import logging
    import subprocess
    from unittest.mock import MagicMock

    from device_manager.connection.connection_manager import ConnectionManager
    from device_manager.connection.utils.connection_type import ConnectionType
    from device_manager.connection.utils.service_info import ServiceInfo

    mocker.patch('device_manager.connection.connection_manager.sleep')
    mock_disc_cls = mocker.patch(
        'device_manager.connection.connection_manager.AdbConnectionDiscovery'
    )
    mock_disc = mock_disc_cls.return_value

    gw = MagicMock()
    cm = ConnectionManager(
        subprocess_check_flag=True,
        restart_adb_server=True,
        gateway=gw,
    )
    assert gw.run.call_args_list == [
        mocker.call(['adb', 'kill-server'], check=True),
        mocker.call(['adb', 'start-server'], check=True),
    ]
    mock_disc.start.assert_called_once()

    # check_devices_adb_connection exact args & matching
    mock_run = mocker.patch(
        'device_manager.connection.connection_manager.subprocess.run',
        return_value=subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout='List of devices attached\n10.0.0.1:5555\tdevice\n10.0.0.2:5555\toffline\n',
        ),
    )
    assert cm.check_devices_adb_connection('10.0.0.1:5555') is True
    mock_run.assert_called_with(
        ['adb', 'devices'],
        capture_output=True,
        text=True,
        check=False,
    )
    assert (
        cm.check_devices_adb_connection(
            '10.0.0.2:5555', subprocess_check_flag=True
        )
        is False
    )
    mock_run.assert_called_with(
        ['adb', 'devices'],
        capture_output=True,
        text=True,
        check=True,
    )

    # device_connect exact args & logs
    svc = ServiceInfo('S1', '10.0.0.1', 5555, ConnectionType.WIFI)
    mock_disc.get_service_info_for.return_value = svc
    gw.run.reset_mock()
    gw.run.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout='connected to 10.0.0.1:5555\n'
    )
    with caplog.at_level(
        logging.INFO, logger='device_manager.connection.connection_manager'
    ):
        assert cm.device_connect('S1') == svc
    assert 'Connected to device: serial=S1 uri=10.0.0.1:5555' in caplog.text
    gw.run.assert_called_once_with(
        ['adb', 'connect', '10.0.0.1:5555'],
        capture_output=True,
        text=True,
        check=True,
    )

    caplog.clear()
    gw.run.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout='failed to connect to 10.0.0.1:5555\n'
    )
    with caplog.at_level(
        logging.WARNING, logger='device_manager.connection.connection_manager'
    ):
        assert cm.device_connect('S1') == svc
    assert 'Failed to connect device: serial=S1 uri=10.0.0.1:5555' in caplog.text

    caplog.clear()
    mock_disc.get_service_info_for.return_value = None
    with caplog.at_level(
        logging.WARNING, logger='device_manager.connection.connection_manager'
    ):
        assert cm.device_connect('MISSING') is None
    assert 'Device service not online or located: serial=MISSING' in caplog.text

    # device_pairing deprecation warning, log, and exact call sequence
    import pytest

    mock_pairing_cls = mocker.patch(
        'device_manager.connection.connection_manager.AdbPairing'
    )
    mock_pairing = mock_pairing_cls.return_value
    mock_pairing.pair_devices.return_value = True
    mock_show_qr = mocker.patch(
        'device_manager.connection.connection_manager.show_qr_window'
    )
    caplog.clear()
    with (
        caplog.at_level(
            logging.WARNING,
            logger='device_manager.connection.connection_manager',
        ),
        pytest.warns(
            DeprecationWarning,
            match='ConnectionManager.device_pairing is deprecated; use AdbPairing directly.',
        ),
    ):
        assert ConnectionManager.device_pairing(timeout_s=7.5) is True
    assert (
        'ConnectionManager.device_pairing is deprecated; use AdbPairing directly.'
        in caplog.text
    )
    mock_pairing.start.assert_called_once()
    mock_show_qr.assert_called_once_with(mock_pairing.qrcode_image)
    mock_pairing._context.wait_for_online_service.assert_called_once_with(
        timeout=7.5
    )
    mock_pairing.pair_devices.assert_called_once()
    mock_pairing.stop_pair_listener.assert_called_once()
