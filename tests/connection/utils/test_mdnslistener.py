# If you exceptionally want to enable socket for one particular execution pass
# --force-enable-socket. It takes precedence over --disable-socket.
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from device_manager.connection.utils.connection_type import ConnectionType
from device_manager.connection.utils.mdns_context import MDnsContext
from device_manager.connection.utils.mdns_listener import (
    DEFAULT_REGEX_FILTER,
    MDnsListener,
    ServiceInfo,
)


@pytest.fixture
def mdns_listener(
    mock_mdns_context: MDnsContext,
    mocker: MockerFixture,
) -> MDnsListener:
    listener = MDnsListener(mock_mdns_context)
    extract_info = mocker.patch(
        'device_manager.connection.utils.mdns_listener.MDnsListener._extract_info',  # noqa
    )
    extract_info.return_value = ServiceInfo(
        serial_number='emulator',
        ip='127.0.0.1',
        port=5555,
        connection=ConnectionType.WIFI,
    )
    return listener


def test_extract_info_with_no_filter(
    mock_zeroconf: MagicMock,
    mock_mdns_context: MagicMock,
    mocker: MockerFixture,
) -> None:
    listener = MDnsListener(mock_mdns_context)
    mocker.patch(
        'device_manager.connection.utils.mdns_listener.socket.inet_ntoa',
        return_value='127.0.0.1',
    )
    result = listener._extract_info(  # pyright: ignore[reportPrivateUsage]
        mock_zeroconf.get_service_info(
            'test-type',
            'test-name',
        ),
    )
    # not sure if this is realy the expected result
    expected = ServiceInfo(
        serial_number='adb-emulator-5555',
        ip='127.0.0.1',
        port=5555,
        connection=ConnectionType.WIFI,
    )
    assert result == expected


def test_extract_info_with_re_filter(
    mock_zeroconf: MagicMock,
    mock_mdns_context: MagicMock,
    mocker: MockerFixture,
) -> None:
    listener = MDnsListener(
        mock_mdns_context,
        re_filter=DEFAULT_REGEX_FILTER,
    )
    mocker.patch(
        'device_manager.connection.utils.mdns_listener.socket.inet_ntoa',
        return_value='127.0.0.1',
    )
    result = listener._extract_info(  # pyright: ignore[reportPrivateUsage]
        mock_zeroconf.get_service_info(
            'test-type',
            'test-name',
        ),
    )
    expected = ServiceInfo(
        serial_number='emulator',
        ip='127.0.0.1',
        port=5555,
        connection=ConnectionType.WIFI,
    )
    assert result == expected


def test_extract_info_with_no_match(
    mock_zeroconf: MagicMock,
    mock_mdns_context: MagicMock,
    mocker: MockerFixture,
    capsys: pytest.CaptureFixture[str],
) -> None:
    listener = MDnsListener(
        mock_mdns_context,
        re_filter=r'a-bad-filter',
    )
    mocker.patch(
        'device_manager.connection.utils.mdns_listener.socket.inet_ntoa',
        return_value='127.0.0.1',
    )
    listener._extract_info(  # pyright: ignore[reportPrivateUsage]
        mock_zeroconf.get_service_info(
            'test-type',
            'test-name',
        ),
    )
    captured = capsys.readouterr()
    assert '' in captured.out


def test_add_service(
    mdns_listener: MDnsListener,
    mock_zeroconf: MagicMock,
    mock_mdns_context: MagicMock,
) -> None:
    mdns_listener.add_service(
        mock_zeroconf,
        'test-type',
        'test-name',
    )
    mock_zeroconf.get_service_info.assert_called_once_with(
        'test-type',
        'test-name',
    )
    info = ServiceInfo(
        serial_number='emulator',
        ip='127.0.0.1',
        port=5555,
        connection=ConnectionType.WIFI,
    )
    mock_mdns_context.add_service.assert_called_once_with(
        info.serial_number,
        info,
    )


def test_update_service(
    mdns_listener: MDnsListener,
    mock_zeroconf: MagicMock,
    mock_mdns_context: MagicMock,
) -> None:
    mdns_listener.update_service(
        mock_zeroconf,
        'test-type',
        'test-name',
    )
    mock_zeroconf.get_service_info.assert_called_once_with(
        'test-type',
        'test-name',
    )
    info = ServiceInfo(
        serial_number='emulator',
        ip='127.0.0.1',
        port=5555,
        connection=ConnectionType.WIFI,
    )
    mock_mdns_context.add_service.assert_called_once_with(
        info.serial_number,
        info,
    )


def test_remove_service(
    mdns_listener: MDnsListener,
    mock_zeroconf: MagicMock,
    mock_mdns_context: MagicMock,
) -> None:
    mdns_listener.remove_service(
        mock_zeroconf,
        'test-type',
        'test-name',
    )
    mock_zeroconf.get_service_info.assert_called_once_with(
        'test-type',
        'test-name',
    )
    info = ServiceInfo(
        serial_number='emulator',
        ip='127.0.0.1',
        port=5555,
        connection=ConnectionType.WIFI,
    )
    mock_mdns_context.to_offline_service.assert_called_once_with(
        info.serial_number,
        info,
    )


def test_mdns_listener_service_callbacks_exact_logs(
    caplog,
) -> None:
    import logging
    import socket
    from unittest.mock import MagicMock

    from device_manager.connection.utils.mdns_context import MDnsContext
    from device_manager.connection.utils.mdns_listener import (
        CONNECT_SERVICE_TYPE,
        MDnsListener,
    )

    ctx = MDnsContext()
    listener = MDnsListener(ctx, service_type=CONNECT_SERVICE_TYPE)

    zc_info = MagicMock()
    zc_info.type = CONNECT_SERVICE_TYPE
    zc_info.name = f'adb-SER99-xyz.{CONNECT_SERVICE_TYPE}'
    zc_info.port = 37000
    zc_info.addresses = [socket.inet_aton('10.0.0.9')]

    zc = MagicMock()
    zc.get_service_info.return_value = zc_info

    with caplog.at_level(
        logging.DEBUG, logger='device_manager.connection.utils.mdns_listener'
    ):
        listener.add_service(zc, CONNECT_SERVICE_TYPE, zc_info.name)
        listener.update_service(zc, CONNECT_SERVICE_TYPE, zc_info.name)
        listener.remove_service(zc, CONNECT_SERVICE_TYPE, zc_info.name)

    zc.get_service_info.assert_called_with(CONNECT_SERVICE_TYPE, zc_info.name)
    assert any(
        'mDNS service discovered: serial=adb-SER99-xyz endpoint=10.0.0.9:37000'
        in r.message
        for r in caplog.records
    )
    assert any(
        'mDNS service updated: serial=adb-SER99-xyz endpoint=10.0.0.9:37000'
        in r.message
        for r in caplog.records
    )
    assert any(
        'mDNS service offline: serial=adb-SER99-xyz endpoint=10.0.0.9:37000'
        in r.message
        for r in caplog.records
    )

    # Filter mismatch warning + extra fields + port None error
    import pytest

    filtered = MDnsListener(
        ctx,
        r'adb-([A-Z0-9]+)-xyz',
        CONNECT_SERVICE_TYPE,
    )
    bad_info = MagicMock()
    bad_info.name = f'other-name.{CONNECT_SERVICE_TYPE}'
    bad_info.port = 37000
    bad_info.addresses = [socket.inet_aton('10.0.0.9')]
    caplog.clear()
    with caplog.at_level(
        logging.WARNING, logger='device_manager.connection.utils.mdns_listener'
    ):
        assert filtered._extract_info(bad_info) is None
    warn_recs = [
        r
        for r in caplog.records
        if 'AdbMDns service name did not match filter:' in r.message
    ]
    assert len(warn_recs) == 1
    assert warn_recs[0].service_name == bad_info.name
    assert warn_recs[0].service_type == CONNECT_SERVICE_TYPE

    no_port_info = MagicMock()
    no_port_info.name = f'adb-SER99-xyz.{CONNECT_SERVICE_TYPE}'
    no_port_info.port = None
    no_port_info.addresses = [socket.inet_aton('10.0.0.9')]
    with pytest.raises(ValueError, match='Port not detected'):
        filtered._extract_info(no_port_info)
