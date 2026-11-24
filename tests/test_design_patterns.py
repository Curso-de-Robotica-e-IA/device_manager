import subprocess
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from device_manager.adb_executor import execute_adb_command
from device_manager.cli.device_prompt import DevicePromptCLI
from device_manager.connection.adb_connection_discovery import (
    AdbConnectionDiscovery,
)
from device_manager.connection.strategies import get_connection_strategy
from device_manager.connection.utils.connection_type import ConnectionType
from device_manager.connection.utils.mdns_context import MDnsContext
from device_manager.connection.utils.mdns_session import MdnsBrowserSession
from device_manager.connection.utils.service_info import ServiceInfo
from device_manager.device_info import DeviceInfo
from device_manager.exceptions.errors import (
    DeviceManagerError,
    DeviceNotFoundError,
)
from device_manager.manager import DeviceManager
from device_manager.manager_singleton import (
    get_device_manager,
    reset_device_manager,
)


def test_adb_gateway_dependency_injection() -> None:
    calls: list[list[str]] = []

    class FakeGateway:
        def run(self, args, *, check=False, capture_output=False, text=None):
            calls.append(list(args))
            return subprocess.CompletedProcess(
                args=list(args),
                returncode=0,
                stdout='  mScreenOn=true\n',
            )

    gateway = FakeGateway()
    res = execute_adb_command(
        command='dumpsys deviceidle',
        comm_uris=['emulator-5554'],
        shell=True,
        capture_output=True,
        gateway=gateway,
    )
    assert res.stdout == '  mScreenOn=true\n'
    assert calls == [
        ['adb', '-s', 'emulator-5554', 'shell', 'dumpsys', 'deviceidle']
    ]

    conn = MagicMock()
    conn.build_comm_uri.return_value = 'emulator-5554'
    conn.validate_connection.return_value = True
    info = DeviceInfo(conn, 'emulator-5554', gateway=gateway)
    assert info.is_screen_on() is True


def test_connection_strategy_resolution() -> None:
    usb_service = ServiceInfo('USB1', '', 0, ConnectionType.USB)
    wifi_service = ServiceInfo('WIFI1', '10.0.0.5', 5555, ConnectionType.WIFI)

    usb_strategy = get_connection_strategy(ConnectionType.USB)
    wifi_strategy = get_connection_strategy(ConnectionType.WIFI)

    assert usb_strategy.build_comm_uri(usb_service) == 'USB1'
    assert usb_strategy.format_adb_device_entry(usb_service) == 'USB1\tdevice'
    assert wifi_strategy.build_comm_uri(wifi_service) == '10.0.0.5:5555'
    assert (
        wifi_strategy.format_adb_device_entry(wifi_service)
        == '10.0.0.5:5555\tdevice'
    )

    with pytest.raises(ValueError, match='Unsupported connection type'):
        get_connection_strategy('invalid')  # type: ignore[arg-type]


def test_device_manager_connect_devices_uses_connection_strategy() -> None:
    usb_service = ServiceInfo('USB1', '', 0, ConnectionType.USB)
    wifi_service = ServiceInfo('WIFI1', '10.0.0.5', 5555, ConnectionType.WIFI)

    conn = MagicMock()
    conn.usb_scanner.list_connected_devices.return_value = []
    conn.visible_devices.return_value = [usb_service, wifi_service]
    conn.is_connected.side_effect = lambda s: s == 'USB1'
    conn.start_connection.return_value = ['WIFI1']
    conn.build_comm_uri.side_effect = (
        lambda s: 'USB1' if s == 'USB1' else '10.0.0.5:5555'
    )

    dm = DeviceManager(check_dependencies=False, connector=conn)
    connected = dm.connect_devices('USB1', 'WIFI1', 'MISSING')

    assert connected == ['USB1', 'WIFI1']
    assert 'USB1' in dm
    assert 'WIFI1' in dm
    conn.is_connected.assert_called_once_with('USB1')
    conn.start_connection.assert_called_once_with(['WIFI1'])


def test_mdns_context_wait_event() -> None:
    ctx = MDnsContext()
    assert ctx.wait_for_online_service(timeout=0.01) is False

    svc = ServiceInfo('DEV1', '192.168.1.2', 5555, ConnectionType.WIFI)
    ctx.add_service('DEV1', svc)
    assert ctx.wait_for_online_service(timeout=0.1) is True

    ctx.to_offline_service('DEV1', svc)
    assert ctx.wait_for_online_service(timeout=0.01) is False


def test_mdns_browser_session_lifecycle() -> None:
    ctx = MDnsContext()
    mock_zc = MagicMock()
    mock_browser = MagicMock()

    session = MdnsBrowserSession(
        context=ctx,
        service_type='_adb-tls-connect._tcp.local.',
        zeroconf_factory=lambda **kwargs: mock_zc,
        browser_factory=lambda *args: mock_browser,
    )

    assert session.started is False
    assert session.zeroconf_status is False

    with pytest.raises(AttributeError):
        session.stop()

    session.start()
    assert session.started is True
    assert session.browser is mock_browser
    assert session.zeroconf_status is True

    session.stop()
    mock_zc.close.assert_called_once()
    assert session.started is False
    assert session.browser is None


def test_adb_connection_discovery_context_manager(
    mocker: MockerFixture,
) -> None:
    mock_zc = mocker.patch(
        'device_manager.connection.utils.mdns_session.Zeroconf',
    )
    mocker.patch('device_manager.connection.utils.mdns_session.ServiceBrowser')

    discovery = AdbConnectionDiscovery()
    with discovery.start_discovery_listener():
        assert discovery.service_browser_started is True
    mock_zc.return_value.close.assert_called_once()
    assert discovery.service_browser_started is False


def test_device_manager_factory_context_manager_and_exceptions() -> None:
    conn = MagicMock()
    conn.usb_scanner.list_connected_devices.return_value = []

    with DeviceManager(check_dependencies=False, connector=conn) as dm:
        with pytest.raises(DeviceNotFoundError) as exc_info:
            _ = dm['MISSING']
        assert isinstance(exc_info.value, DeviceManagerError)
        assert isinstance(exc_info.value, ValueError)

    conn.close.assert_called_once()


def test_get_device_manager_provider_and_reset() -> None:
    reset_device_manager()
    conn = MagicMock()
    conn.usb_scanner.list_connected_devices.return_value = []

    dm1 = get_device_manager(check_dependencies=False, connector=conn)
    dm2 = get_device_manager(check_dependencies=False, connector=conn)
    assert dm1 is dm2

    reset_device_manager()
    dm3 = get_device_manager(check_dependencies=False, connector=conn)
    assert dm3 is not dm1
    reset_device_manager()


def test_device_prompt_cli(mocker: MockerFixture) -> None:
    conn_mgr = MagicMock()
    conn_mgr.device_pairing.return_value = True
    conn_mgr.available_devices.return_value = {
        'DEV1': ServiceInfo('DEV1', '192.168.1.5', 5555, ConnectionType.WIFI),
    }
    mock_prompt = mocker.patch(
        'device_manager.cli.device_prompt.Prompt.ask',
        side_effect=['N', 'N', '1', 'N'],
    )

    cli = DevicePromptCLI(conn_mgr, console=MagicMock())
    selected = cli.prompt_device_connection()

    assert selected == ['DEV1']
    conn_mgr.device_pairing.assert_called_once_with(5)
    assert mock_prompt.call_count == 4


def test_async_adb_pairing_decoupled_from_sync_lsp() -> None:
    from collections.abc import MutableMapping

    from device_manager.asyncio_dm.async_adb_pairing import AsyncAdbPairing
    from device_manager.components.object_manager import ObjectManager
    from device_manager.connection.adb_pairing import AdbPairing

    assert not issubclass(AsyncAdbPairing, AdbPairing)
    assert isinstance(ObjectManager(), MutableMapping)


def test_device_info_native_xml_via_injected_gateway() -> None:
    conn = MagicMock()
    conn.build_comm_uri.return_value = 'emulator-5554'
    conn.validate_connection.return_value = True

    gw = MagicMock()
    gw.run.return_value = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout='UI dumped\n<?xml version="1.0"?><hierarchy />',
    )
    info = DeviceInfo(conn, 'emulator-5554', gateway=gw)

    assert info.get_screen_gui_xml() == '<?xml version="1.0"?><hierarchy />'


def test_usb_scanner_accepts_injected_gateway() -> None:
    from device_manager.connection.utils.usb_device_scanner import (
        UsbDeviceScanner,
    )

    class FakeGateway:
        def run(self, args, *, check=False, capture_output=False, text=None):
            return subprocess.CompletedProcess(
                args=list(args),
                returncode=0,
                stdout='List of devices attached\nemulator-5554\tdevice\n',
            )

    scanner = UsbDeviceScanner(
        subprocess_check_flag=False,
        gateway=FakeGateway(),
    )
    assert scanner.list_all_devices() == {'emulator-5554': 'device'}


def test_mdns_session_defaults_factory_args_zombies_and_logs(
    caplog: pytest.LogCaptureFixture,
) -> None:
    import logging

    from zeroconf import InterfaceChoice

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

    session._zeroconf_zombies = [MagicMock()]
    session._zeroconf = MagicMock()
    session.start()
    assert len(session._zeroconf_zombies) == 2

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
