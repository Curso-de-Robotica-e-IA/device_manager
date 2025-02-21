import pytest


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
def mock_mdns_context(mocker):
    context = mocker.patch(
        'device_manager.connection.utils.mdns_context.MDnsContext',
    )
    context.add_service = mocker.MagicMock(
        return_value=None,
    )
    return context
