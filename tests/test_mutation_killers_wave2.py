"""Targeted mutation-killing unit tests (Given-When-Then) for Wave 2 modules."""

from __future__ import annotations

import logging
import subprocess
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture
from zeroconf import InterfaceChoice, IPVersion

from device_manager.connection.adb_pairing import AdbPairing
from device_manager.connection.device_connection import (
    DEFAULT_FIXED_PORT,
    DeviceConnection,
)
from device_manager.connection.utils.connection_type import ConnectionType
from device_manager.connection.utils.mdns_context import MDnsContext
from device_manager.connection.utils.mdns_listener import PAIRING_SERVICE_TYPE
from device_manager.connection.utils.mdns_session import MdnsBrowserSession
from device_manager.connection.utils.service_info import ServiceInfo
from device_manager.connection.utils.usb_device_scanner import UsbDeviceScanner
from device_manager.manager import DeviceManager


# ============================================================================
# 1. UsbDeviceScanner
# ============================================================================
def test_usb_scanner_exact_adb_args_and_service_fields() -> None:
    gw = MagicMock()
    gw.run.return_value = subprocess.CompletedProcess(
        args=['adb', 'devices'],
        returncode=0,
        stdout=(
            'List of devices attached\n'
            'USB-01\tdevice\n'
            '192.168.1.5:5555\tdevice\n'
            'USB-02\tunauthorized\n'
        ),
    )
    scanner = UsbDeviceScanner(subprocess_check_flag=True, gateway=gw)

    devices = scanner.list_connected_devices()

    gw.run.assert_called_once_with(
        ['adb', 'devices'],
        capture_output=True,
        text=True,
        check=True,
    )
    assert devices == [
        ServiceInfo(
            serial_number='USB-01',
            ip='',
            port=0,
            connection=ConnectionType.USB,
        )
    ]


# ============================================================================
# 2. MdnsBrowserSession
# ============================================================================
def test_mdns_session_defaults_factory_args_zombies_and_logs(
    caplog: pytest.LogCaptureFixture,
) -> None:
    ctx = MDnsContext()
    created_zcs: list[MagicMock] = []
    browser_calls: list[tuple[object, str, object]] = []

    def zc_factory(**kwargs):
        zc = MagicMock()
        zc.init_kwargs = kwargs
        created_zcs.append(zc)
        return zc

    def browser_factory(zc, service_type, listener):
        browser_calls.append((zc, service_type, listener))
        return MagicMock()

    session = MdnsBrowserSession(
        context=ctx,
        service_type='_adb._tcp.local.',
        service_re_filter=r'^adb-',
        zeroconf_factory=zc_factory,
        browser_factory=browser_factory,
    )
    assert session._max_zc_instances == 10

    with caplog.at_level(
        logging.DEBUG, logger='device_manager.connection.utils.mdns_session'
    ):
        session.start()

    assert len(created_zcs) == 1
    assert created_zcs[0].init_kwargs == {
        'interfaces': InterfaceChoice.Default,
        'unicast': False,
        'ip_version': None,
        'apple_p2p': False,
    }
    zc_arg, svc_type_arg, listener_arg = browser_calls[0]
    assert zc_arg is created_zcs[0]
    assert svc_type_arg == '_adb._tcp.local.'
    assert listener_arg._service_context is ctx  # type: ignore[attr-defined]
    assert listener_arg._MDnsListener__re_filter == r'^adb-'  # type: ignore[attr-defined]
    assert listener_arg._MDnsListener__type_filter == '_adb._tcp.local.'  # type: ignore[attr-defined]
    assert any(
        r.message == 'Started mDNS browser for service_type=_adb._tcp.local.'
        for r in caplog.records
    )

    # Finalizer callback must log and reset state
    assert session._finalize is not None
    with caplog.at_level(
        logging.DEBUG, logger='device_manager.connection.utils.mdns_session'
    ):
        session._finalize()
    assert session.browser is None
    assert session.started is False
    assert any(
        r.message == 'Finalizing Zeroconf instance.' for r in caplog.records
    )

    # Stop must close zeroconf and log exact message
    with caplog.at_level(
        logging.DEBUG, logger='device_manager.connection.utils.mdns_session'
    ):
        session.stop()
    created_zcs[0].close.assert_called_once_with()
    assert any(
        r.message == 'Stopped mDNS browser for service_type=_adb._tcp.local.'
        for r in caplog.records
    )


def test_mdns_session_exact_error_messages_and_zombie_boundary() -> None:
    ctx = MDnsContext()
    session = MdnsBrowserSession(
        context=ctx,
        service_type='_adb._tcp.local.',
        max_zeroconf_instances=1,
        zeroconf_factory=lambda **kw: MagicMock(),
        browser_factory=lambda zc, st, lst: MagicMock(),
    )

    with pytest.raises(AttributeError, match=r'^ServiceBrowser not started$'):
        session.stop()

    # Exact boundary: len(zombies) == max_zc_instances (1 <= 1) MUST still create a new zc
    session._zeroconf_zombies = [MagicMock()]
    session._zeroconf = MagicMock()
    session.start()
    assert len(session._zeroconf_zombies) == 2

    # Above boundary: len(zombies) > max_zc_instances with _zeroconf=None MUST raise exact message
    session2 = MdnsBrowserSession(
        context=ctx,
        service_type='_adb._tcp.local.',
        max_zeroconf_instances=0,
        zeroconf_factory=lambda **kw: MagicMock(),
        browser_factory=lambda zc, st, lst: MagicMock(),
    )
    session2._zeroconf_zombies = [MagicMock()]
    with pytest.raises(AttributeError, match=r'^Zeroconf not configured$'):
        session2.start()

    # RuntimeError wrapping exact message
    def failing_browser(zc, st, lst):
        raise RuntimeError('boom')

    session3 = MdnsBrowserSession(
        context=ctx,
        service_type='_adb._tcp.local.',
        zeroconf_factory=lambda **kw: MagicMock(),
        browser_factory=failing_browser,
    )
    with pytest.raises(
        RuntimeError,
        match=r'^Maximum number of Zeroconf instances reached\.$',
    ):
        session3.start()


# ============================================================================
# 3. AdbPairing
# ============================================================================
def test_adb_pairing_defaults_start_and_exact_gateway_calls_and_logs(
    caplog: pytest.LogCaptureFixture,
) -> None:
    default_pairing = AdbPairing(password='123456')
    assert default_pairing._name == 'robot-celular'
    assert default_pairing._subprocess_check_flag is False
    assert default_pairing._session._service_type == PAIRING_SERVICE_TYPE
    assert default_pairing._session._service_re_filter is None
    assert default_pairing._session._max_zc_instances == 10

    mock_session = MagicMock()
    gw = MagicMock()
    pairing = AdbPairing(
        service_name='svc-a',
        subprocess_check_flag=True,
        password='654321',
        gateway=gw,
        session=mock_session,
    )
    pairing.start()
    mock_session.start.assert_called_once_with(
        interfaces=InterfaceChoice.All,
        unicast=False,
        ip_version=None,
    )

    # pair_devices success + failure exact gateway args & logs
    pairing._context.add_service(
        'SER1', ServiceInfo('SER1', '10.0.0.1', 37123, ConnectionType.WIFI)
    )
    gw.run.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout='Successfully paired to 10.0.0.1:37123\n'
    )
    with caplog.at_level(
        logging.INFO, logger='device_manager.connection.adb_pairing'
    ):
        assert pairing.pair_devices() is True

    gw.run.assert_called_with(
        ['adb', 'pair', '10.0.0.1:37123', '654321'],
        capture_output=True,
        text=True,
        check=True,
    )
    assert any(
        r.message == 'Successfully paired device: uri=10.0.0.1:37123'
        for r in caplog.records
    )

    gw.run.return_value = subprocess.CompletedProcess(
        args=[], returncode=1, stdout='  bad code  \n'
    )
    with caplog.at_level(
        logging.WARNING, logger='device_manager.connection.adb_pairing'
    ):
        assert pairing.pair_devices() is False
    assert any(
        r.message
        == 'Failed to pair device: uri=10.0.0.1:37123 output=bad code'
        for r in caplog.records
    )

    # pair_device_with_paring_code success + failure exact gateway args & logs
    gw.run.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout='Successfully paired to 10.0.0.2:44444\n'
    )
    with caplog.at_level(
        logging.INFO, logger='device_manager.connection.adb_pairing'
    ):
        assert (
            pairing.pair_device_with_paring_code('10.0.0.2:44444', '999888')
            is True
        )
    gw.run.assert_called_with(
        ['adb', 'pair', '10.0.0.2:44444', '999888'],
        capture_output=True,
        text=True,
        check=True,
    )
    assert any(
        r.message == 'Successfully paired device with code: uri=10.0.0.2:44444'
        for r in caplog.records
    )

    gw.run.return_value = subprocess.CompletedProcess(
        args=[], returncode=1, stdout='  rejected  \n'
    )
    with caplog.at_level(
        logging.WARNING, logger='device_manager.connection.adb_pairing'
    ):
        assert (
            pairing.pair_device_with_paring_code('10.0.0.2:44444', '000000')
            is False
        )
    assert any(
        r.message
        == 'Failed to pair device with code: uri=10.0.0.2:44444 output=rejected'
        for r in caplog.records
    )


# ============================================================================
# 4. DeviceConnection
# ============================================================================
def test_device_connection_exact_commands_retries_and_logs(
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
) -> None:
    gw = MagicMock()
    dc = DeviceConnection(subprocess_check_flag=True, gateway=gw)
    assert dc.fixed_port == DEFAULT_FIXED_PORT == 5555
    gw.run.reset_mock()

    # _adb_devices_output exact gateway args
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

    # establish_first_connection default max_retries=5 + logs
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

    # validate_connection missing device log (before patching validate_connection)
    with caplog.at_level(
        logging.DEBUG, logger='device_manager.connection.device_connection'
    ):
        assert dc.validate_connection('GHOST') is False
    assert any(
        r.message == 'No devices currently connected for GHOST'
        for r in caplog.records
    )

    # establish_first_connection succeeds on attempt 2 and does NOT call attempt 3
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

    # __connect_with_fix_port exact gateway args & missing error
    gw.run.reset_mock()
    dc._DeviceConnection__connect_with_fix_port('S1')
    gw.run.assert_called_once_with(
        ['adb', 'connect', '10.0.0.1:5555'],
        check=True,
    )
    with pytest.raises(ValueError, match=r'^device was not found$'):
        dc._DeviceConnection__connect_with_fix_port('NO_SUCH')

    # stop_connection exact gateway args & empty error
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

    # disconnect default subprocess_check_flag=False
    mock_sub_run = mocker.patch(
        'device_manager.connection.device_connection.subprocess.run'
    )
    DeviceConnection.disconnect()
    mock_sub_run.assert_called_once_with(['adb', 'kill-server'], check=False)


# ============================================================================
# 5. DeviceManager
# ============================================================================
def test_device_manager_defaults_forwarding_and_logs(
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
) -> None:
    mock_check = mocker.patch(
        'device_manager.manager.check_adb_dependencies_version'
    )
    mock_dc_cls = mocker.patch('device_manager.manager.DeviceConnection')
    mock_dc_inst = mock_dc_cls.return_value
    usb_svc = ServiceInfo('USB-1', '', 0, ConnectionType.USB)
    mock_dc_inst.usb_scanner.list_connected_devices.return_value = [usb_svc]
    mock_dc_inst.connection_info.get.return_value = None

    with caplog.at_level(logging.INFO, logger='device_manager.manager'):
        dm = DeviceManager()

    mock_check.assert_called_once_with()
    mock_dc_cls.assert_called_once_with(
        subprocess_check_flag=False,
        fixed_port=DEFAULT_FIXED_PORT,
    )
    assert dm.adb_pair is None
    assert dm.subprocess_check is False
    assert dm._devices_fixed_port == DEFAULT_FIXED_PORT
    mock_dc_inst.connection_info.add.assert_called_once_with('USB-1', usb_svc)
    assert any(
        r.message == "Loaded connected USB devices: serials=['USB-1']"
        for r in caplog.records
    )

    # adb_pairing_instance defaults and custom forwarding
    mock_ap_cls = mocker.patch('device_manager.manager.AdbPairing')
    dm.adb_pairing_instance()
    mock_ap_cls.assert_called_once_with(
        service_name='robot_celular',
        service_regex_filter=None,
        subprocess_check_flag=False,
    )

    # execute_adb_command default kwargs forwarding + exact TypeError
    mock_exec = mocker.patch('device_manager.manager.execute_adb_command')
    mock_dc_inst.connection_info.get.return_value = usb_svc
    dm.execute_adb_command('ls')
    mock_exec.assert_called_once_with(
        command='ls',
        comm_uris=['USB-1'],
        shell=True,
        subprocess_check_flag=False,
        capture_output=False,
        gateway=mock_dc_inst._gateway,
    )
    with pytest.raises(
        TypeError,
        match=r"comm_uris must be a list, tuple or None, got <class 'int'>",
    ):
        dm.execute_adb_command('ls', comm_uris=123)  # type: ignore[arg-type]

    # disconnect_devices exact INFO and WARNING logs
    mock_dc_inst.stop_connection.return_value = True
    mock_dc_inst.connection_info.get.return_value = None
    with caplog.at_level(logging.INFO, logger='device_manager.manager'):
        assert dm.disconnect_devices('USB-1') is True
    assert any(
        r.message == "Disconnected devices: serials=['USB-1']"
        for r in caplog.records
    )

    mock_dc_inst.stop_connection.return_value = False
    with caplog.at_level(logging.WARNING, logger='device_manager.manager'):
        assert dm.disconnect_devices('USB-1') is False
    assert any(
        r.message
        == "Failed to disconnect all requested devices: serials=['USB-1']"
        for r in caplog.records
    )
