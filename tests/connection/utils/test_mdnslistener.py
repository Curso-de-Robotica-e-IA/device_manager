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
        connection=ConnectionType.WIFI
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
    result = listener._extract_info( # pyright: ignore[reportPrivateUsage]
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
    result = listener._extract_info( # pyright: ignore[reportPrivateUsage]
        mock_zeroconf.get_service_info(
            'test-type',
            'test-name',
        ),
    )
    expected = ServiceInfo(
        serial_number='emulator',
        ip='127.0.0.1',
        port=5555,
        connection=ConnectionType.WIFI
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
    listener._extract_info( # pyright: ignore[reportPrivateUsage]
        mock_zeroconf.get_service_info(
            'test-type',
            'test-name',
        ),
    )
    captured = capsys.readouterr()
    assert '' in captured.out


def test_add_service(mdns_listener: MDnsListener, mock_zeroconf: MagicMock, mock_mdns_context: MagicMock) -> None:
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
        connection=ConnectionType.WIFI
    )
    mock_mdns_context.add_service.assert_called_once_with(
        info.serial_number,
        info,
    )


def test_update_service(mdns_listener: MDnsListener, mock_zeroconf: MagicMock, mock_mdns_context: MagicMock) -> None:
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
        connection=ConnectionType.WIFI
    )
    mock_mdns_context.add_service.assert_called_once_with(
        info.serial_number,
        info,
    )


def test_remove_service(mdns_listener: MDnsListener, mock_zeroconf: MagicMock, mock_mdns_context: MagicMock) -> None:
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
        connection=ConnectionType.WIFI
    )
    mock_mdns_context.to_offline_service.assert_called_once_with(
        info.serial_number,
        info,
    )
