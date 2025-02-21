# If you exceptionally want to enable socket for one particular execution pass
# --force-enable-socket. It takes precedence over --disable-socket.
import pytest

from device_manager.connection.utils.mdns_listener import (
    DEFAULT_REGEX_FILTER,
    MDnsListener,
    ServiceInfo,
)


@pytest.fixture
def mock_mdns_context(mocker):
    context = mocker.patch(
        'device_manager.connection.utils.mdns_context.MDnsContext',
    )
    context.add_service = mocker.MagicMock(
        return_value=None,
    )
    return context


@pytest.fixture
def mock_zeroconf(mocker):
    zeroconf = mocker.patch(
        'device_manager.connection.utils.mdns_listener.Zeroconf',
    )
    zeroconf.service_info = mocker.MagicMock()
    zeroconf.service_info.adresses = ['127.0.0.1']
    zeroconf.service_info.port = 5555
    zeroconf.service_info.name = 'adb-emulator-5555._adb-tls-pairing._tcp.local.'  # noqa
    zeroconf.service_info.server = 'test-server'
    zeroconf.get_service_info = mocker.MagicMock(
        return_value=zeroconf.service_info,
    )
    return zeroconf


@pytest.fixture
def mdns_listener(mock_mdns_context, mocker):
    listener = MDnsListener(mock_mdns_context)
    extract_info = mocker.patch(
        'device_manager.connection.utils.mdns_listener.MDnsListener._extract_info',  # noqa
    )
    extract_info.return_value = ServiceInfo(
        serial_number='emulator',
        ip='127.0.0.1',
        port=5555,
    )
    return listener


def test_extract_info_with_no_filter(
    mock_zeroconf,
    mock_mdns_context,
    mocker,
):
    listener = MDnsListener(mock_mdns_context)
    mocker.patch(
        'device_manager.connection.utils.mdns_listener.socket.inet_ntoa',
        return_value='127.0.0.1',
    )
    result = listener._extract_info(
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
    )
    assert result == expected


def test_extract_info_with_re_filter(
    mock_zeroconf,
    mock_mdns_context,
    mocker,
):
    listener = MDnsListener(
        mock_mdns_context,
        re_filter=DEFAULT_REGEX_FILTER,
    )
    mocker.patch(
        'device_manager.connection.utils.mdns_listener.socket.inet_ntoa',
        return_value='127.0.0.1',
    )
    result = listener._extract_info(
        mock_zeroconf.get_service_info(
            'test-type',
            'test-name',
        ),
    )
    expected = ServiceInfo(
        serial_number='emulator',
        ip='127.0.0.1',
        port=5555,
    )
    assert result == expected


def test_extract_info_with_no_match(
    mock_zeroconf,
    mock_mdns_context,
    mocker,
    capsys,
):
    listener = MDnsListener(
        mock_mdns_context,
        re_filter=r'a-bad-filter',
    )
    mocker.patch(
        'device_manager.connection.utils.mdns_listener.socket.inet_ntoa',
        return_value='127.0.0.1',
    )
    listener._extract_info(
        mock_zeroconf.get_service_info(
            'test-type',
            'test-name',
        ),
    )
    captured = capsys.readouterr()
    assert 'AdbMDns not match: ' in captured.out


def test_add_service(mdns_listener, mock_zeroconf, mock_mdns_context):
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
        )
    mock_mdns_context.add_service.assert_called_once_with(
        info.serial_number, info,
    )


def test_update_service(mdns_listener, mock_zeroconf, mock_mdns_context):
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
        )
    mock_mdns_context.update_service.assert_called_once_with(
        info.serial_number, info,
    )


def test_remove_service(mdns_listener, mock_zeroconf, mock_mdns_context):
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
        )
    mock_mdns_context.to_offline_service.assert_called_once_with(
        info.serial_number, info,
    )
