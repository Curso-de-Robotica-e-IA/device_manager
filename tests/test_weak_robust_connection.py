"""Weak Robust Equivalence Class tests for the connection subsystem."""

import subprocess
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from device_manager.connection.adb_connection_discovery import (
    AdbConnectionDiscovery,
)
from device_manager.connection.adb_pairing import AdbPairing
from device_manager.connection.connection_manager import ConnectionManager
from device_manager.connection.device_connection import DeviceConnection
from device_manager.connection.strategies import (
    UsbConnectionStrategy,
    WifiConnectionStrategy,
)
from device_manager.connection.utils.connection_status import (
    ConnectionInfoStatus,
)
from device_manager.connection.utils.connection_type import ConnectionType
from device_manager.connection.utils.mdns_context import MDnsContext
from device_manager.connection.utils.mdns_listener import MDnsListener
from device_manager.connection.utils.mdns_session import MdnsBrowserSession
from device_manager.connection.utils.service_info import ServiceInfo


class _StaticGateway:
    def __init__(self, stdout: str = '', returncode: int = 0) -> None:
        self.stdout = stdout
        self.returncode = returncode
        self.calls: list[list[str]] = []

    def run(self, args, *, check=False, capture_output=False, text=None):
        self.calls.append(list(args))
        return subprocess.CompletedProcess(
            args=list(args),
            returncode=self.returncode,
            stdout=self.stdout,
            stderr='',
        )


# ============================================================================
# 1. AdbConnectionDiscovery.connection_status_for_device — Weak Robust
# ============================================================================
@pytest.mark.parametrize(
    ('online_map', 'offline_map', 'query_service', 'expected_status'),
    [
        pytest.param(
            {},
            {'S1': ServiceInfo('S1', '10.0.0.1', 5555, ConnectionType.WIFI)},
            ServiceInfo('S1', '10.0.0.1', 5555, ConnectionType.WIFI),
            ConnectionInfoStatus.DOWN,
            id='[Vs1]-service_offline_down',
        ),
        pytest.param(
            {},
            {},
            ServiceInfo('S1', '10.0.0.1', 5555, ConnectionType.WIFI),
            ConnectionInfoStatus.UNKNOWN,
            id='[Vs2]-service_unknown',
        ),
        pytest.param(
            {'S1': ServiceInfo('S1', '10.0.0.1', 5555, ConnectionType.WIFI)},
            {},
            ServiceInfo('S1', '10.0.0.1', 5555, ConnectionType.WIFI),
            ConnectionInfoStatus.UPDATED,
            id='[Vs3]-service_online_same_ip_updated',
        ),
        pytest.param(
            {'S1': ServiceInfo('S1', '10.0.0.9', 5555, ConnectionType.WIFI)},
            {},
            ServiceInfo('S1', '10.0.0.1', 5555, ConnectionType.WIFI),
            ConnectionInfoStatus.CHANGED,
            id='[Vs4]-service_online_different_ip_changed',
        ),
    ],
)
def test_discovery_connection_status_weak_robust_valid(
    online_map: dict[str, ServiceInfo],
    offline_map: dict[str, ServiceInfo],
    query_service: ServiceInfo,
    expected_status: ConnectionInfoStatus,
) -> None:
    discovery = AdbConnectionDiscovery()
    for k, v in online_map.items():
        discovery._AdbConnectionDiscovery__context.add_service(k, v)  # type: ignore[attr-defined]
    for k, v in offline_map.items():
        discovery._AdbConnectionDiscovery__context.to_offline_service(k, v)  # type: ignore[attr-defined]

    assert (
        discovery.connection_status_for_device(query_service)
        == expected_status
    )
    assert discovery.online_devices() == online_map
    assert discovery.offline_devices() == offline_map
    assert discovery.browser is None
    assert discovery.zeroconf_status is False
    expected_info = online_map.get(query_service.serial_number)
    assert (
        discovery.get_service_info_for(query_service.serial_number)
        == expected_info
    )


# ============================================================================
# 2. AdbPairing.pair_device_with_paring_code — Weak Robust
# ============================================================================
@pytest.mark.parametrize(
    ('comm_uri', 'pair_code', 'stdout', 'expected'),
    [
        pytest.param(
            '192.168.1.50:40000',
            '123456',
            'Successfully paired to 192.168.1.50:40000\n',
            True,
            id='[Vu1,Vp1]-pairing_code_success',
        ),
        pytest.param(
            '192.168.1.50:40000',
            '000000',
            'Failed: wrong pairing code\n',
            False,
            id='[Vu1,Ip1]-pairing_code_rejected',
        ),
    ],
)
def test_pair_device_with_pairing_code_weak_robust(
    comm_uri: str,
    pair_code: str,
    stdout: str,
    expected: bool,
) -> None:
    pairing = AdbPairing(gateway=_StaticGateway(stdout=stdout))
    assert (
        pairing.pair_device_with_paring_code(comm_uri, pair_code) is expected
    )


# ============================================================================
# 3. ConnectionManager — Weak Robust
# ============================================================================
def test_connection_manager_methods_weak_robust(mocker: MockerFixture) -> None:
    mocker.patch('device_manager.connection.connection_manager.sleep')
    mock_disc_cls = mocker.patch(
        'device_manager.connection.connection_manager.AdbConnectionDiscovery'
    )
    disc = mock_disc_cls.return_value
    svc = ServiceInfo('DEV1', '10.0.0.5', 5555, ConnectionType.WIFI)
    disc.online_devices.return_value = {'DEV1': svc}
    disc.connection_status_for_device.return_value = (
        ConnectionInfoStatus.UPDATED
    )

    gw = _StaticGateway(stdout='failed to connect to 10.0.0.5:5555\n')
    cm = ConnectionManager(gateway=gw)

    assert cm.available_devices() == {'DEV1': svc}
    assert (
        cm.check_wireless_adb_service_for(svc) == ConnectionInfoStatus.UPDATED
    )

    disc.get_service_info_for.return_value = None
    assert cm.device_connect('MISSING') is None

    disc.get_service_info_for.return_value = svc
    assert cm.device_connect('DEV1') == svc

    mocker.patch.object(cm, 'check_devices_adb_connection', return_value=True)
    assert cm.validate_and_reconnect_device(svc) == svc

    mocker.patch.object(cm, 'check_devices_adb_connection', return_value=False)
    assert cm.validate_and_reconnect_device(svc) == svc


def test_connection_manager_deprecated_device_pairing(
    mocker: MockerFixture,
) -> None:
    mock_pairing_cls = mocker.patch(
        'device_manager.connection.connection_manager.AdbPairing'
    )
    mock_pairing = mock_pairing_cls.return_value
    mock_pairing.pair_devices.return_value = True
    mocker.patch('device_manager.connection.connection_manager.show_qr_window')

    with pytest.warns(DeprecationWarning, match='deprecated'):
        assert ConnectionManager.device_pairing(timeout_s=0.01) is True
    mock_pairing.start.assert_called_once()
    mock_pairing.stop_pair_listener.assert_called_once()


# ============================================================================
# 4. DeviceConnection — Weak Robust (full lifecycle + error paths)
# ============================================================================
def test_device_connection_lifecycle_weak_robust_valid(
    mocker: MockerFixture,
) -> None:
    mock_cm_cls = mocker.patch(
        'device_manager.connection.device_connection.ConnectionManager'
    )
    mock_usb_cls = mocker.patch(
        'device_manager.connection.device_connection.UsbDeviceScanner'
    )
    wifi_svc = ServiceInfo('WIFI1', '10.0.0.5', 40000, ConnectionType.WIFI)
    usb_svc = ServiceInfo('USB1', '', 0, ConnectionType.USB)
    mock_cm_cls.return_value.available_devices.return_value = {
        'WIFI1': wifi_svc
    }
    mock_usb_cls.return_value.list_connected_devices.return_value = [usb_svc]
    mock_cm_cls.return_value.device_connect.return_value = wifi_svc
    mock_cm_cls.return_value.check_wireless_adb_service_for.return_value = (
        ConnectionInfoStatus.UPDATED
    )
    mock_cm_cls.return_value.check_devices_adb_connection.return_value = True

    gw = _StaticGateway(
        stdout='List of devices attached\n10.0.0.5:5555\tdevice\n',
    )

    with DeviceConnection(gateway=gw) as dc:
        assert dc.visible_devices() == [wifi_svc, usb_svc]
        assert dc.check_connections() is False
        assert dc.validate_connection('MISSING') is False

        assert dc.establish_first_connection('WIFI1', max_retries=2) is True
        assert dc.establish_first_connection('WIFI1', max_retries=1) is True
        assert dc.is_connected('WIFI1') is True
        assert dc.check_connections() is True

        mocker.patch.object(dc, 'disconnect')
        connected = dc.start_connection(['WIFI1'])
        assert connected == ['WIFI1']

    mock_cm_cls.return_value.close_discovery.assert_called_once()


def test_device_connection_retry_failure_and_disconnect_static(
    mocker: MockerFixture,
) -> None:
    mock_cm_cls = mocker.patch(
        'device_manager.connection.device_connection.ConnectionManager'
    )
    mocker.patch(
        'device_manager.connection.device_connection.UsbDeviceScanner'
    )
    mock_cm_cls.return_value.device_connect.return_value = None

    dc = DeviceConnection(gateway=_StaticGateway())
    assert dc.establish_first_connection('NO_DEV', max_retries=2) is False

    mock_run = mocker.patch(
        'device_manager.connection.device_connection.subprocess.run'
    )
    DeviceConnection.disconnect()
    mock_run.assert_called_once_with(['adb', 'kill-server'], check=False)


def test_device_connection_private_port_helpers_invalid(
    mocker: MockerFixture,
) -> None:
    mocker.patch(
        'device_manager.connection.device_connection.ConnectionManager'
    )
    mocker.patch(
        'device_manager.connection.device_connection.UsbDeviceScanner'
    )
    dc = DeviceConnection(gateway=_StaticGateway())

    with pytest.raises(ValueError, match='device was not found'):
        dc._DeviceConnection__connect_with_fix_port('MISSING')  # type: ignore[attr-defined]

    mocker.patch.object(dc, 'validate_connection', return_value=True)
    mocker.patch.object(dc, 'build_comm_uri', return_value='10.0.0.5:40000')
    with pytest.raises(ValueError, match='device not found'):
        dc._DeviceConnection__fix_adb_port('MISSING')  # type: ignore[attr-defined]


# ============================================================================
# 5. ConnectionStrategy, MDnsListener & MdnsBrowserSession edge cases
# ============================================================================
def test_strategies_remaining_paths() -> None:
    usb_strategy = UsbConnectionStrategy()
    wifi_strategy = WifiConnectionStrategy()

    conn = MagicMock()
    conn.usb_scanner.validate_connection.return_value = True
    usb_svc = ServiceInfo('USB1', '', 0, ConnectionType.USB)
    assert usb_strategy.validate(conn, usb_svc) is True

    assert wifi_strategy.connect(conn, []) == []

    wifi_svc = ServiceInfo('WIFI1', '10.0.0.5', 5555, ConnectionType.WIFI)
    conn.connection.check_wireless_adb_service_for.return_value = (
        ConnectionInfoStatus.UPDATED
    )
    conn.connection.check_devices_adb_connection.return_value = True
    assert wifi_strategy.validate(conn, wifi_svc) is True


def test_mdns_listener_extract_info_weak_robust_invalid() -> None:
    listener = MDnsListener(MDnsContext())
    assert listener._extract_info(None) is None

    bad_info = MagicMock()
    bad_info.addresses = [b'\x7f\x00\x00\x01']
    bad_info.port = None
    bad_info.name = 'adb-test._adb-tls-connect._tcp.local.'
    with pytest.raises(ValueError, match='Port not detected'):
        listener._extract_info(bad_info)


def test_mdns_browser_session_zombies_and_limit() -> None:
    ctx = MDnsContext()
    mock_zc = MagicMock()
    session = MdnsBrowserSession(
        context=ctx,
        service_type='_adb-tls-connect._tcp.local.',
        max_zeroconf_instances=0,
        zeroconf_factory=lambda **kwargs: mock_zc,
        browser_factory=lambda *args: MagicMock(),
    )
    session.start()
    session.stop()
    session.start()
    assert len(session._zeroconf_zombies) == 1

    # Exceed max_zeroconf_instances when _zeroconf is None
    session.stop()
    session._zeroconf = None
    with pytest.raises(AttributeError, match='Zeroconf not configured'):
        session.start()


def test_usb_strategy_validate_passes_exact_serial() -> None:
    from unittest.mock import MagicMock

    from device_manager.connection.strategies import UsbConnectionStrategy
    from device_manager.connection.utils.connection_type import ConnectionType
    from device_manager.connection.utils.service_info import ServiceInfo

    connector = MagicMock()
    connector.usb_scanner.validate_connection.return_value = True
    svc = ServiceInfo('USB-99', '', 0, ConnectionType.USB)

    assert UsbConnectionStrategy().validate(connector, svc) is True
    connector.usb_scanner.validate_connection.assert_called_once_with('USB-99')


@pytest.mark.parametrize(
    ('mdns_status', 'adb_connected'),
    [
        pytest.param(
            ConnectionInfoStatus.UPDATED,
            False,
            id='updated_but_adb_disconnected',
        ),
        pytest.param(
            ConnectionInfoStatus.CHANGED,
            True,
            id='changed_but_adb_connected',
        ),
    ],
)
def test_wifi_strategy_validate_single_fault_no_reconnect(
    mdns_status: ConnectionInfoStatus,
    adb_connected: bool,
    caplog: pytest.LogCaptureFixture,
) -> None:
    import logging
    from unittest.mock import MagicMock

    from device_manager.connection.strategies import WifiConnectionStrategy
    from device_manager.connection.utils.connection_type import ConnectionType
    from device_manager.connection.utils.service_info import ServiceInfo

    connector = MagicMock()
    connector.connection.check_wireless_adb_service_for.return_value = (
        mdns_status
    )
    connector.connection.check_devices_adb_connection.return_value = (
        adb_connected
    )
    svc = ServiceInfo('WIFI-1', '10.0.0.1', 5555, ConnectionType.WIFI)

    with caplog.at_level(
        logging.DEBUG, logger='device_manager.connection.strategies'
    ):
        result = WifiConnectionStrategy().validate(connector, svc)

    assert result is False
    connector.connection.check_wireless_adb_service_for.assert_called_once_with(
        svc
    )
    connector.connection.check_devices_adb_connection.assert_called_once_with(
        '10.0.0.1:5555'
    )
    connector.establish_first_connection.assert_not_called()
    expected_msg = (
        'Wi-Fi validation failed (no reconnect): '
        f'serial=WIFI-1 uri=10.0.0.1:5555 mdns_status={mdns_status.name} '
        f'adb_connected={adb_connected}'
    )
    assert any(r.message == expected_msg for r in caplog.records)


def test_wifi_strategy_validate_force_reconnect_logs_exact_warning(
    caplog: pytest.LogCaptureFixture,
) -> None:
    import logging
    from unittest.mock import MagicMock

    from device_manager.connection.strategies import WifiConnectionStrategy
    from device_manager.connection.utils.connection_type import ConnectionType
    from device_manager.connection.utils.service_info import ServiceInfo

    connector = MagicMock()
    connector.connection.check_wireless_adb_service_for.return_value = (
        ConnectionInfoStatus.UPDATED
    )
    connector.connection.check_devices_adb_connection.return_value = False
    connector.validate_connection.side_effect = [False, True]
    svc = ServiceInfo('WIFI-2', '10.0.0.2', 5555, ConnectionType.WIFI)

    with caplog.at_level(
        logging.WARNING, logger='device_manager.connection.strategies'
    ):
        result = WifiConnectionStrategy().validate(
            connector, svc, force_reconnect=True
        )

    assert result is True
    connector.establish_first_connection.assert_called_once_with('WIFI-2')
    connector.disconnect.assert_called_once_with()
    connector.connect_all_devices.assert_called_once_with()
    assert connector.validate_connection.call_count == 2
    expected_msg = (
        'Wi-Fi connection invalid; attempting targeted reconnect: '
        'serial=WIFI-2 uri=10.0.0.2:5555 mdns_status=UPDATED adb_connected=False'
    )
    assert any(r.message == expected_msg for r in caplog.records)
