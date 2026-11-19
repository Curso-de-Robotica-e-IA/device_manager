from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from device_manager.connection.adb_pairing import AdbPairing
from device_manager.connection.utils.mdns_session import MdnsBrowserSession


@pytest.fixture
def sample_service(mocker: MockerFixture) -> MagicMock:
    service = mocker.MagicMock()
    service.ip = '192.168.155.87'
    service.port = 5555
    return service


@pytest.fixture
def mock_zeroconf_session(mocker: MockerFixture) -> MagicMock:
    mock_zc = mocker.patch(
        'device_manager.connection.utils.mdns_session.Zeroconf'
    )
    return mock_zc.return_value


@pytest.fixture
def adb_pairing() -> AdbPairing:
    return AdbPairing()


def test_init_with_explicit_password() -> None:
    custom_pass = 'my_secret_pass'
    pairing = AdbPairing(password=custom_pass)
    assert pairing.password == custom_pass


def test_initial_properties_state(adb_pairing: AdbPairing) -> None:
    assert adb_pairing.browser is None
    assert adb_pairing.password
    assert adb_pairing.zeroconf_status is False
    assert adb_pairing.qrcode is not None
    assert adb_pairing.qrcode_image is not None


def test_zeroconf_status_alive(
    adb_pairing: AdbPairing,
    mocker: MockerFixture,
    mock_zeroconf_session: MagicMock,
) -> None:
    mocker.patch('device_manager.connection.utils.mdns_session.ServiceBrowser')
    mock_fin = mocker.patch(
        'device_manager.connection.utils.mdns_session.weakref.finalize'
    )
    mock_fin.return_value.alive = True

    adb_pairing.start()
    assert adb_pairing.zeroconf_status is True


def test_update_qrcode_persistence(
    adb_pairing: AdbPairing,
    mocker: MockerFixture,
) -> None:
    mock_qr = mocker.patch('device_manager.connection.adb_pairing.QRCode')
    current_password = adb_pairing.password
    adb_pairing.update_qrcode(new_password=False)
    assert adb_pairing.password == current_password
    assert mock_qr.call_count == 1


def test_update_qrcode_rotation(
    adb_pairing: AdbPairing,
    mocker: MockerFixture,
) -> None:
    mocker.patch('device_manager.connection.adb_pairing.QRCode')
    mocker.patch(
        'device_manager.connection.adb_pairing.create_password',
        return_value='999999',
    )
    old_password = adb_pairing.password
    adb_pairing.update_qrcode(new_password=True)
    assert adb_pairing.password == '999999'
    assert adb_pairing.password != old_password


def test_set_password_behavior(
    adb_pairing: AdbPairing,
    mocker: MockerFixture,
) -> None:
    mock_update = mocker.patch.object(adb_pairing, 'update_qrcode')
    new_pass = '123456'

    adb_pairing.set_password(new_pass, update_qrcode=True)
    assert adb_pairing.password == new_pass
    mock_update.assert_called_with(new_password=False)

    mock_update.reset_mock()
    adb_pairing.set_password('999999', update_qrcode=False)
    mock_update.assert_not_called()


def test_start_engine_configuration(
    adb_pairing: AdbPairing,
    mocker: MockerFixture,
    mock_zeroconf_session: MagicMock,
) -> None:
    mock_browser = mocker.patch(
        'device_manager.connection.utils.mdns_session.ServiceBrowser'
    )
    mock_listener = mocker.patch(
        'device_manager.connection.utils.mdns_session.MDnsListener'
    )
    mocker.patch(
        'device_manager.connection.utils.mdns_session.weakref.finalize'
    )

    adb_pairing.start(unicast=True)
    mock_listener.assert_called_once()
    mock_browser.assert_called_once()
    assert adb_pairing.service_browser_started is True


def test_start_prevents_duplicate_browsers(
    adb_pairing: AdbPairing,
    mocker: MockerFixture,
    mock_zeroconf_session: MagicMock,
) -> None:
    mock_browser = mocker.patch(
        'device_manager.connection.utils.mdns_session.ServiceBrowser'
    )
    mocker.patch(
        'device_manager.connection.utils.mdns_session.weakref.finalize'
    )
    adb_pairing.start()
    adb_pairing.start()
    assert mock_browser.call_count == 1


def test_start_runtime_error_wrapping(
    adb_pairing: AdbPairing,
    mocker: MockerFixture,
    mock_zeroconf_session: MagicMock,
) -> None:
    mocker.patch(
        'device_manager.connection.utils.mdns_session.ServiceBrowser',
        side_effect=RuntimeError,
    )
    with pytest.raises(
        RuntimeError,
        match='Maximum number of Zeroconf instances reached.',
    ):
        adb_pairing.start()


def test_stop_cleans_resources(
    adb_pairing: AdbPairing,
    mocker: MockerFixture,
    mock_zeroconf_session: MagicMock,
) -> None:
    mocker.patch('device_manager.connection.utils.mdns_session.ServiceBrowser')
    mocker.patch(
        'device_manager.connection.utils.mdns_session.weakref.finalize'
    )
    adb_pairing.start()
    adb_pairing.stop_pair_listener()
    mock_zeroconf_session.close.assert_called_once()
    assert adb_pairing.browser is None
    assert adb_pairing.service_browser_started is False


def test_finalize_atexit_cleanup(
    adb_pairing: AdbPairing,
    mocker: MockerFixture,
    mock_zeroconf_session: MagicMock,
) -> None:
    mocker.patch('device_manager.connection.utils.mdns_session.ServiceBrowser')
    mock_fin = mocker.patch(
        'device_manager.connection.utils.mdns_session.weakref.finalize'
    )
    adb_pairing.start()
    callback = mock_fin.call_args[0][1]
    callback()
    assert adb_pairing.browser is None
    assert adb_pairing.service_browser_started is False


def test_uses_injected_mdns_session() -> None:
    mock_session = MagicMock(spec=MdnsBrowserSession)
    mock_session.started = True
    pairing = AdbPairing(session=mock_session)
    pairing.start()
    pairing.stop_pair_listener()
    assert pairing.service_browser_started is True
    mock_session.start.assert_called_once()
    mock_session.stop.assert_called_once()


def test_device_discovery_status(
    adb_pairing: AdbPairing,
    mocker: MockerFixture,
    sample_service: MagicMock,
) -> None:
    mocker.patch.object(
        adb_pairing._context,
        'get_online_service',
        return_value={},
    )
    assert adb_pairing.has_device_to_pairing() is False

    mocker.patch.object(
        adb_pairing._context,
        'get_online_service',
        return_value={'dev': sample_service},
    )
    assert adb_pairing.has_device_to_pairing() is True


def test_pair_devices_adb_success(
    adb_pairing: AdbPairing,
    sample_service: MagicMock,
    mocker: MockerFixture,
) -> None:
    mocker.patch.object(
        adb_pairing._context,
        'get_online_service',
        return_value={'dev': sample_service},
    )
    mock_res = mocker.MagicMock(
        stdout=f'Successfully paired to {sample_service.ip}:{sample_service.port}'
    )
    mocker.patch(
        'device_manager.connection.adb_pairing.subprocess.run',
        return_value=mock_res,
    )
    assert adb_pairing.pair_devices() is True


def test_pair_devices_adb_failure(
    adb_pairing: AdbPairing,
    sample_service: MagicMock,
    mocker: MockerFixture,
) -> None:
    mocker.patch.object(
        adb_pairing._context,
        'get_online_service',
        return_value={'dev': sample_service},
    )
    mock_res = mocker.MagicMock(stdout='Failed: error')
    mocker.patch(
        'device_manager.connection.adb_pairing.subprocess.run',
        return_value=mock_res,
    )
    assert adb_pairing.pair_devices() is False


def test_pair_devices_no_online_services(
    adb_pairing: AdbPairing,
    mocker: MockerFixture,
) -> None:
    mocker.patch.object(
        adb_pairing._context,
        'get_online_service',
        return_value={},
    )
    assert adb_pairing.pair_devices() is False


def test_context_manager_lifecycle(
    adb_pairing: AdbPairing,
    mocker: MockerFixture,
) -> None:
    mock_start = mocker.patch.object(adb_pairing, 'start')
    mock_stop = mocker.patch.object(adb_pairing, 'stop_pair_listener')
    mock_pair = mocker.patch.object(
        adb_pairing,
        'pair_devices',
        return_value=True,
    )

    with adb_pairing.pair() as qr:
        assert qr == adb_pairing.qrcode_string
        mock_start.assert_called_once()

    mock_pair.assert_called_once()
    mock_stop.assert_called_once()


def test_context_manager_retry_limit(
    adb_pairing: AdbPairing,
    mocker: MockerFixture,
) -> None:
    mocker.patch.object(adb_pairing, 'start')
    mocker.patch.object(adb_pairing, 'stop_pair_listener')
    mock_pair = mocker.patch.object(
        adb_pairing,
        'pair_devices',
        return_value=False,
    )

    with adb_pairing.pair(max_attempts=3) as _:
        pass

    assert mock_pair.call_count == 3
